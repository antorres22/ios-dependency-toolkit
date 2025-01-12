# spm_generator/core/generator.py

import os
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom
import uuid
import json
import re

from utils.version_checker import VersionChecker
from diagram.components import (
    add_version_legend,
    add_statistics,
    add_conflicts_section,
    add_dependency_connections
)

class SPMDiagramGenerator:
    def __init__(self, project_root, use_cache=False):
        self.project_root = os.path.abspath(project_root)
        self.spm_modules = []
        self.app_name = os.path.basename(project_root)
        self.setup_logging()
        self.version_checker = VersionChecker(use_cache_only=use_cache)
        self.unique_dependencies = {}

    def setup_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('spm_generator.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def find_spm_modules(self):
        """
        Buscar módulos de Swift Package Manager en el proyecto y agruparlos por directorio
        """
        self.logger.info(f"Buscando en: {self.project_root}")
        self.logger.info("Directorios encontrados:")
        
        ignore_dirs = {'.git', 'build', 'DerivedData', 'Pods', '.build', '.swiftpm'}
        modules_by_directory = {}
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            relative_path = os.path.relpath(root, self.project_root)
            if relative_path != '.':
                self.logger.debug(f"📁 Escaneando: {relative_path}")
            
            if 'Package.swift' in files:
                module_name = os.path.basename(root)
                package_path = os.path.join(root, 'Package.swift')
                
                try:
                    dependencies = self.parse_package_dependencies(package_path)
                    parent_dir = os.path.dirname(relative_path) or "root"
                    
                    if parent_dir not in modules_by_directory:
                        modules_by_directory[parent_dir] = []
                    
                    module_info = {
                        'name': module_name,
                        'path': relative_path,
                        'full_path': root,
                        'dependencies': dependencies,
                        'package_size': os.path.getsize(package_path),
                        'last_modified': datetime.fromtimestamp(os.path.getmtime(package_path)).strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    modules_by_directory[parent_dir].append(module_info)
                    self.logger.info(f"\n✅ Encontrado módulo SPM: {module_name}")
                    
                except Exception as e:
                    self.logger.error(f"Error procesando módulo {module_name}: {str(e)}")
        
        self.spm_modules = []
        for directory, modules in modules_by_directory.items():
            self.spm_modules.append({
                'directory': directory,
                'modules': modules
            })
        
        if not self.spm_modules:
            self.logger.warning("\n⚠️  No se encontraron módulos SPM")
            
        return self.spm_modules

    def parse_package_dependencies(self, package_path):
        """
        Analiza el archivo Package.swift para extraer las dependencias
        """
        dependencies = []
        try:
            with open(package_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                dependency_patterns = {
                    'standard': [
                        r'\.package\(url:\s*"([^"]+)",\s*from:\s*"([^"]+)"\)',
                        r'\.package\(url:\s*"([^"]+)",\s*exact:\s*"([^"]+)"\)',
                        r'\.package\(url:\s*"([^"]+)",\s*branch:\s*"([^"]+)"\)',
                        r'\.package\(url:\s*"([^"]+)",\s*revision:\s*"([^"]+)"\)',
                    ],
                    'range': [
                        r'\.package\(url:\s*"([^"]+)",\s*\.upToNextMajor\(from:\s*"([^"]+)"\)\)',
                        r'\.package\(url:\s*"([^"]+)",\s*\.upToNextMinor\(from:\s*"([^"]+)"\)\)',
                    ],
                    'custom': [
                        r'\.package\(url:\s*"([^"]+)",\s*exact:\s*\.init\(stringLiteral:\s*"([^"]+)"\)\)'
                    ]
                }
                # Procesar dependencias externas
                for pattern_type, patterns in dependency_patterns.items():
                    for pattern in patterns:
                        matches = re.finditer(pattern, content)
                        for match in matches:
                            url = match.group(1)
                            version = match.group(2)
                            package_name = url.split('/')[-1].replace('.git', '')
                            
                            dependency = {
                                'name': package_name,
                                'url': url,
                                'version': version,
                                'type': pattern_type
                            }
                            
                            if 'apple.com' in url.lower():
                                dependency['isAppleDependency'] = True
                            
                            dependencies.append(dependency)
                            
                            # Agregar a dependencias únicas si es externa
                            if not dependency.get('isLocal', False):
                                dep_key = dependency['name']
                                if dep_key not in self.unique_dependencies:
                                    self.unique_dependencies[dep_key] = dependency
                
                # Procesar dependencias locales
                local_patterns = [
                    r'\.package\(path:\s*"([^"]+)"\)',
                    r'\.package\(name:\s*"([^"]+)",\s*path:\s*"([^"]+)"\)',
                ]
                
                for pattern in local_patterns:
                    local_matches = re.finditer(pattern, content)
                    for match in local_matches:
                        if len(match.groups()) == 2:
                            name = match.group(1)
                            path = match.group(2)
                            dependencies.append({
                                'name': name,
                                'path': path,
                                'isLocal': True
                            })
                        else:
                            path = match.group(1)
                            name = os.path.basename(path)
                            dependencies.append({
                                'name': name,
                                'path': path,
                                'isLocal': True
                            })
                
                self.logger.info(f"Analizadas {len(dependencies)} dependencias en {package_path}")
                
        except Exception as e:
            self.logger.error(f"Error al analizar Package.swift: {str(e)}")
        
        return dependencies

    def analyze_dependency_conflicts(self):
        """Analiza conflictos potenciales entre dependencias"""
        dependency_versions = {}
        conflicts = []
        
        for package_group in self.spm_modules:
            for module in package_group['modules']:
                for dep in module['dependencies']:
                    if 'version' in dep and not dep.get('isLocal', False):
                        key = f"{dep['name']}"
                        if key not in dependency_versions:
                            dependency_versions[key] = []
                        dependency_versions[key].append({
                            'version': dep['version'],
                            'module': module['name']
                        })
        
        for package, versions in dependency_versions.items():
            if len(versions) > 1:
                unique_versions = {v['version'] for v in versions}
                if len(unique_versions) > 1:
                    conflicts.append({
                        'package': package,
                        'versions': versions
                    })
        
        return conflicts

    def generate_drawio_diagram(self):
        """
        Generar diagrama Draw.io con módulos SPM agrupados en packages verticalmente
        """
        module_width = 240
        module_height = 180
        module_spacing = 80
        package_spacing = 420  # Aumentado 200%
        package_padding = 40
        
        # Ajustamos el ancho del canvas basado en el número de paquetes
        canvas_width = max(2000, (len(self.spm_modules) * (module_width + package_spacing)))
        canvas_height = 1000  # Altura fija inicial
        
        # Crear elemento raíz con metadatos mejorados
        mxfile = ET.Element('mxfile')
        mxfile.set('host', 'app.diagrams.net')
        mxfile.set('modified', datetime.now().isoformat())
        mxfile.set('agent', 'Python SPM Diagram Generator v2.0')
        mxfile.set('version', '21.6.8')
        mxfile.set('type', 'device')
        
        # Añadir metadatos del proyecto
        metadata = ET.SubElement(mxfile, 'metadata')
        project_info = {
            'projectName': self.app_name,
            'generatedDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'totalModules': sum(len(pkg['modules']) for pkg in self.spm_modules),
            'totalPackages': len(self.spm_modules)
        }
        metadata.text = json.dumps(project_info)
        
        # Configurar el diagrama
        diagram = ET.SubElement(mxfile, 'diagram')
        diagram.set('id', str(uuid.uuid4()))
        diagram.set('name', 'Diagrama de Módulos SPM')
        
        graphModel = ET.SubElement(diagram, 'mxGraphModel')
        graphModel.set('dx', str(canvas_width))
        graphModel.set('dy', str(canvas_height))
        graphModel.set('grid', '1')
        graphModel.set('gridSize', '10')
        graphModel.set('guides', '1')
        graphModel.set('tooltips', '1')
        graphModel.set('connect', '1')
        graphModel.set('arrows', '1')
        graphModel.set('fold', '1')
        graphModel.set('page', '1')
        graphModel.set('pageScale', '1')
        
        root = ET.SubElement(graphModel, 'root')
        
        cell0 = ET.SubElement(root, 'mxCell')
        cell0.set('id', '0')
        
        cell1 = ET.SubElement(root, 'mxCell')
        cell1.set('id', '1')
        cell1.set('parent', '0')
        
        # Añadir nodo de la aplicación
        app_width = 300
        app_height = 60
        app_x = (canvas_width - app_width) / 2
        app_y = 40
        
        app_cell = ET.SubElement(root, 'mxCell')
        app_cell.set('id', 'app')
        app_cell.set('value', self.app_name)
        app_cell.set('style', 'rounded=1;whiteSpace=wrap;html=1;fillColor=#e6d0ff;strokeColor=#9370db;fontSize=14;fontStyle=1')
        app_cell.set('vertex', '1')
        app_cell.set('parent', '1')
        
        app_geo = ET.SubElement(app_cell, 'mxGeometry')
        app_geo.set('x', str(app_x))
        app_geo.set('y', str(app_y))
        app_geo.set('width', str(app_width))
        app_geo.set('height', str(app_height))
        app_geo.set('as', 'geometry')
        
        # Calcular dimensiones para paquetes
        total_packages_width = 0
        package_widths = []
        module_cells = {}
        
        for package_group in self.spm_modules:
            modules = package_group['modules']
            row_width = module_width
            package_width = row_width + (2 * package_padding)
            package_widths.append(package_width)
            total_packages_width += package_width
        
        total_packages_width += (len(self.spm_modules) - 1) * package_spacing
        current_x = (canvas_width - total_packages_width) / 2
        package_y = 160
        
        # Generar paquetes y módulos
        for pkg_idx, package_group in enumerate(self.spm_modules):
            modules = package_group['modules']
            directory = package_group['directory']
            
            rows = len(modules)
            package_width = package_widths[pkg_idx]
            package_height = (rows * module_height) + ((rows - 1) * module_spacing) + (2 * package_padding)
            
            # Crear el contenedor del paquete
            package_cell = ET.SubElement(root, 'mxCell')
            package_cell.set('id', f'package_{pkg_idx}')
            package_cell.set('value', directory)
            package_cell.set('style', 'shape=package;align=center;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;verticalAlign=top')
            package_cell.set('vertex', '1')
            package_cell.set('parent', '1')
            
            package_geo = ET.SubElement(package_cell, 'mxGeometry')
            package_geo.set('x', str(current_x))
            package_geo.set('y', str(package_y))
            package_geo.set('width', str(package_width))
            package_geo.set('height', str(package_height))
            package_geo.set('as', 'geometry')
            
            # Generar cada módulo dentro del paquete
            for i, module in enumerate(modules):
                module_cells[module['name']] = f'module_{pkg_idx}_{i}'
                
                x_pos = current_x + package_padding
                y_pos = package_y + package_padding + (i * (module_height + module_spacing))
                
                # Crear el módulo
                module_cell = ET.SubElement(root, 'mxCell')
                module_cell.set('id', f'module_{pkg_idx}_{i}')
                module_cell.set('vertex', '1')
                module_cell.set('parent', '1')
                
                # Estilo del módulo
                style = 'shape=module;align=left;spacingLeft=20;align=center;verticalAlign=top;'
                style += 'whiteSpace=wrap;html=1;jettyWidth=20;jettyHeight=10;'
                
                if any('isAppleDependency' in dep for dep in module['dependencies']):
                    style += 'fillColor=#e8f4ff;strokeColor=#4a90e2;'
                else:
                    style += 'fillColor=#e0f8ff;strokeColor=#87cefa;'
                
                module_cell.set('style', style)
                
                # Geometría del módulo
                module_geo = ET.SubElement(module_cell, 'mxGeometry')
                module_geo.set('x', str(x_pos))
                module_geo.set('y', str(y_pos))
                module_geo.set('width', str(module_width))
                module_geo.set('height', str(module_height))
                module_geo.set('as', 'geometry')
                
                # Contenido HTML del módulo
                dependencies_html = ""
                if module['dependencies']:
                    dependencies_html = "<hr size='1'/><p style='margin:0px;margin-left:4px;'><u>Dependencies:</u></p>"
                    for dep in module['dependencies']:
                        if 'isLocal' in dep:
                            dependencies_html += f"<p style='margin:0px;margin-left:8px;font-size:10px'>• {dep['name']} (local)</p>"
                        else:
                            version_info = dep.get('version', 'N/A')
                            dependencies_html += f"<p style='margin:0px;margin-left:8px;font-size:10px'>• {dep['name']} ({version_info})</p>"
                
                module_cell.set('value', 
                    f'<p style="margin:0px;margin-top:4px;text-align:center;"><b>{module["name"]}</b></p>' +
                    dependencies_html)
            
            # Conectar App con el paquete
            edge = ET.SubElement(root, 'mxCell')
            edge.set('id', f'edge_{pkg_idx}')
            edge.set('edge', '1')
            edge.set('parent', '1')
            edge.set('source', 'app')
            edge.set('target', f'package_{pkg_idx}')
            edge.set('style', 'endArrow=block;dashed=1;endFill=0;endSize=12;html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;')
            
            edge_geo = ET.SubElement(edge, 'mxGeometry')
            edge_geo.set('relative', '1')
            edge_geo.set('as', 'geometry')
            
            current_x += package_width + package_spacing
        
        # Añadir conexiones de dependencias
        add_dependency_connections(root, module_cells, self.spm_modules)
        
        # Calcular posición x para leyenda y estadísticas
        legend_x = current_x + 40
        
        # Añadir leyenda y estadísticas
        add_version_legend(root, package_y + package_height + package_spacing, legend_x)
        add_statistics(root, package_y + package_height + package_spacing + 100, legend_x, 
                      self.spm_modules, self.unique_dependencies, self.version_checker)
        
        # Analizar y mostrar conflictos
        conflicts = self.analyze_dependency_conflicts()
        if conflicts:
          add_conflicts_section(root, package_y + package_height + package_spacing + 200, legend_x, conflicts)
        
        # Crear directorio results si no existe
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            self.logger.info(f"📁 Directorio '{results_dir}' creado")
      
        # Generar archivo
        tree = ET.ElementTree(mxfile)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(results_dir, f'diagrama_modulos_spm_{timestamp}.xml')
        
        xml_str = ET.tostring(mxfile, encoding='unicode')
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        self.logger.info(f"Diagrama generado exitosamente: {output_file}")
        return output_file