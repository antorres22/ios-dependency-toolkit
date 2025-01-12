#!/bin/bash

# Directorio base del script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Valores por defecto
PYTHON_ARGS=""

# Parsear argumentos
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --path|-p) 
            PYTHON_ARGS+=" --path $2"
            shift 2
            ;;
        --cached|-c) 
            PYTHON_ARGS+=" --cached"
            shift
            ;;
        *) 
            PYTHON_ARGS+=" $1"
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

# Ejecutar script de Python con todos los argumentos
echo "🏃 Ejecutando script principal"
python "$SCRIPT_DIR/main.py" $PYTHON_ARGS

# Desactivar entorno virtual
deactivate

echo "✅ Proceso completado"