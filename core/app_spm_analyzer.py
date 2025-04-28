# app_spm_analyzer.py

import os
import json
import re
import logging
import plistlib
from typing import Dict, List, Optional, Tuple

class AppSPMDependencyAnalyzer:
    """
    Analizador de dependencias SPM integradas directamente en la aplicación iOS.
    Busca dependencias SPM definidas en el archivo Package.resolved o en archivos
    de proyecto Xcode.
    """
    
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        self.logger = self._setup_logging()
        self.direct_dependencies = []
        
    def _setup_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def find_app_spm_dependencies(self) -> List[Dict]:
      """
      Busca dependencias SPM directamente integradas en la aplicación iOS.
      Retorna una lista de diccionarios con información de cada dependencia.
      """
      self.logger.info(f"\n🔍 Buscando dependencias SPM integradas directamente en la aplicación: {self.project_root}")
      
      # Lista para almacenar todas las dependencias encontradas
      all_dependencies = []
      
      # Determinar el archivo de proyecto principal
      main_xcodeproj = self._find_main_xcodeproj()
      if main_xcodeproj:
          self.logger.info(f"✅ Detectado proyecto principal: {main_xcodeproj}")
          main_pbxproj = os.path.join(main_xcodeproj, "project.pbxproj")
          
          if os.path.exists(main_pbxproj):
              self.logger.info(f"🔍 Analizando archivo project.pbxproj principal: {main_pbxproj}")
              dependencies = self._parse_pbxproj_for_spm(main_pbxproj)
              all_dependencies.extend(dependencies)
      
      # También buscar Package.resolved en el proyecto principal
      package_resolved_paths = []
      
      # En la raíz del proyecto
      root_package_resolved = os.path.join(self.project_root, "Package.resolved")
      if os.path.exists(root_package_resolved):
          package_resolved_paths.append(root_package_resolved)
      
      # En .swiftpm
      swiftpm_package_resolved = os.path.join(self.project_root, ".swiftpm", "Package.resolved")
      if os.path.exists(swiftpm_package_resolved):
          package_resolved_paths.append(swiftpm_package_resolved)
      
      # En el proyecto principal
      if main_xcodeproj:
          main_package_resolved = os.path.join(main_xcodeproj, "project.xcworkspace", "xcshareddata", "swiftpm", "Package.resolved")
          if os.path.exists(main_package_resolved):
              package_resolved_paths.append(main_package_resolved)
      
      # Procesar los Package.resolved encontrados
      for path in package_resolved_paths:
          self.logger.info(f"✅ Analizando Package.resolved: {path}")
          dependencies = self._parse_package_resolved(path)
          all_dependencies.extend(dependencies)
      
      # Eliminar duplicados (basado en URL)
      unique_dependencies = {}
      for dep in all_dependencies:
          if dep['url'] not in unique_dependencies:
              unique_dependencies[dep['url']] = dep
      
      self.direct_dependencies = list(unique_dependencies.values())
      self.logger.info(f"📊 Total de dependencias SPM directas encontradas: {len(self.direct_dependencies)}")
      
      return self.direct_dependencies
    
    def _find_package_resolved_files(self) -> List[str]:
        """
        Busca archivos Package.resolved en el proyecto.
        Pueden estar en:
        - La raíz del proyecto
        - Dentro de .xcodeproj
        - Dentro de .swiftpm
        """
        package_resolved_paths = []
        
        # Buscar en la raíz del proyecto
        root_package_resolved = os.path.join(self.project_root, "Package.resolved")
        if os.path.exists(root_package_resolved):
            package_resolved_paths.append(root_package_resolved)
        
        # Buscar dentro de .swiftpm
        swiftpm_package_resolved = os.path.join(self.project_root, ".swiftpm", "Package.resolved")
        if os.path.exists(swiftpm_package_resolved):
            package_resolved_paths.append(swiftpm_package_resolved)
        
        # Buscar dentro de .xcodeproj
        for root, dirs, files in os.walk(self.project_root):
            for dir_name in dirs:
                if dir_name.endswith('.xcodeproj'):
                    xcodeproj_package_resolved = os.path.join(root, dir_name, "project.xcworkspace", "xcshareddata", "swiftpm", "Package.resolved")
                    if os.path.exists(xcodeproj_package_resolved):
                        package_resolved_paths.append(xcodeproj_package_resolved)
        
        return package_resolved_paths
    
    def _find_xcodeproj_files(self) -> List[str]:
        """Busca archivos .xcodeproj en el proyecto"""
        xcodeproj_paths = []
        
        for root, dirs, files in os.walk(self.project_root):
            for dir_name in dirs:
                if dir_name.endswith('.xcodeproj'):
                    xcodeproj_paths.append(os.path.join(root, dir_name))
        
        return xcodeproj_paths
    
    def _find_pbxproj_files(self) -> List[str]:
        """Busca archivos project.pbxproj dentro de .xcodeproj"""
        pbxproj_paths = []
        
        for root, dirs, files in os.walk(self.project_root):
            for dir_name in dirs:
                if dir_name.endswith('.xcodeproj'):
                    pbxproj_path = os.path.join(root, dir_name, "project.pbxproj")
                    if os.path.exists(pbxproj_path):
                        pbxproj_paths.append(pbxproj_path)
        
        return pbxproj_paths
    
    def _parse_package_resolved(self, file_path: str) -> List[Dict]:
        """
        Parsea un archivo Package.resolved para extraer dependencias SPM.
        Soporta tanto formato v1 como v2 de Package.resolved.
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            
            # Formato v2: {"pins": [{...}]}
            if "pins" in content:
                self.logger.info("📦 Detectado formato v2 de Package.resolved")
                for pin in content["pins"]:
                    dependency = {
                        'name': pin.get("identity", "Unknown"),
                        'url': pin.get("location", "N/A"),
                        'version': pin.get("state", {}).get("version", "N/A"),
                        'type': 'spm_app_direct',
                        'source': 'Package.resolved'
                    }
                    dependencies.append(dependency)
            
            # Formato v1: {"object": {"pins": [{...}]}}
            elif "object" in content and "pins" in content["object"]:
                self.logger.info("📦 Detectado formato v1 de Package.resolved")
                for pin in content["object"]["pins"]:
                    # Extraer versión
                    version = "N/A"
                    if "state" in pin:
                        if "version" in pin["state"]:
                            version = pin["state"]["version"]
                        elif "branch" in pin["state"]:
                            version = f"branch: {pin['state']['branch']}"
                        elif "revision" in pin["state"]:
                            version = f"revision: {pin['state']['revision'][:8]}"
                    
                    dependency = {
                        'name': pin.get("package", "Unknown"),
                        'url': pin.get("repositoryURL", "N/A"),
                        'version': version,
                        'type': 'spm_app_direct',
                        'source': 'Package.resolved'
                    }
                    dependencies.append(dependency)
        
        except Exception as e:
            self.logger.error(f"❌ Error parseando {file_path}: {str(e)}")
        
        self.logger.info(f"📑 Encontradas {len(dependencies)} dependencias en {file_path}")
        return dependencies
    
    def _parse_xcodeproj_for_spm(self, xcodeproj_path: str) -> List[Dict]:
        """
        Analiza un archivo .xcodeproj para encontrar referencias a dependencias SPM.
        """
        # Este es un enfoque básico, ya que el formato de .xcodeproj es complejo.
        # Buscaremos principalmente en package.xcworkspace/xcshareddata/swiftpm/...
        
        dependencies = []
        swiftpm_config_path = os.path.join(xcodeproj_path, "project.xcworkspace", "xcshareddata", "swiftpm", "configuration")
        
        if os.path.exists(swiftpm_config_path):
            self.logger.info(f"✅ Encontrada configuración SPM en: {swiftpm_config_path}")
            
            # Buscar archivos .xcconfig o .plist
            for file_name in os.listdir(swiftpm_config_path):
                if file_name.endswith('.xcconfig'):
                    config_deps = self._parse_xcconfig(os.path.join(swiftpm_config_path, file_name))
                    dependencies.extend(config_deps)
        
        return dependencies
    
    def _parse_xcconfig(self, file_path: str) -> List[Dict]:
        """Parsea un archivo .xcconfig para buscar referencias a SPM"""
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Buscar referencias a SPM - esto es un enfoque básico
            # Un análisis más profundo requeriría entender mejor la estructura de estos archivos
            spm_refs = re.finditer(r'SWIFTPM_PACKAGE_URL\s*=\s*([^\n]+)', content)
            
            for match in spm_refs:
                url = match.group(1).strip()
                name = url.split('/')[-1].replace('.git', '')
                
                dependency = {
                    'name': name,
                    'url': url,
                    'version': 'N/A',  # No podemos obtener la versión del xcconfig
                    'type': 'spm_app_direct',
                    'source': 'xcconfig'
                }
                dependencies.append(dependency)
        
        except Exception as e:
            self.logger.error(f"❌ Error parseando {file_path}: {str(e)}")
        
        return dependencies
    
    def _parse_pbxproj_for_spm(self, file_path: str) -> List[Dict]:
      """
      Parsea un archivo project.pbxproj para buscar referencias a dependencias SPM.
      Versión mejorada con mejor detección de patrones.
      """
      dependencies = []
      
      try:
          with open(file_path, 'r', encoding='utf-8') as f:
              content = f.read()
          
          self.logger.info(f"📄 Analizando contenido de project.pbxproj ({len(content)} bytes)")
          
          # Identificar sección de XCRemoteSwiftPackageReference
          package_refs_section = re.search(r'\/\* Begin XCRemoteSwiftPackageReference section \*\/\s+(.*?)\/\* End XCRemoteSwiftPackageReference section \*\/', content, re.DOTALL)
          
          if not package_refs_section:
              self.logger.warning("⚠️ No se encontró sección XCRemoteSwiftPackageReference en project.pbxproj")
              # Buscar referencias individuales como alternativa
              package_refs = re.finditer(r'XCRemoteSwiftPackageReference\s+"([^"]+)"\s*=\s*\{\s*isa\s+=\s+XCRemoteSwiftPackageReference;\s+repositoryURL\s+=\s+"([^"]+)"', content, re.DOTALL)
              
              for match in package_refs:
                  ref_name = match.group(1)
                  url = match.group(2)
                  self.logger.info(f"🔹 Encontrada referencia individual: {ref_name} - {url}")
                  
                  # Buscar información de versión
                  version_info = self._extract_version_info(content, ref_name)
                  
                  dependency = {
                      'name': url.split('/')[-1].replace('.git', ''),
                      'url': url,
                      'version': version_info,
                      'type': 'spm_app_direct',
                      'source': 'project.pbxproj'
                  }
                  dependencies.append(dependency)
              
              return dependencies
          
          # Analizar la sección de XCRemoteSwiftPackageReference
          refs_section = package_refs_section.group(1)
          self.logger.info(f"✅ Sección XCRemoteSwiftPackageReference encontrada ({len(refs_section)} bytes)")
          
          # Extraer cada referencia a paquete
          package_entries = re.finditer(r'([A-F0-9]{24})\s*\/\*\s*([^*]+)\s*\*\/\s*=\s*\{\s*isa\s*=\s*XCRemoteSwiftPackageReference;\s*repositoryURL\s*=\s*"([^"]+)";\s*requirement\s*=\s*\{([^}]+)\}', refs_section, re.DOTALL)
          
          for entry in package_entries:
              ref_id = entry.group(1)
              ref_name = entry.group(2).strip()
              url = entry.group(3)
              req_block = entry.group(4)
              
              self.logger.info(f"🔹 Encontrado paquete: {ref_name} - {url}")
              
              # Extraer información de versión
              version = "N/A"
              
              if 'kind = exactVersion' in req_block:
                  version_match = re.search(r'version\s*=\s*"([^"]+)"', req_block)
                  if version_match:
                      version = version_match.group(1)
              elif 'kind = upToNextMajorVersion' in req_block:
                  version_match = re.search(r'minimumVersion\s*=\s*"([^"]+)"', req_block)
                  if version_match:
                      version = f"~> {version_match.group(1)}"
              elif 'kind = upToNextMinorVersion' in req_block:
                  version_match = re.search(r'minimumVersion\s*=\s*"([^"]+)"', req_block)
                  if version_match:
                      version = f"~> {version_match.group(1)}"
              elif 'kind = branch' in req_block:
                  branch_match = re.search(r'branch\s*=\s*"([^"]+)"', req_block)
                  if branch_match:
                      version = f"branch: {branch_match.group(1)}"
              elif 'kind = revision' in req_block:
                  revision_match = re.search(r'revision\s*=\s*"([^"]+)"', req_block)
                  if revision_match:
                      version = f"revision: {revision_match.group(1)[:8]}"
              
              package_name = ref_name.strip()
              if not package_name:
                  package_name = url.split('/')[-1].replace('.git', '')
              
              dependency = {
                  'name': package_name,
                  'url': url,
                  'version': version,
                  'type': 'spm_app_direct',
                  'source': 'project.pbxproj',
                  'ref_id': ref_id
              }
              dependencies.append(dependency)
          
          # Si no encontramos nada con el patrón anterior, intentar con uno más simple
          if not dependencies:
              self.logger.info("🔍 Intentando con patrón alternativo...")
              simple_refs = re.finditer(r'isa\s*=\s*XCRemoteSwiftPackageReference;\s*repositoryURL\s*=\s*"([^"]+)"', content)
              
              for match in simple_refs:
                  url = match.group(1)
                  name = url.split('/')[-1].replace('.git', '')
                  self.logger.info(f"🔹 Encontrada referencia simple: {name} - {url}")
                  
                  dependency = {
                      'name': name,
                      'url': url,
                      'version': 'N/A',
                      'type': 'spm_app_direct',
                      'source': 'project.pbxproj'
                  }
                  dependencies.append(dependency)
          
          # Búsqueda desesperada: extraer todas las URLs que parecen ser de GitHub/GitLab
          if not dependencies:
              self.logger.info("🔍 Búsqueda de último recurso por URLs de repositorios...")
              url_pattern = r'repositoryURL\s*=\s*"(https://(?:github|gitlab).com/[^"]+)"'
              url_matches = re.finditer(url_pattern, content)
              
              for match in url_matches:
                  url = match.group(1)
                  name = url.split('/')[-1].replace('.git', '')
                  self.logger.info(f"🔹 URL de repositorio encontrada: {url}")
                  
                  dependency = {
                      'name': name,
                      'url': url,
                      'version': 'N/A',
                      'type': 'spm_app_direct',
                      'source': 'project.pbxproj'
                  }
                  dependencies.append(dependency)
      
      except Exception as e:
          self.logger.error(f"❌ Error parseando {file_path}: {str(e)}")
      
      # Mostrar resultados
      if dependencies:
          self.logger.info(f"📊 Encontradas {len(dependencies)} dependencias en {file_path}:")
          for dep in dependencies:
              self.logger.info(f"  - {dep['name']} ({dep['url']}) - {dep['version']}")
      else:
          self.logger.warning(f"⚠️ No se encontraron dependencias SPM en {file_path}")
      
      return dependencies
    
    def _parse_package_swift(self, file_path: str) -> List[Dict]:
        """
        Parsea un archivo Package.swift para extraer dependencias SPM.
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
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
                                'type': 'spm_app_direct',
                                'source': 'Package.swift'
                            }
                            
                            if 'apple.com' in url.lower():
                                dependency['isAppleDependency'] = True
                            
                            dependencies.append(dependency)
        
        except Exception as e:
            self.logger.error(f"❌ Error al analizar Package.swift: {str(e)}")
        
        self.logger.info(f"📑 Encontradas {len(dependencies)} dependencias en {file_path}")
        return dependencies
      
    def _find_main_xcodeproj(self) -> Optional[str]:
        """
        Intenta determinar cuál es el proyecto Xcode principal de la aplicación.
        Estrategias:
        1. Si hay un único .xcodeproj, ese es el principal
        2. Si hay varios, buscar el que tenga nombre similar al directorio
        3. Si hay varios, buscar el que contenga AppDelegate.swift
        4. Si todo falla, retornar el primer .xcodeproj encontrado
        """
        xcodeproj_paths = []
        
        # Buscar todos los .xcodeproj
        for root, dirs, _ in os.walk(self.project_root):
            for dir_name in dirs:
                if dir_name.endswith('.xcodeproj'):
                    xcodeproj_paths.append(os.path.join(root, dir_name))
        
        if not xcodeproj_paths:
            self.logger.warning("⚠️ No se encontraron archivos .xcodeproj")
            return None
        
        if len(xcodeproj_paths) == 1:
            return xcodeproj_paths[0]
        
        # Si hay varios, intentar encontrar el principal
        
        # Estrategia 1: Nombre similar al directorio del proyecto
        project_dir_name = os.path.basename(self.project_root)
        for path in xcodeproj_paths:
            xcodeproj_name = os.path.basename(path).replace('.xcodeproj', '')
            if xcodeproj_name.lower() == project_dir_name.lower():
                self.logger.info(f"✅ Proyecto principal detectado por nombre: {path}")
                return path
        
        # Estrategia 2: Buscar el que contenga AppDelegate.swift
        for xcodeproj_path in xcodeproj_paths:
            parent_dir = os.path.dirname(xcodeproj_path)
            for root, _, files in os.walk(parent_dir):
                if 'AppDelegate.swift' in files:
                    self.logger.info(f"✅ Proyecto principal detectado por AppDelegate: {xcodeproj_path}")
                    return xcodeproj_path
        
        # Si todo falla, usar el primer .xcodeproj
        self.logger.info(f"⚠️ No se pudo determinar el proyecto principal, usando el primero: {xcodeproj_paths[0]}")
        return xcodeproj_paths[0]
    
    def _extract_version_info(self, content: str, ref_name: str) -> str:
      """Extrae información de versión para una referencia de paquete específica"""
      # Buscar bloque de requirement para esta referencia
      req_pattern = rf'repositoryURL\s+=\s+"[^"]+";\s+requirement\s+=\s+\{{(.*?)\}};\s*\}};'
      req_match = re.search(req_pattern, content, re.DOTALL)
      
      if not req_match:
          return "N/A"
      
      req_block = req_match.group(1)
      
      # Extraer información de versión según el tipo
      if 'kind = exactVersion' in req_block:
          version_match = re.search(r'version\s*=\s*"([^"]+)"', req_block)
          if version_match:
              return version_match.group(1)
      elif 'kind = upToNextMajorVersion' in req_block:
          version_match = re.search(r'minimumVersion\s*=\s*"([^"]+)"', req_block)
          if version_match:
              return f"~> {version_match.group(1)}"
      elif 'kind = upToNextMinorVersion' in req_block:
          version_match = re.search(r'minimumVersion\s*=\s*"([^"]+)"', req_block)
          if version_match:
              return f"~> {version_match.group(1)}"
      elif 'kind = branch' in req_block:
          branch_match = re.search(r'branch\s*=\s*"([^"]+)"', req_block)
          if branch_match:
              return f"branch: {branch_match.group(1)}"
      elif 'kind = revision' in req_block:
          revision_match = re.search(r'revision\s*=\s*"([^"]+)"', req_block)
          if revision_match:
              return f"revision: {revision_match.group(1)[:8]}"
      
      return "N/A"