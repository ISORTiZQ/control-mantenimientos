#!/bin/bash
# ============================================
# Script de inicio para Linux/Mac
# ============================================
set -e

echo ""
echo "============================================"
echo "  Panel de Control - Visualizador de Excel"
echo "============================================"
echo ""

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 no está instalado."
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "[1/4] Creando entorno virtual..."
    python3 -m venv venv
fi

# Activar entorno virtual
source venv/bin/activate

# Instalar dependencias
echo "[2/4] Instalando dependencias..."
pip install -r requirements.txt -q

# Configurar Excel
echo "[3/4] Configurando Excel..."
python setup_excel.py

# Si no hay Excel, generar ejemplo
if [ ! -f "data/datos.xlsx" ]; then
    echo "      Generando Excel de ejemplo..."
    python generate_sample_excel.py
fi

# Iniciar
echo "[4/4] Iniciando aplicación..."
echo ""
echo "   URL: http://localhost:5000"
echo "   Usuario: admin"
echo "   Contraseña: admin123"
echo ""
python app.py
