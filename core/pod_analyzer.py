# pod_analyzer/pod_analyzer.py

import os
import re
import logging
import requests
import yaml
from typing import List, Dict, Optional

class PodfileAnalyzer:
    def __init__(self, project_root: str):
        self.project_root = os.path.abspath(project_root)
        self.logger = self._setup_logging()
        self.pods = []
        self.unique_dependencies = {}
        self.pods_versions_cache = {}

    def _setup_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def find_podfile(self) -> Optional[str]:
      """Busca el Podfile en el directorio del proyecto"""
      self.logger.info(f"\n🔍 Buscando Podfile en: {self.project_root}")
      
      podfile_path = os.path.join(self.project_root, 'Podfile')
      if os.path.exists(podfile_path):
          self.logger.info(f"✅ Podfile encontrado en: {podfile_path}")
          return podfile_path
      
      self.logger.info("❌ No se encontró Podfile")
      return None
  
    def get_pod_info(self, pod_name: str) -> Dict:
        try:
            base_pod_name = pod_name.split('/')[0]
            api_url = f"https://trunk.cocoapods.org/api/v1/pods/{base_pod_name}"
            
            response = requests.get(api_url)
            if response.status_code == 200:
                data = response.json()
                versions = data.get('versions', [])
                if versions:
                    latest_version = max(versions, key=lambda x: x.get('created_at', ''))
                    self.logger.info(latest_version)
                    return {
                        'version': latest_version.get('name'),
                        'url': 'N/A'
                    }
            
            self.logger.info(f"No se encontró información para {pod_name}")
        except Exception as e:
            self.logger.error(f"Error obteniendo info para {pod_name}: {str(e)}")
        
        return {'version': 'N/A', 'url': 'N/A'}

    def _process_pod_dependency(self, pod_name: str, version: str = None) -> Dict:
        pod_info = self.get_pod_info(pod_name)
        current_version = self.get_current_pod_version(pod_name)
        return {
            'name': pod_name,
            'version': current_version,
            'latest_version': pod_info.get('version'),
            'url': pod_info.get('url', 'N/A')
        }
    
    def get_current_pod_version(self, pod_name: str) -> str:
        """Obtiene la versión actual de un pod desde Podfile.lock"""
        try:
            # Buscar Podfile.lock en el directorio del proyecto y sus padres
            current_dir = self.project_root
            while current_dir != '/':
                lock_path = os.path.join(current_dir, 'Podfile.lock')
                if os.path.exists(lock_path):
                    with open(lock_path, 'r') as file:
                        lock_data = yaml.safe_load(file)
                        pods = lock_data.get('PODS', [])
                        for pod in pods:
                            if isinstance(pod, str):
                                name, version = pod.split(' (')
                                if name == pod_name:
                                    return version.rstrip(')')
                            elif isinstance(pod, dict):
                                for name, deps in pod.items():
                                    if name.split(' (')[0] == pod_name:
                                        return name.split(' (')[1].rstrip(')')
                    return 'N/A'
                current_dir = os.path.dirname(current_dir)
            return 'N/A'
        except Exception as e:
            self.logger.error(f"Error leyendo Podfile.lock para {pod_name}: {str(e)}")
            return 'N/A'

    def parse_podfile(self, podfile_path: str) -> List[Dict]:
        """Analiza el Podfile para extraer las dependencias"""
        self.logger.info(f"\n📝 Analizando Podfile: {podfile_path}")
        dependencies_dict = {}  # Usar diccionario para evitar duplicados
        
        try:
            with open(podfile_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                pod_lines = [line.strip() for line in content.split('\n') if line.strip().startswith('pod ')]
                
                for line in pod_lines:
                    pod_name_match = re.search(r'pod\s+[\'"]([^\'"]+)[\'"]', line)
                    if not pod_name_match:
                        continue
                    
                    pod_name = pod_name_match.group(1).split('/')[0]  # Obtener nombre base del pod
                    
                    # Si ya existe este pod, comparar versiones y mantener la más reciente
                    if pod_name in dependencies_dict:
                        continue
                    
                    version_match = re.search(r'[\'"]([0-9][^\'"]*)[\'"]\s*[,}]', line)
                    version = version_match.group(1) if version_match else None
                    
                    dependency = self._process_pod_dependency(pod_name, version)
                    dependencies_dict[pod_name] = dependency
                    self.logger.info(f"📦 Procesado: {dependency}")
        
        except Exception as e:
            self.logger.error(f"❌ Error al analizar Podfile: {str(e)}")
        
        return list(dependencies_dict.values())
    
    def get_latest_pod_version(self, pod_name: str) -> str:
        """Obtiene la última versión disponible de un pod desde cocoapods.org"""
        try:
            url = f"https://cocoapods.org/pods/{pod_name}"
            self.logger.info(f"🔍 Buscando versión para {pod_name} en {url}")
            
            response = requests.get(url)
            if response.status_code == 200:
                # Buscar la versión en el contenido HTML
                version_pattern = r'<span class="version">(.*?)</span>'
                match = re.search(version_pattern, response.text)
                if match:
                    version = match.group(1)
                    self.logger.info(f"✅ Versión encontrada: {version}")
                    return version
        except Exception as e:
            self.logger.error(f"❌ Error obteniendo versión para {pod_name}: {str(e)}")
        
        return "N/A"