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
    
    def _debug_extract_spm_info(self, file_path: str) -> List[Dict]:
        """
        Función de diagnóstico para extraer toda la información posible sobre paquetes SPM
        del archivo project.pbxproj, mostrando los bloques completos encontrados.
        """
        dependencies = []
        debug_info = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info(f"🔍 ANÁLISIS DE DIAGNÓSTICO: {file_path}")
            
            # 1. Buscar sección de XCRemoteSwiftPackageReference
            self.logger.info("1. Buscando sección XCRemoteSwiftPackageReference")
            section_match = re.search(r'\/\* Begin XCRemoteSwiftPackageReference section \*\/\s+(.*?)\/\* End XCRemoteSwiftPackageReference section \*\/', content, re.DOTALL)
            
            if section_match:
                section = section_match.group(1)
                self.logger.info(f"✅ Sección encontrada: {len(section)} bytes")
                debug_info.append({"section": "XCRemoteSwiftPackageReference", "content_size": len(section)})
                
                # Extraer todos los bloques de la sección
                blocks = re.finditer(r'([A-F0-9]+)\s+\/\*\s+(.*?)\s+\*\/\s+=\s+{(.*?)};', section, re.DOTALL)
                
                for i, block in enumerate(blocks):
                    block_id = block.group(1)
                    block_name = block.group(2)
                    block_content = block.group(3)
                    
                    self.logger.info(f"\nBloque #{i+1}: ID={block_id}, Nombre={block_name}")
                    self.logger.info(f"Contenido: {block_content}")
                    
                    # Extraer URL y requirement
                    url_match = re.search(r'repositoryURL\s+=\s+"([^"]+)"', block_content)
                    req_match = re.search(r'requirement\s+=\s+{(.*?)}', block_content, re.DOTALL)
                    
                    url = url_match.group(1) if url_match else "No URL encontrada"
                    req = req_match.group(1) if req_match else "No requirement encontrado"
                    
                    self.logger.info(f"URL: {url}")
                    self.logger.info(f"Requirement: {req}")
                    
                    # Guardar la información de debug
                    debug_info.append({
                        "block_id": block_id,
                        "block_name": block_name,
                        "url": url,
                        "requirement": req,
                        "full_content": block_content
                    })
                    
                    # Intentar extraer detalles del requirement
                    if req_match:
                        kind_match = re.search(r'kind\s+=\s+([^;]+);', req)
                        version_match = re.search(r'version\s+=\s+"([^"]+)"', req)
                        min_version_match = re.search(r'minimumVersion\s+=\s+"([^"]+)"', req)
                        max_version_match = re.search(r'maximumVersion\s+=\s+"([^"]+)"', req)
                        branch_match = re.search(r'branch\s+=\s+"([^"]+)"', req)
                        revision_match = re.search(r'revision\s+=\s+"([^"]+)"', req)
                        
                        kind = kind_match.group(1) if kind_match else "No kind encontrado"
                        self.logger.info(f"Kind: {kind}")
                        
                        if version_match:
                            self.logger.info(f"Version: {version_match.group(1)}")
                        if min_version_match:
                            self.logger.info(f"Min Version: {min_version_match.group(1)}")
                        if max_version_match:
                            self.logger.info(f"Max Version: {max_version_match.group(1)}")
                        if branch_match:
                            self.logger.info(f"Branch: {branch_match.group(1)}")
                        if revision_match:
                            self.logger.info(f"Revision: {revision_match.group(1)}")
                    
                    # Añadir a las dependencias
                    name = block_name.strip() or url.split('/')[-1].replace('.git', '')
                    version = "Extracción en diagnóstico"
                    
                    dependencies.append({
                        'name': name,
                        'url': url if url_match else "Desconocida",
                        'version': version,
                        'type': 'spm_app_direct',
                        'source': 'project.pbxproj_debug',
                        'debug_info': debug_info[-1]
                    })
            else:
                self.logger.info("❌ No se encontró sección XCRemoteSwiftPackageReference")
            
            # 2. Buscar patrones de paquetes individuales
            self.logger.info("\n2. Buscando patrones de paquetes individuales")
            package_patterns = [
                r'XCRemoteSwiftPackageReference\s+"([^"]+)"\s+=\s+{(.*?)};',
                r'isa\s+=\s+XCRemoteSwiftPackageReference;\s+repositoryURL\s+=\s+"([^"]+)";\s+requirement\s+=\s+{(.*?)}'
            ]
            
            for pattern_idx, pattern in enumerate(package_patterns):
                self.logger.info(f"Probando patrón #{pattern_idx+1}: {pattern[:30]}...")
                matches = re.finditer(pattern, content, re.DOTALL)
                
                for i, match in enumerate(matches):
                    if pattern_idx == 0:  # Primer patrón con nombre
                        name = match.group(1)
                        content_block = match.group(2)
                        self.logger.info(f"\nPaquete #{i+1} (Patrón 1): Nombre={name}")
                        self.logger.info(f"Contenido: {content_block}")
                        
                        url_match = re.search(r'repositoryURL\s+=\s+"([^"]+)"', content_block)
                        url = url_match.group(1) if url_match else "No URL encontrada"
                        self.logger.info(f"URL: {url}")
                        
                        req_match = re.search(r'requirement\s+=\s+{(.*?)}', content_block, re.DOTALL)
                        req = req_match.group(1) if req_match else "No requirement encontrado"
                        self.logger.info(f"Requirement: {req}")
                    else:  # Segundo patrón con URL directa
                        url = match.group(1)
                        req = match.group(2)
                        name = url.split('/')[-1].replace('.git', '')
                        self.logger.info(f"\nPaquete #{i+1} (Patrón 2): URL={url}")
                        self.logger.info(f"Requirement: {req}")
                    
                    # Guardar información de debug
                    debug_info.append({
                        "pattern": f"Package Pattern #{pattern_idx+1}",
                        "name": name,
                        "url": url,
                        "requirement": req
                    })
                    
                    # Añadir a las dependencias si no está duplicada
                    if not any(d['url'] == url for d in dependencies):
                        dependencies.append({
                            'name': name,
                            'url': url,
                            'version': "Extracción en diagnóstico",
                            'type': 'spm_app_direct',
                            'source': f'project.pbxproj_pattern_{pattern_idx+1}',
                            'debug_info': debug_info[-1]
                        })
            
            # 3. Buscar URLs directamente
            self.logger.info("\n3. Buscando URLs de repositorios directamente")
            url_pattern = r'repositoryURL\s+=\s+"(https://[^"]+)"'
            url_matches = re.finditer(url_pattern, content)
            
            for i, match in enumerate(url_matches):
                url = match.group(1)
                name = url.split('/')[-1].replace('.git', '')
                self.logger.info(f"\nURL #{i+1}: {url}")
                
                # Intentar encontrar el requirement asociado
                context_start = max(0, match.start() - 500)
                context_end = min(len(content), match.end() + 500)
                context = content[context_start:context_end]
                
                req_match = re.search(r'requirement\s+=\s+{(.*?)}', context, re.DOTALL)
                req = req_match.group(1) if req_match else "No requirement encontrado en contexto"
                self.logger.info(f"Requirement (en contexto): {req}")
                
                # Guardar información de debug
                debug_info.append({
                    "pattern": "Direct URL",
                    "url": url,
                    "context_size": len(context),
                    "requirement_context": req
                })
                
                # Añadir a las dependencias si no está duplicada
                if not any(d['url'] == url for d in dependencies):
                    dependencies.append({
                        'name': name,
                        'url': url,
                        'version': "Extracción en diagnóstico",
                        'type': 'spm_app_direct',
                        'source': 'project.pbxproj_url_direct',
                        'debug_info': debug_info[-1]
                    })
            
            # Guardar toda la información de diagnóstico en un archivo
            debug_file = os.path.join('results', 'pbxproj_debug_info.json')
            os.makedirs(os.path.dirname(debug_file), exist_ok=True)
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                json.dump(debug_info, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"\n📊 Información de diagnóstico guardada en: {debug_file}")
            
        except Exception as e:
            self.logger.error(f"❌ Error en diagnóstico: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
        
        return dependencies

    def find_app_spm_dependencies(self) -> List[Dict]:
        """
        Busca dependencias SPM directamente integradas en la aplicación iOS.
        Versión limpia sin logs excesivos.
        """
        self.logger.info(f"Buscando dependencias SPM integradas directamente en la aplicación")
        
        # Lista para almacenar todas las dependencias encontradas
        all_dependencies = []
        
        # Determinar el archivo de proyecto principal
        main_xcodeproj = self._find_main_xcodeproj()
        if main_xcodeproj:
            main_pbxproj = os.path.join(main_xcodeproj, "project.pbxproj")
            
            if os.path.exists(main_pbxproj):
                # Usar la función mejorada para analizar el archivo
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
            dependencies = self._parse_package_resolved(path)
            
            # Añadir solo las que no están duplicadas (por URL)
            for dep in dependencies:
                if not any(d['url'] == dep['url'] for d in all_dependencies):
                    all_dependencies.append(dep)
        
        self.direct_dependencies = all_dependencies
        self.logger.info(f"Total de dependencias SPM directas encontradas: {len(self.direct_dependencies)}")
        
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
        Versión limpia sin logs excesivos.
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.logger.info(f"Analizando archivo project.pbxproj")
            
            # Buscar todos los bloques con repositoryURL y requirement juntos
            repo_req_blocks = re.finditer(r'repositoryURL\s*=\s*"([^"]+)";\s*requirement\s*=\s*\{([^{]+?)(?=\n\t\t[A-Z0-9]|\Z)', content, re.DOTALL)
            
            for match in repo_req_blocks:
                url = match.group(1)
                req_block = match.group(2)
                
                # Determinar el nombre basado en la URL
                name = url.split('/')[-1].replace('.git', '')
                
                # Extraer la versión basada en el tipo de requisito
                version = "N/A"
                
                if 'kind = exactVersion' in req_block:
                    version_match = re.search(r'version\s*=\s*([^;]+);', req_block)
                    if version_match:
                        version = version_match.group(1).strip().replace('"', '')
                
                elif 'kind = upToNextMajorVersion' in req_block or 'kind = upToNextMinorVersion' in req_block:
                    min_version_match = re.search(r'minimumVersion\s*=\s*([^;]+);', req_block)
                    if min_version_match:
                        version = min_version_match.group(1).strip().replace('"', '')
                
                elif 'kind = branch' in req_block:
                    branch_match = re.search(r'branch\s*=\s*([^;]+);', req_block)
                    if branch_match:
                        version = branch_match.group(1).strip().replace('"', '')
                
                elif 'kind = revision' in req_block:
                    revision_match = re.search(r'revision\s*=\s*([^;]+);', req_block)
                    if revision_match:
                        version = revision_match.group(1).strip().replace('"', '')
                
                # Si no se encontró con los patrones específicos, intentar con un patrón genérico
                if version == "N/A":
                    any_version_match = re.search(r'(version|minimumVersion|branch|revision)\s*=\s*([^;]+);', req_block)
                    if any_version_match:
                        version = any_version_match.group(2).strip().replace('"', '')
                
                # Añadir a la lista de dependencias, evitando duplicados
                if not any(d['url'] == url for d in dependencies):
                    dependency = {
                        'name': name,
                        'url': url,
                        'version': version,
                        'type': 'spm_app_direct',
                        'source': 'project.pbxproj'
                    }
                    
                    dependencies.append(dependency)
            
            self.logger.info(f"Encontradas {len(dependencies)} dependencias SPM en project.pbxproj")
        
        except Exception as e:
            self.logger.error(f"Error parseando {file_path}: {str(e)}")
        
        return dependencies
    
    def _parse_requirement_block(self, req_block: str) -> str:
        """
        Analiza un bloque de requirement para extraer la información de versión.
        Esta versión es más robusta y reporta más detalles sobre el process.
        """
        if not req_block:
            return "N/A"
        
        self.logger.debug(f"Analizando bloque requirement: {req_block}")
        
        # Determinar el tipo de requirement
        kind_match = re.search(r'kind\s*=\s*([^;]+);', req_block)
        if not kind_match:
            self.logger.debug("No se encontró 'kind' en el bloque")
            return "N/A"
        
        kind = kind_match.group(1).strip()
        self.logger.debug(f"Tipo de requirement: {kind}")
        
        # Extraer versión según el tipo
        if 'exactVersion' in kind:
            version_match = re.search(r'version\s*=\s*"([^"]+)"', req_block)
            if version_match:
                version = version_match.group(1)
                self.logger.debug(f"Versión exacta encontrada: {version}")
                return version
        
        elif 'versionRange' in kind:
            min_match = re.search(r'minimumVersion\s*=\s*"([^"]+)"', req_block)
            max_match = re.search(r'maximumVersion\s*=\s*"([^"]+)"', req_block)
            
            if min_match and max_match:
                min_ver = min_match.group(1)
                max_ver = max_match.group(1)
                version = f"{min_ver} ... {max_ver}"
                self.logger.debug(f"Rango de versiones encontrado: {version}")
                return version
            elif min_match:
                version = f">= {min_match.group(1)}"
                self.logger.debug(f"Versión mínima encontrada: {version}")
                return version
        
        elif 'upToNextMajorVersion' in kind:
            min_match = re.search(r'minimumVersion\s*=\s*"([^"]+)"', req_block)
            if min_match:
                version = f"~> {min_match.group(1)}"
                self.logger.debug(f"Versión up-to-next-major encontrada: {version}")
                return version
        
        elif 'upToNextMinorVersion' in kind:
            min_match = re.search(r'minimumVersion\s*=\s*"([^"]+)"', req_block)
            if min_match:
                version = f"~> {min_match.group(1)}"
                self.logger.debug(f"Versión up-to-next-minor encontrada: {version}")
                return version
        
        elif 'branch' in kind:
            branch_match = re.search(r'branch\s*=\s*"([^"]+)"', req_block)
            if branch_match:
                version = f"branch: {branch_match.group(1)}"
                self.logger.debug(f"Branch encontrado: {version}")
                return version
        
        elif 'revision' in kind:
            revision_match = re.search(r'revision\s*=\s*"([^"]+)"', req_block)
            if revision_match:
                revision = revision_match.group(1)
                # Acortar el hash si es demasiado largo
                if len(revision) > 8:
                    revision = revision[:8]
                version = f"revision: {revision}"
                self.logger.debug(f"Revision encontrada: {version}")
                return version
        
        # Si llegamos aquí, no pudimos extraer la versión
        self.logger.debug(f"No se pudo extraer versión del tipo: {kind}")
        
        # Mostrar el bloque completo para depuración
        self.logger.debug(f"Bloque completo: {req_block}")
        
        return "N/A"
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
    
    def _extract_version_info(self, content: str, url: str) -> str:
        """
        Busca información de versión para una URL específica en todo el contenido.
        Versión mejorada que busca el requirement asociado a una URL.
        """
        # Escapar caracteres especiales en la URL para la búsqueda regex
        escaped_url = re.escape(url)
        
        # Buscar el bloque que contiene esta URL y su requirement
        pattern = rf'repositoryURL\s*=\s*"{escaped_url}";\s*requirement\s*=\s*\{{(.*?)\}}'
        req_match = re.search(pattern, content, re.DOTALL)
        
        if not req_match:
            self.logger.debug(f"No se encontró bloque requirement para URL: {url}")
            return "N/A"
        
        req_block = req_match.group(1)
        return self._parse_requirement_block(req_block)