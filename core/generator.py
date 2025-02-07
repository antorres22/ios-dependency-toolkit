import os
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from xml.dom import minidom
import uuid
import json
import re
from collections import defaultdict
from .pod_analyzer import PodfileAnalyzer

from utils.version_checker import VersionChecker
from diagram.components import (
    add_version_legend,
    add_statistics,
    add_conflicts_section,
    add_spm_dependencies_section,
    add_pods_dependencies_section
)

class SPMDiagramGenerator:
    def __init__(self, project_root, use_cache=False):
        self.project_root = os.path.abspath(project_root)
        self.spm_modules = []
        self.app_name = os.path.basename(project_root)
        self.logger = self.setup_logging()
        self.version_checker = VersionChecker(use_cache_only=not use_cache)
        self.unique_dependencies = {}
        self.layers = defaultdict(list)
        
        # Añadir el analizador de Pods
        self.pod_analyzer = PodfileAnalyzer(project_root)
        self.pod_dependencies = []

    def setup_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def analyze_dependencies(self):
        """Analiza tanto las dependencias SPM como las de Cocoapods"""
        self.logger.info("\n🔍 Analizando dependencias...")
        
        # Analizar SPM
        self.logger.info("📦 Analizando módulos SPM")
        self.find_spm_modules()
        
        # Analizar Pods
        self.logger.info("📦 Analizando Pods")
        podfile_path = self.pod_analyzer.find_podfile()
        if podfile_path:
            self.pod_dependencies = self.pod_analyzer.parse_podfile(podfile_path)
            self.logger.info(f"✅ Encontradas {len(self.pod_dependencies)} dependencias en Pods")
        else:
            self.logger.info("ℹ️ No se encontraron dependencias de Pods")

    def generate_dependencies_json(self):
        """Genera un JSON con la información de todas las dependencias"""
        self.analyze_dependencies()
        dependencies_info = {}
        
        # Procesar dependencias SPM
        for dependency in self.unique_dependencies.values():
            latest_version = self.version_checker.get_latest_version(dependency['url'])
            status = self.version_checker._get_version_status(dependency['version'], latest_version, dependency['url'])
            
            dependencies_info[dependency['name']] = {
                'url': dependency['url'],
                'version_used': dependency['version'],
                'latest_version': latest_version,
                'timestamp': datetime.now().isoformat(),
                'status': status,
                'type': 'spm'
            }
        
        # Procesar dependencias Pods
        if self.pod_dependencies:
            for pod in self.pod_dependencies:
                if pod['name'] not in dependencies_info:  # Evitar duplicados
                    latest_version = pod.get('latest_version', 'N/A')
                    status = "⚫"
                    if pod.get('version', 'N/A') != 'N/A' and latest_version != 'N/A':
                        try:
                            if pod['version'] == latest_version:
                                status = "🟢"
                            elif pod['version'] < latest_version:
                                status = "🔴"
                            else:
                                status = "🟡"
                        except:
                            status = "⚫"
                    
                    dependencies_info[pod['name']] = {
                        'url': pod.get('url', 'N/A'),
                        'version_used': pod.get('version', 'N/A'),
                        'latest_version': latest_version,
                        'timestamp': datetime.now().isoformat(),
                        'status': status,
                        'type': 'pod'
                    }
        
        # Guardar el JSON
        output_file = os.path.join('results', 'dependencies_info.json')
        os.makedirs('results', exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(dependencies_info, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"\n📝 Información de dependencias guardada en: {output_file}")
        return output_file

    def find_spm_modules(self):
        """Buscar módulos de Swift Package Manager en el proyecto"""
        self.logger.info(f"Buscando en: {self.project_root}")
        
        ignore_dirs = {'.git', 'build', 'DerivedData', 'Pods', '.build', '.swiftpm'}
        modules_by_directory = {}
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            if 'Package.swift' in files:
                module_name = os.path.basename(root)
                package_path = os.path.join(root, 'Package.swift')
                relative_path = os.path.relpath(root, self.project_root)
                
                try:
                    dependencies = self.parse_package_dependencies(package_path)
                    parent_dir = os.path.dirname(relative_path) or "root"
                    
                    if parent_dir not in modules_by_directory:
                        modules_by_directory[parent_dir] = []
                    
                    module_info = {
                        'name': module_name,
                        'path': relative_path,
                        'dependencies': dependencies
                    }
                    
                    modules_by_directory[parent_dir].append(module_info)
                    self.logger.info(f"\n✅ Encontrado módulo SPM: {module_name}")
                    
                except Exception as e:
                    self.logger.error(f"Error procesando módulo {module_name}: {str(e)}")
        
        self.spm_modules = [
            {'directory': dir, 'modules': modules}
            for dir, modules in modules_by_directory.items()
        ]

        # Logging de módulos encontrados
        self.logger.info(f"Módulos encontrados por directorio:")
        for dir, modules in modules_by_directory.items():
            self.logger.info(f"  {dir}: {[m['name'] for m in modules]}")
        
        return self.spm_modules
    
    def parse_package_dependencies(self, package_path):
        """Analiza el archivo Package.swift para extraer dependencias"""
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
        """Generar diagrama Draw.io con módulos SPM y Pods agrupados"""
        # Analizar todas las dependencias
        self.analyze_dependencies()

        # Calcular dimensiones necesarias
        dimensions = self._calculate_dimensions()
        
        # Crear estructura base del XML
        mxfile, root = self._create_base_structure(dimensions)
        
        # Crear layers
        self._create_layers(root)
        
        # Agregar nodo de la aplicación
        self._add_app_node(root, dimensions)
        
        # Agregar encabezados de secciones
        self._add_section_headers(root, dimensions)
        
        # Calcular posición inicial para centrado
        current_x = (dimensions['canvas_width'] - dimensions['total_width']) / 2
        
        # Generar sección SPM
        module_cells = self._generate_packages_and_modules(root, dimensions, current_x)
        
        # Agregar conexiones entre módulos SPM
        self._add_dependencies_connections(root, module_cells)
        
        # Generar sección Pods si existe
        if self.pod_dependencies:
            pod_section_x = (dimensions['canvas_width'] - (3 * (dimensions['module_width'] + dimensions['module_spacing']))) / 2
            self._generate_pods_section(root, dimensions, pod_section_x)
        
        # Agregar estadísticas y leyenda
        stats_x = current_x + dimensions['total_width'] + 40
        self._add_statistics_and_legend(root, dimensions, stats_x)
        
        # Generar y guardar el archivo
        return self._save_diagram(mxfile)

    def _calculate_dimensions(self):
        """Calcula las dimensiones necesarias para el diagrama"""
        dimensions = {
            'module_width': 240,
            'module_height': 180,
            'module_spacing': 80,
            'package_spacing': 420,
            'package_padding': 40,
            'section_spacing': 200,  # Espacio entre sección SPM y Pods
            'package_y': 120,  # Añadimos la posición Y inicial para los paquetes
        }
        
        # Calcular anchos de paquetes SPM
        package_widths = []
        for package_group in self.spm_modules:
            package_width = dimensions['module_width'] + (2 * dimensions['package_padding'])
            package_widths.append(package_width)
        dimensions['package_widths'] = package_widths
        
        # Calcular dimensiones para SPM
        max_spm_modules_per_package = max(len(pkg['modules']) for pkg in self.spm_modules) if self.spm_modules else 0
        spm_height = dimensions['package_padding'] + (max_spm_modules_per_package * (dimensions['module_height'] + dimensions['module_spacing']))
        
        # Calcular dimensiones para Pods
        pods_height = 0
        if self.pod_dependencies:
            pods_per_row = 3  # Número de pods por fila
            num_pod_rows = (len(self.pod_dependencies) + pods_per_row - 1) // pods_per_row
            pods_height = (num_pod_rows * (dimensions['module_height'] + dimensions['module_spacing']))
        
        # Altura total necesaria
        total_height = spm_height + (pods_height if pods_height > 0 else 0) + dimensions['section_spacing']
        dimensions['canvas_height'] = max(2000, total_height + 500)
        
        # Calcular ancho total y agregarlo a dimensions
        total_width = self._calculate_total_width(dimensions)
        dimensions['total_width'] = total_width
        dimensions['canvas_width'] = max(3000, total_width + 800)  # Agregar espacio para estadísticas
        
        # Posiciones iniciales
        dimensions.update({
            'spm_start_y': 120,
            'pods_start_y': spm_height + dimensions['section_spacing'] + 120 if pods_height > 0 else 0,
        })
        
        return dimensions

    def _calculate_total_width(self, dimensions):
        """Calcula el ancho total necesario para el diagrama"""
        # Ancho para sección SPM
        total_package_width = 0
        for package_group in self.spm_modules:
            package_width = dimensions['module_width'] + (2 * dimensions['package_padding'])
            total_package_width += package_width
        
        spm_width = total_package_width + ((len(self.spm_modules) - 1) * dimensions['package_spacing'])
        
        # Ancho para sección Pods
        pods_width = 0
        if self.pod_dependencies:
            pods_per_row = 3
            num_pods = len(self.pod_dependencies)
            num_columns = min(pods_per_row, num_pods)
            pods_width = (num_columns * dimensions['module_width']) + ((num_columns - 1) * dimensions['module_spacing'])
        
        # Retornar el máximo entre el ancho de SPM y Pods
        return max(spm_width, pods_width)

    def _create_base_structure(self, dimensions):
        """Crea la estructura base del XML para el diagrama"""
        mxfile = ET.Element('mxfile')
        mxfile.set('host', 'app.diagrams.net')
        mxfile.set('modified', datetime.now().isoformat())
        mxfile.set('agent', 'Python SPM Diagram Generator v2.0')
        mxfile.set('version', '21.6.8')
        mxfile.set('type', 'device')
        
        # Añadir metadatos
        metadata = ET.SubElement(mxfile, 'metadata')
        project_info = {
            'projectName': self.app_name,
            'generatedDate': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'totalModules': sum(len(pkg['modules']) for pkg in self.spm_modules),
            'totalPackages': len(self.spm_modules)
        }
        metadata.text = json.dumps(project_info)

        # Crear estructura del diagrama
        diagram = ET.SubElement(mxfile, 'diagram')
        diagram.set('id', str(uuid.uuid4()))
        diagram.set('name', 'Diagrama de Módulos SPM')
        
        graphModel = ET.SubElement(diagram, 'mxGraphModel')
        graphModel.set('dx', str(dimensions['canvas_width']))
        graphModel.set('dy', str(dimensions['canvas_height']))
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
        
        # Células base
        cell0 = ET.SubElement(root, 'mxCell')
        cell0.set('id', '0')
        
        cell1 = ET.SubElement(root, 'mxCell')
        cell1.set('id', '1')
        cell1.set('parent', '0')
        
        return mxfile, root

    def _create_layers(self, root):
        """Crea los layers del diagrama"""
        # Layer Base (siempre visible)
        base_layer = ET.SubElement(root, 'mxCell')
        base_layer.set('id', 'base_layer')
        base_layer.set('value', 'Base')
        base_layer.set('style', 'defaultLayer;')
        base_layer.set('parent', '0')
        
        # Crear layer para cada módulo
        for package_group in self.spm_modules:
            for module in package_group['modules']:
                module_layer = ET.SubElement(root, 'mxCell')
                layer_id = f"layer_{module['name'].replace(' ', '_')}"
                module_layer.set('id', layer_id)
                module_layer.set('value', f"Conexiones {module['name']}")
                module_layer.set('style', 'defaultLayer;labelBackgroundColor=#ffffff;')
                module_layer.set('parent', '0')
                self.layers[module['name']] = layer_id

    def _add_app_node(self, root, dimensions):
        """Agrega el nodo de la aplicación al diagrama"""
        app_width = 300
        app_height = 60
        app_x = (dimensions['canvas_width'] - app_width) / 2
        app_y = 40
        
        app_cell = ET.SubElement(root, 'mxCell')
        app_cell.set('id', 'app')
        app_cell.set('value', self.app_name)
        app_cell.set('style', 'rounded=1;whiteSpace=wrap;html=1;fillColor=#e6d0ff;strokeColor=#9370db;fontSize=14;fontStyle=1')
        app_cell.set('vertex', '1')
        app_cell.set('parent', 'base_layer')
        
        app_geo = ET.SubElement(app_cell, 'mxGeometry')
        app_geo.set('x', str(app_x))
        app_geo.set('y', str(app_y))
        app_geo.set('width', str(app_width))
        app_geo.set('height', str(app_height))
        app_geo.set('as', 'geometry')
    
    def _generate_packages_and_modules(self, root, dimensions, current_x):
        """Genera los paquetes y módulos del diagrama"""
        module_cells = {}
        
        for pkg_idx, package_group in enumerate(self.spm_modules):
            modules = package_group['modules']
            directory = package_group['directory']
            
            # Calcular altura real necesaria para el paquete
            package_height = (len(modules) * (dimensions['module_height'] + dimensions['module_spacing'])) - dimensions['module_spacing'] + (2 * dimensions['package_padding'])
            package_width = dimensions['package_widths'][pkg_idx]
            
            # Crear el contenedor del paquete
            package_cell = self._create_package(root, pkg_idx, directory, current_x, dimensions['package_y'], 
                                            package_width, package_height)
            
            # Crear conexión con la app
            self._create_app_connection(root, pkg_idx, package_cell)
            
            # Crear módulos
            for i, module in enumerate(modules):
                x_pos = current_x + dimensions['package_padding']
                y_pos = dimensions['package_y'] + dimensions['package_padding'] + (i * (dimensions['module_height'] + dimensions['module_spacing']))
                
                module_cells[module['name']] = self._create_module(root, pkg_idx, i, module, x_pos, y_pos, 
                                                                dimensions['module_width'], dimensions['module_height'])
            
            current_x += package_width + dimensions['package_spacing']
        
        return module_cells

    def _create_package(self, root, pkg_idx, directory, x, y, width, height):
        """Crea un paquete individual"""
        package_cell = ET.SubElement(root, 'mxCell')
        package_cell.set('id', f'package_{pkg_idx}')
        package_cell.set('value', directory)
        package_cell.set('style', 'shape=package;align=center;html=1;fillColor=#f5f5f5;strokeColor=#666666;fontStyle=1;verticalAlign=top;spacing=10;')
        package_cell.set('vertex', '1')
        package_cell.set('parent', 'base_layer')
        
        package_geo = ET.SubElement(package_cell, 'mxGeometry')
        package_geo.set('x', str(x))
        package_geo.set('y', str(y))
        package_geo.set('width', str(width))
        package_geo.set('height', str(height))
        package_geo.set('as', 'geometry')
        
        return package_cell
    
    def _create_app_connection(self, root, pkg_idx, package_cell):
        """Crea la conexión entre la app y un paquete"""
        edge = ET.SubElement(root, 'mxCell')
        edge.set('id', f'edge_{pkg_idx}')
        edge.set('edge', '1')
        edge.set('parent', 'base_layer')
        edge.set('source', 'app')
        edge.set('target', f'package_{pkg_idx}')
        edge.set('style', 'endArrow=block;dashed=1;endFill=0;endSize=12;html=1;rounded=0;edgeStyle=orthogonalEdgeStyle;')
        
        edge_geo = ET.SubElement(edge, 'mxGeometry')
        edge_geo.set('relative', '1')
        edge_geo.set('as', 'geometry')

    def _create_module(self, root, pkg_idx, module_idx, module, x, y, width, height):
        """Crea un módulo individual"""
        module_cell = ET.SubElement(root, 'mxCell')
        module_id = f'module_{pkg_idx}_{module_idx}'
        module_cell.set('id', module_id)
        module_cell.set('vertex', '1')
        module_cell.set('parent', 'base_layer')
        
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
        module_geo.set('x', str(x))
        module_geo.set('y', str(y))
        module_geo.set('width', str(width))
        module_geo.set('height', str(height))
        module_geo.set('as', 'geometry')
        
        # Contenido del módulo
        module_cell.set('value', self._create_module_content(module))
        
        return module_id
    
    def _create_module_content(self, module):
        """Crea el contenido HTML del módulo"""
        dependencies_html = ""
        if module['dependencies']:
            dependencies_html = "<hr size='1'/><p style='margin:2px;margin-left:4px;'><u>Dependencies:</u></p>"
            for dep in module['dependencies']:
                if 'isLocal' in dep:
                    dependencies_html += f"<p style='margin:2px;margin-left:8px;font-size:10px'>• {dep['name']} (local)</p>"
                else:
                    version_info = dep.get('version', 'N/A')
                    dependencies_html += f"<p style='margin:2px;margin-left:8px;font-size:10px'>• {dep['name']} ({version_info})</p>"
        
        return f'<p style="margin:4px;margin-top:6px;text-align:center;font-weight:bold;">{module["name"]}</p>' + dependencies_html

    def _add_dependencies_connections(self, root, module_cells):
        """Agrega las conexiones entre módulos basadas en sus dependencias"""
        for pkg_idx, package_group in enumerate(self.spm_modules):
            for i, module in enumerate(package_group['modules']):
                source_id = f'module_{pkg_idx}_{i}'
                layer_id = self.layers[module['name']]
                
                for dep in module['dependencies']:
                    if dep.get('isLocal', False) and dep['name'] in module_cells:
                        target_id = module_cells[dep['name']]
                        self._create_dependency_connection(root, source_id, target_id, layer_id)

    def _create_dependency_connection(self, root, source_id, target_id, layer_id):
        """Crea una conexión de dependencia entre dos módulos"""
        edge = ET.SubElement(root, 'mxCell')
        edge.set('id', f'dep_edge_{source_id}_{target_id}')
        edge.set('edge', '1')
        edge.set('parent', layer_id)
        edge.set('source', source_id)
        edge.set('target', target_id)
        edge.set('style', 'edgeStyle=orthogonalEdgeStyle;html=1;exitX=0;exitY=0.5;' +
                'entryX=1;entryY=0.5;curved=1;rounded=0;dashed=1;' +
                'endArrow=open;endFill=0;strokeWidth=1.5;strokeColor=#0066CC;')
        
        edge_geo = ET.SubElement(edge, 'mxGeometry')
        edge_geo.set('relative', '1')
        edge_geo.set('as', 'geometry')
        
        points = ET.SubElement(edge_geo, 'Array')
        points.set('as', 'points')
        
        label = ET.SubElement(edge_geo, 'mxPoint')
        label.set('x', '0.5')
        label.set('y', '0')
        label.set('as', 'offset')

    def _add_statistics_and_legend(self, root, dimensions, x_position):
        """Agrega estadísticas y leyenda con las dependencias en columnas"""
        width = 380
        base_y = dimensions['package_y']
        
        # Leyenda de versiones primero (arriba)
        add_version_legend(root, base_y, x_position + width/2, 'base_layer')
        legend_height = 150  # altura aproximada de la leyenda
        
        # Ajustar posición Y inicial para los contenedores
        containers_y = base_y + legend_height + 20
        
        # Contenedor SPM
        spm_container = ET.SubElement(root, 'mxCell')
        spm_id = f'statistics_spm_{uuid.uuid4().hex[:8]}'
        spm_container.set('id', spm_id)
        spm_container.set('value', 'Dependencias SPM Externas')
        spm_container.set('style', 'swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=30;fillColor=#f5f5f5;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;strokeColor=#666666;fontSize=12;')
        spm_container.set('vertex', '1')
        spm_container.set('parent', 'base_layer')
        
        spm_geo = ET.SubElement(spm_container, 'mxGeometry')
        spm_geo.set('x', str(x_position))
        spm_geo.set('y', str(containers_y))
        spm_geo.set('width', str(width))
        spm_geo.set('height', '2000')
        spm_geo.set('as', 'geometry')
        
        # SPM Dependencies
        y_offset = 30  # Empezar después del título
        if self.unique_dependencies:
            y_offset = add_spm_dependencies_section(root, spm_id, y_offset, self.unique_dependencies, self.version_checker)
            spm_container.set('height', str(y_offset + 30))  # Ajustar altura del contenedor SPM
        
        # Contenedor Pods
        if self.pod_dependencies:
            pods_container = ET.SubElement(root, 'mxCell')
            pods_id = f'statistics_pods_{uuid.uuid4().hex[:8]}'
            pods_container.set('id', pods_id)
            pods_container.set('value', 'Dependencias CocoaPods')
            pods_container.set('style', 'swimlane;fontStyle=1;childLayout=stackLayout;horizontal=1;startSize=30;fillColor=#f5f5f5;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;strokeColor=#666666;fontSize=12;')
            pods_container.set('vertex', '1')
            pods_container.set('parent', 'base_layer')
            
            # Calcular altura real necesaria para pods
            num_pods = len(self.pod_dependencies)
            pod_cell_height = 90  # Altura de cada celda de pod
            separator_height = 8  # Altura de cada separador
            title_height = 30    # Altura del título
            padding = 40        # Padding adicional
            
            # Altura total = título + (altura_celda * num_pods) + (altura_separador * (num_pods-1)) + padding
            pod_height = title_height + (pod_cell_height * num_pods) + (separator_height * (num_pods - 1)) + padding
            
            pods_geo = ET.SubElement(pods_container, 'mxGeometry')
            pods_geo.set('x', str(x_position + width + 40))
            pods_geo.set('y', str(containers_y))
            pods_geo.set('width', str(width))
            pods_geo.set('height', str(pod_height))
            pods_geo.set('as', 'geometry')
            
            pods_y_offset = add_pods_dependencies_section(root, pods_id, 30, self.pod_dependencies, self.version_checker)

    def _save_diagram(self, mxfile):
        """Guarda el diagrama en un archivo XML"""
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)
            self.logger.info(f"📁 Directorio '{results_dir}' creado")
        
        tree = ET.ElementTree(mxfile)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = os.path.join(results_dir, f'diagrama_modulos_spm_{timestamp}.xml')
        
        xml_str = ET.tostring(mxfile, encoding='unicode')
        xml_str = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_str
        pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(pretty_xml)
        
        self.logger.info(f"Diagrama generado exitosamente: {output_file}")
        return output_file
    def _add_section_headers(self, root, dimensions):
        """Agrega los encabezados de las secciones SPM y Pods"""
        # Encabezado SPM
        spm_header = ET.SubElement(root, 'mxCell')
        spm_header.set('id', 'spm_header')
        spm_header.set('value', 'Swift Package Manager Dependencies')
        spm_header.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=16;fontStyle=1')
        spm_header.set('vertex', '1')
        spm_header.set('parent', 'base_layer')
        
        header_geo = ET.SubElement(spm_header, 'mxGeometry')
        header_geo.set('x', str((dimensions['canvas_width'] - 300) / 2))
        header_geo.set('y', str(dimensions['spm_start_y'] - 50))
        header_geo.set('width', '300')
        header_geo.set('height', '30')
        header_geo.set('as', 'geometry')
        
        if self.pod_dependencies:
            # Encabezado Pods
            pods_header = ET.SubElement(root, 'mxCell')
            pods_header.set('id', 'pods_header')
            pods_header.set('value', 'CocoaPods Dependencies')
            pods_header.set('style', 'text;html=1;strokeColor=none;fillColor=none;align=center;verticalAlign=middle;whiteSpace=wrap;rounded=0;fontSize=16;fontStyle=1')
            pods_header.set('vertex', '1')
            pods_header.set('parent', 'base_layer')
            
            pods_header_geo = ET.SubElement(pods_header, 'mxGeometry')
            pods_header_geo.set('x', str((dimensions['canvas_width'] - 300) / 2))
            pods_header_geo.set('y', str(dimensions['pods_start_y'] - 50))
            pods_header_geo.set('width', '300')
            pods_header_geo.set('height', '30')
            pods_header_geo.set('as', 'geometry')

    def _generate_pods_section(self, root, dimensions, current_x):
        """Genera la sección de dependencias de Cocoapods"""
        if not self.pod_dependencies:
            return
        
        pods_per_row = 3
        module_width = dimensions['module_width']
        module_height = dimensions['module_height']
        module_spacing = dimensions['module_spacing']
        
        for i, pod in enumerate(self.pod_dependencies):
            row = i // pods_per_row
            col = i % pods_per_row
            
            x_pos = current_x + (col * (module_width + module_spacing))
            y_pos = dimensions['pods_start_y'] + (row * (module_height + module_spacing))
            
            # Crear el módulo para el pod
            pod_cell = ET.SubElement(root, 'mxCell')
            pod_cell.set('id', f'pod_{i}')
            pod_cell.set('vertex', '1')
            pod_cell.set('parent', 'base_layer')
            
            # Estilo especial para pods
            style = 'shape=module;align=left;spacingLeft=20;align=center;verticalAlign=top;'
            style += 'whiteSpace=wrap;html=1;jettyWidth=20;jettyHeight=10;'
            style += 'fillColor=#fff2cc;strokeColor=#d6b656;'  # Color distintivo para pods
            
            pod_cell.set('style', style)
            
            # Contenido del pod
            pod_content = f'<p style="margin:4px;margin-top:6px;text-align:center;font-weight:bold;">{pod["name"]}</p>'
            if 'version' in pod:
                pod_content += f'<hr size="1"/><p style="margin:2px;margin-left:8px;font-size:10px">Version: {pod["version"]}</p>'
            if 'url' in pod:
                pod_content += f'<p style="margin:2px;margin-left:8px;font-size:10px">Git: {pod["url"]}</p>'
                
            pod_cell.set('value', pod_content)
            
            # Geometría del pod
            pod_geo = ET.SubElement(pod_cell, 'mxGeometry')
            pod_geo.set('x', str(x_pos))
            pod_geo.set('y', str(y_pos))
            pod_geo.set('width', str(module_width))
            pod_geo.set('height', str(module_height))
            pod_geo.set('as', 'geometry')