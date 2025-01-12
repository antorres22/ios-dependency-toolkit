# spm_generator/main.py

import os
import argparse
import logging
import sys
import subprocess

def check_and_install_requests():
    """Verifica si requests está instalado y lo instala si es necesario"""
    try:
        import requests
    except ImportError:
        print("📦 Instalando dependencia requerida: requests")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "requests"])
            print("✅ requests instalado correctamente")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error instalando requests: {e}")
            sys.exit(1)

def main():
    """
    Punto de entrada principal del generador de diagramas SPM.
    Maneja los argumentos de la línea de comandos y la ejecución del programa.
    """
    # Verificar e instalar dependencias
    check_and_install_requests()

    # Ahora podemos importar el generador
    from core.generator import SPMDiagramGenerator
    
    parser = argparse.ArgumentParser(
        description='Generador de diagramas SPM para proyectos iOS',
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    parser.add_argument(
        '--path', '-p',
        help='Ruta al proyecto iOS'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Mostrar información detallada'
    )
    
    parser.add_argument(
        '--cached', '-c',
        action='store_true',
        help='Usar solo versiones en caché (sin consultas remotas)'
    )
    
    args = parser.parse_args()
    
    # Configurar logging si se solicita modo verbose
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.info("Modo verbose activado")
    
    # Obtener la ruta del proyecto
    project_path = args.path
    if not project_path:
        project_path = input("Por favor, introduce la ruta completa de tu proyecto iOS: ").strip()
    
    if not project_path:
        project_path = os.getcwd()
        logging.info(f"Usando directorio actual: {project_path}")
    
    # Validar que la ruta existe
    if not os.path.exists(project_path):
        logging.error(f"❌ Error: La ruta {project_path} no existe")
        return
    
    try:
        # Crear instancia del generador
        diagram_generator = SPMDiagramGenerator(project_path, use_cache=args.cached)
        
        if args.cached:
            logging.info("🔄 Usando modo caché (sin consultas remotas)")
        
        # Buscar módulos SPM
        spm_modules = diagram_generator.find_spm_modules()
        
        if spm_modules:
            # Generar el diagrama
            output_file = diagram_generator.generate_drawio_diagram()
            logging.info(f"\n📊 Diagrama generado exitosamente en: {output_file}")
            logging.info("\nPuedes abrir este archivo en draw.io o en la aplicación de escritorio Diagrams")
        else:
            logging.warning("\n⚠️  No se encontraron módulos SPM en el proyecto")
            
    except Exception as e:
        logging.error(f"\n❌ Error durante la generación del diagrama: {str(e)}")
        if args.verbose:
            logging.exception("Detalles del error:")
        return

if __name__ == "__main__":
    main()