@echo off
REM ============================================
REM Script de inicio para Windows
REM ============================================
echo.
echo ============================================
echo   Panel de Control - Visualizador de Excel
echo ============================================
echo.

REM Verificar si Python esta disponible
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo.
    echo Opciones:
    echo   1. Instalar Python desde: https://www.python.org/downloads/
    echo   2. Asegurar que "Add Python to PATH" este marcado durante la instalacion.
    echo.
    pause
    exit /b 1
)

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo [1/4] Creando entorno virtual...
    python -m venv venv
)

REM Activar entorno virtual
call venv\Scripts\activate

REM Instalar dependencias
echo [2/4] Instalando dependencias...
pip install -r requirements.txt -q

REM Copiar Excel si existe
echo [3/4] Configurando Excel...
python setup_excel.py

REM Si no hay Excel, generar uno de ejemplo
python -c "import os; exit(0 if os.path.exists('data/datos.xlsx') else 1)"
if %errorlevel% neq 0 (
    echo       Generando Excel de ejemplo...
    python generate_sample_excel.py
)

REM Iniciar aplicacion
echo [4/4] Iniciando aplicacion...
echo.
echo    URL: http://localhost:5000
echo    Usuario: admin
echo    Contrasena: admin123
echo.
python app.py

pause
