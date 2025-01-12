# spm_generator/utils/version_checker.py

import os
import json
import re
import requests
from datetime import datetime, timedelta

class VersionChecker:
    def __init__(self, use_cache_only=False):
        print("\n🔧 Inicializando VersionChecker")
        print(f"  Mode: {'Solo Caché' if use_cache_only else 'Caché + API'}")
        
        # Crear directorio results si no existe
        self.results_dir = "results"
        if not os.path.exists(self.results_dir):
            os.makedirs(self.results_dir)
            print(f"  📁 Directorio '{self.results_dir}' creado")
        
        self.cache_file = os.path.join(self.results_dir, 'version_cache.json')
        print(f"  📝 Archivo de caché: {self.cache_file}")
        
        self.cache_duration = timedelta(hours=24)
        print(f"  ⏰ Duración de caché: {self.cache_duration}")
        
        self.version_cache = self._load_cache()
        self.use_cache_only = use_cache_only
        
        print(f"  📦 Entradas en caché: {len(self.version_cache)}")
        if len(self.version_cache) > 0:
            print("  Dependencias en caché:")
            for url, data in self.version_cache.items():
                print(f"    - {url}: {data['version']} ({data['timestamp']})")

    def _load_cache(self):
        """Cargar cache desde archivo"""
        try:
            if os.path.exists(self.cache_file):
                print(f"\n📂 Cargando caché desde: {self.cache_file}")
                with open(self.cache_file, 'r') as f:
                    cache_data = json.load(f)
                    current_time = datetime.now()
                    valid_cache = {}
                    expired_entries = 0
                    
                    for key, value in cache_data.items():
                        try:
                            cached_time = datetime.fromisoformat(value['timestamp'])
                            time_diff = current_time - cached_time
                            
                            if time_diff < self.cache_duration:
                                valid_cache[key] = value
                                print(f"  ✅ Entrada válida: {key}")
                                print(f"     Versión: {value['version']}")
                                print(f"     Edad: {time_diff}")
                            else:
                                expired_entries += 1
                                print(f"  ⏰ Entrada expirada: {key}")
                                print(f"     Edad: {time_diff}")
                        except Exception as e:
                            print(f"  ❌ Error procesando entrada {key}: {str(e)}")
                    
                    print(f"\n📊 Resumen de caché:")
                    print(f"  Total entradas: {len(cache_data)}")
                    print(f"  Entradas válidas: {len(valid_cache)}")
                    print(f"  Entradas expiradas: {expired_entries}")
                    
                    return valid_cache
            else:
                print(f"\n📝 No existe archivo de caché en: {self.cache_file}")
                print("  Se creará uno nuevo cuando se obtengan versiones")
        except Exception as e:
            print(f"\n❌ Error cargando caché: {str(e)}")
        return {}

    def _save_cache(self):
        """Guardar cache en archivo"""
        try:
            print(f"\n💾 Guardando caché en: {self.cache_file}")
            print(f"  Entradas a guardar: {len(self.version_cache)}")
            with open(self.cache_file, 'w') as f:
                json.dump(self.version_cache, f, indent=2)
            print("  ✅ Caché guardado exitosamente")
        except Exception as e:
            print(f"  ❌ Error guardando caché: {str(e)}")

    def _cache_version(self, url, version):
        """Guardar versión en cache"""
        print(f"\n📝 Guardando versión en caché:")
        print(f"  URL: {url}")
        print(f"  Versión: {version}")
        self.version_cache[url] = {
            'version': version,
            'timestamp': datetime.now().isoformat()
        }
        self._save_cache()

    def get_latest_github_version(self, url):
        """Obtener última versión de GitHub"""
        try:
            print(f"\n🔍 Analizando URL de GitHub: {url}")
            parts = url.replace("https://github.com/", "").replace(".git", "").split("/")
            if len(parts) < 2:
                print("❌ Formato de URL inválido")
                return "N/A"
                
            owner, repo = parts[0], parts[1]
            print(f"📂 Propietario: {owner}, Repositorio: {repo}")
            
            # Intentar obtener el último release
            release_url = f'https://api.github.com/repos/{owner}/{repo}/releases/latest'
            print(f"🌐 Consultando releases: {release_url}")
            
            headers = {}
            if 'GITHUB_TOKEN' in os.environ:
                headers['Authorization'] = f"token {os.environ['GITHUB_TOKEN']}"
                print("🔑 Usando token de GitHub")
            
            response = requests.get(release_url, headers=headers, timeout=5)
            print(f"📡 Estado de respuesta: {response.status_code}")
            print(f"   Contenido: {response.text[:200]}...")  # Mostrar los primeros 200 caracteres
            
            if response.status_code == 200:
                version = response.json()['tag_name']
                print(f"✅ Encontrado último release: {version}")
                return version
            
            # Si no hay releases, intentar con tags
            tags_url = f'https://api.github.com/repos/{owner}/{repo}/tags'
            print(f"🌐 Consultando tags: {tags_url}")
            
            response = requests.get(tags_url, headers=headers, timeout=5)
            print(f"📡 Estado de respuesta: {response.status_code}")
            print(f"   Contenido: {response.text[:200]}...")
            
            if response.status_code == 200 and response.json():
                version = response.json()[0]['name']
                print(f"✅ Encontrado último tag: {version}")
                return version
            
            print("❌ No se encontraron releases ni tags")
                
        except Exception as e:
            print(f"❌ Error obteniendo versión de GitHub: {str(e)}")
        return "N/A"

    def get_latest_gitlab_version(self, url):
        """Obtener última versión de GitLab"""
        try:
            print(f"\n🔍 Analizando URL de GitLab: {url}")
            parts = url.replace("https://gitlab.com/", "").replace(".git", "").split("/")
            if len(parts) < 2:
                print("❌ Formato de URL inválido")
                return "N/A"
                
            owner, repo = parts[0], parts[1]
            encoded_project = f'{owner}%2F{repo}'
            print(f"📂 Propietario: {owner}, Repositorio: {repo}")
            print(f"🔧 ID de proyecto codificado: {encoded_project}")
            
            headers = {}
            if 'GITLAB_TOKEN' in os.environ:
                headers['PRIVATE-TOKEN'] = os.environ['GITLAB_TOKEN']
                print("🔑 Usando token de GitLab")
            
            # Intentar obtener el último release
            release_url = f'https://gitlab.com/api/v4/projects/{encoded_project}/releases'
            print(f"🌐 Consultando releases: {release_url}")
            
            response = requests.get(release_url, headers=headers, timeout=5)
            print(f"📡 Estado de respuesta: {response.status_code}")
            print(f"   Contenido: {response.text[:200]}...")
            
            if response.status_code == 200 and response.json():
                version = response.json()[0]['tag_name']
                print(f"✅ Encontrado último release: {version}")
                return version
            
            # Si no hay releases, intentar con tags
            tags_url = f'https://gitlab.com/api/v4/projects/{encoded_project}/repository/tags'
            print(f"🌐 Consultando tags: {tags_url}")
            
            response = requests.get(tags_url, headers=headers, timeout=5)
            print(f"📡 Estado de respuesta: {response.status_code}")
            print(f"   Contenido: {response.text[:200]}...")
            
            if response.status_code == 200 and response.json():
                version = response.json()[0]['name']
                print(f"✅ Encontrado último tag: {version}")
                return version
            
            print("❌ No se encontraron releases ni tags")
                
        except Exception as e:
            print(f"❌ Error obteniendo versión de GitLab: {str(e)}")
        return "N/A"

    def _parse_version(self, version):
        """
        Parsea una versión y retorna sus componentes major, minor y patch
        Args:
            version (str): String de versión (ej: "v1.2.3" o "1.2.3")
        Returns:
            tuple: (major, minor, patch) o None si no se puede parsear
        """
        try:
            version = version.lower().strip('v')
            version_match = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
            if version_match:
                major, minor, patch = map(int, version_match.groups())
                return major, minor, patch
            return None
        except Exception:
            return None

    def _get_version_status(self, current_version, latest_version, url):
        """
        Determina el estado de la versión basado en la diferencia entre versiones.
        Returns:
            - 🔴 : Diferencia Major
            - 🟡 : Diferencia Minor o Patch > 5
            - 🟢 : Versiones iguales o Patch < 5
        """
        print(f"\n🔄 Analizando versiones para {url}")
        print(f"  Versión actual: {current_version}")
        print(f"  Última versión: {latest_version}")
        
        if current_version == "N/A" or latest_version == "N/A":
            print("⚫ No se puede determinar - Una o ambas versiones son N/A")
            return "⚫"
            
        current = self._parse_version(current_version)
        latest = self._parse_version(latest_version)
        
        if not current or not latest:
            print("⚫ No se puede determinar - Error al parsear versiones")
            print(f"  Resultado del parseo - Actual: {current}, Última: {latest}")
            return "⚫"
            
        current_major, current_minor, current_patch = current
        latest_major, latest_minor, latest_patch = latest
        
        print(f"📊 Versiones parseadas:")
        print(f"  Actual: {current_major}.{current_minor}.{current_patch}")
        print(f"  Última: {latest_major}.{latest_minor}.{latest_patch}")
        
        # Diferencia Major
        if latest_major > current_major:
            print(f"🔴 Diferencia Major detectada ({latest_major} > {current_major})")
            return "🔴"
        
        # Si estamos en el mismo Major
        if latest_major == current_major:
            print(f"  ✓ Major iguales ({current_major})")
            
            # Diferencia Minor
            if latest_minor > current_minor:
              print(f"  ➜ Minor mayor ({latest_minor} > {current_minor})")
              return "🟡"
            # Mismo Minor 
            elif abs(latest_patch - current_patch) >= 5:
              patch_diff = abs(latest_patch - current_patch)
              print(f"  ➜ Diferencia de Patch: {patch_diff}")
              print("🟡 Diferencia de Patch mayor o igual a 5")
            elif latest_minor == current_minor:
                patch_diff = abs(latest_patch - current_patch)
                print(f"  ✓ Minor iguales ({current_minor})")
                print(f"  ➜ Diferencia de Patch: {patch_diff}")
                
                if patch_diff <= 5:
                    print("🟢 Diferencia de Patch menor o igual a 5")
                    return "🟢"
                else:
                    print("🟡 Diferencia de Patch mayor a 5")
                    return "🟡"
        
        print("🟢 Versión actual está al día o es más reciente")
        return "🟢"

    def get_latest_version(self, url):
        """
        Determinar el tipo de repositorio y obtener la última versión disponible
        """
        print(f"\n🔍 Buscando última versión para: {url}")

        # Verificar cache primero
        if self.use_cache_only:
            if url in self.version_cache:
                cached_version = self.version_cache[url]['version']
                print(f"📦 Usando versión en caché: {cached_version}")
                return cached_version
            print("❌ No se encontró versión en caché")
            return "N/A (cache)"

        if url in self.version_cache:
            cache_entry = self.version_cache[url]
            cache_time = datetime.fromisoformat(cache_entry['timestamp'])
            if datetime.now() - cache_time < self.cache_duration:
                print(f"📦 Usando versión en caché: {cache_entry['version']}")
                return cache_entry['version']

        try:
            # Determinar el tipo de repositorio y obtener la versión
            if "github.com" in url:
                print("🔄 Consultando API de GitHub...")
                version = self.get_latest_github_version(url)
            elif "gitlab.com" in url:
                print("🔄 Consultando API de GitLab...")
                version = self.get_latest_gitlab_version(url)
            else:
                print("❌ URL no soportada (no es GitHub ni GitLab)")
                version = "N/A"
            
            print(f"📝 Versión obtenida: {version}")
            self._cache_version(url, version)
            return version
            
        except Exception as e:
            print(f"❌ Error al obtener la versión: {str(e)}")
            return "N/A"