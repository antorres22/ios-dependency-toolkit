#!/bin/bash

# Directorio base del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Valores por defecto
PYTHON_ARGS=""

# Procesar argumentos
POSITIONAL_ARGS=()
USE_CACHE=false
DEPENDENCIES_ONLY=false

while [[ $# -gt 0 ]]; do
  case $1 in
    --path)
      PROJECT_PATH="$2"
      PYTHON_ARGS="$PYTHON_ARGS --path $PROJECT_PATH"  # Quitamos las comillas extra
      shift 2
      ;;
    --cached)
      USE_CACHE=true
      PYTHON_ARGS="$PYTHON_ARGS --use-cache"
      shift
      ;;
    --dependencies-only|-d)
      DEPENDENCIES_ONLY=true
      PYTHON_ARGS="$PYTHON_ARGS --dependencies-only"
      shift
      ;;
    *)
      POSITIONAL_ARGS+=("$1")
      shift
      ;;
  esac
done

# Imprimir información de depuración
echo "🚀 Argumentos para script de Python: $PYTHON_ARGS"

# Crear entorno virtual si no existe
VENV_PATH="$SCRIPT_DIR/venv_spm_generator"
if [ ! -d "$VENV_PATH" ]; then
    echo "📦 Creando entorno virtual en $VENV_PATH"
    python3 -m venv "$VENV_PATH"
fi

# Activar entorno virtual
source "$VENV_PATH/bin/activate"

# Instalar dependencias
pip install requests
pip install PyYAML

# Ejecutar script de Python con todos los argumentos
echo "🏃 Ejecutando script principal"
eval "python \"$SCRIPT_DIR/main.py\" $PYTHON_ARGS"

# Desactivar entorno virtual
deactivate

#echo "✅ Proceso completado"