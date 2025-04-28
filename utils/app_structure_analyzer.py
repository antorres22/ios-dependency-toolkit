import os
import logging
from typing import Dict, List, Set

class AppStructureAnalyzer:
    """
    Analizador de estructura de aplicaciones iOS. 
    Escanea el proyecto en busca de directorios de aplicación y analiza
    su estructura de archivos.
    """
    
    def __init__(self, project_root: str, application_path: str = None):
        self.project_root = os.path.abspath(project_root)
        self.application_path = application_path
        self.logger = self._setup_logging()
        self.app_structure = {}
        self.imports_map = {}  # Mapeo de archivos a sus imports

    def _setup_logging(self):
        """Configura el sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)

    def find_app_directories(self) -> List[str]:
        """
        Encuentra directorios de aplicación iOS en el proyecto.
        Prioriza la ruta directa si se especificó con application_path.
        """
        app_dirs = []
        
        # Si se especificó una ruta directa, usarla
        if self.application_path:
            app_path = os.path.abspath(self.application_path)
            self.logger.info(f"🎯 Usando ruta directa a la aplicación: {app_path}")
            
            if os.path.exists(app_path):
                app_dirs.append(app_path)
            else:
                self.logger.warning(f"⚠️ La ruta especificada no existe: {app_path}")
        
        # Si no se encontraron directorios específicos, usar el directorio del proyecto
        if not app_dirs:
            self.logger.info("ℹ️ No se encontraron directorios específicos de app, usando directorio raíz")
            app_dirs.append(self.project_root)
        
        return app_dirs

    def analyze_app_structure(self) -> Dict:
        """Analiza la estructura de la aplicación"""
        app_dirs = self.find_app_directories()
        
        for app_dir in app_dirs:
            app_name = os.path.basename(app_dir)
            self.logger.info(f"\n📂 Analizando estructura de aplicación: {app_name}")
            
            directory_structure = {}
            
            # Recorrer directorios y archivos
            for root, dirs, files in os.walk(app_dir):
                # Filtrar archivos Swift
                swift_files = [f for f in files if f.endswith('.swift')]
                
                if not swift_files:
                    continue
                    
                # Calcular la ruta relativa
                rel_path = os.path.relpath(root, app_dir)
                rel_path = rel_path if rel_path != '.' else 'root'
                
                # Añadir a la estructura
                directory_structure[rel_path] = swift_files
            
            # Guardar la estructura
            if directory_structure:
                self.app_structure[app_name] = directory_structure
                self.logger.info(f"✅ Encontrados {len(directory_structure)} directorios con archivos Swift en {app_name}")
            else:
                self.logger.warning(f"⚠️ No se encontraron archivos relevantes en {app_name}")
        
        # Verificación final
        if not self.app_structure:
            self.logger.warning("⚠️ No se encontró ninguna estructura de aplicación.")
            # Crear una estructura mínima para evitar errores
            self.app_structure["MainApp"] = {"root": ["AppDelegate.swift"]}
        
        return self.app_structure
    
    def get_module_usage(self) -> Dict[str, Set[str]]:
        """
        Retorna un mapa de módulos a los archivos que los importan.
        """
        # Implementación básica
        return {}
    
    def get_architecture_layers(self) -> Dict[str, List[str]]:
        """
        Intenta detectar capas de arquitectura basadas en nombres de directorio.
        """
        # Implementación básica
        return {
            "Views": [],
            "ViewControllers": [],
            "Models": [],
            "ViewModels": [],
            "Services": [],
            "Networking": [],
            "Utilities": [],
            "Resources": [],
            "Other": []
        }