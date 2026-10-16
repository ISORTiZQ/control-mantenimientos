# 📊 Panel de Control - Visualizador de Excel

Aplicación web en Python (Flask) que lee un archivo Excel y muestra columnas específicas (**OT**, **Tienda**, **Tipo de servicio**) en una página web con login.

## ✨ Características

- 🔐 **Login** con usuario y contraseña
- 🏠 **Página Home** con tabla renderizada desde Excel
- 📋 Muestra solo columnas: **OT**, **Tienda**, **Tipo de servicio**
- 🔍 Búsqueda en tiempo real
- 📊 Tarjetas de estadísticas (total registros, tiendas únicas, tipos de servicio)
- 🔄 Botón de actualización (recarga datos del Excel)
- ☁️ **Integración con Microsoft Graph API** (lee Excel desde OneDrive)
- 📱 Diseño responsive con Bootstrap 5
- 🎨 UI moderna con gradientes e iconos

## 🚀 Instalación

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Generar Excel de ejemplo

```bash
python generate_sample_excel.py
```

Esto crea `data/datos.xlsx` con 25 registros de prueba.

### 3. Ejecutar la aplicación

```bash
python app.py
```

### 4. Abrir en el navegador

```
http://localhost:5000
```

## 🔑 Credenciales

Las credenciales se configuran mediante variables de entorno. En producción, define `SECRET_KEY` y la base de datos con `DATABASE_URL`.

## 📁 Estructura del Proyecto

```
APP/
├── app.py                      # Aplicación principal Flask
├── graph_client.py             # Cliente Microsoft Graph API (OneDrive)
├── generate_sample_excel.py    # Genera Excel de ejemplo
├── setup_excel.py              # Detecta y copia Excel existente
├── requirements.txt            # Dependencias
├── .env.example                # Template de configuración
├── data/
│   └── datos.xlsx              # Archivo Excel local (fallback)
├── docs/
│   └── SETUP_ONEDRIVE.md       # Guía de configuración OneDrive
├── static/
│   ├── css/
│   │   └── style.css           # Estilos personalizados
│   └── js/
│       └── main.js             # JavaScript general
└── templates/
    ├── base.html               # Template base
    ├── login.html              # Página de login
    └── home.html               # Página home con tabla
```

## ☁️ Integración OneDrive (Microsoft Graph API)

La app puede leer el Excel directamente desde OneDrive, ideal para formularios de Microsoft Forms.

### Configuración rápida

1. Copia `.env.example` a `.env`
2. Sigue la guía detallada en [`docs/SETUP_ONEDRIVE.md`](docs/SETUP_ONEDRIVE.md)
3. Configura tus credenciales de Azure en `.env`
4. Reinicia la app

### Modos de operación

| `EXCEL_SOURCE` | Comportamiento |
|----------------|---------------|
| `auto` (default) | OneDrive primero, fallback a local |
| `onedrive` | Solo OneDrive |
| `local` | Solo archivo local |

## 📄 Formato del Excel

El archivo Excel debe tener al menos estas columnas (los nombres exactos):

| OT       | Tienda         | Tipo de servicio |
|----------|----------------|-----------------|
| OT-1001  | Tienda Centro  | Instalación     |
| OT-1002  | Tienda Norte   | Mantenimiento   |

> El Excel puede tener columnas adicionales; solo se mostrarán las tres indicadas.

## 🌐 Despliegue

### Opción 1: Render.com

1. Sube el repo a GitHub
2. Crea un nuevo servicio en [Render](https://render.com)
3. Configura:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python app.py` o `gunicorn app:app`
   - Agrega `gunicorn` a `requirements.txt` para producción

### Opción 2: Railway

1. Sube el repo a GitHub
2. Importa en [Railway](https://railway.app)
3. Railway detecta Flask automáticamente

### Opción 3: PythonAnywhere

1. Sube los archivos a [PythonAnywhere](https://www.pythonanywhere.com)
2. Crea una web app con Flask
3. Configura el path de `app.py`

### Opción 4: VPS / Docker

```bash
# Con Gunicorn (producción)
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## ⚙️ Configuración

- **Archivo Excel:** Coloca tu archivo en `data/datos.xlsx`
- **Clave secreta:** Configura la variable de entorno `SECRET_KEY`
- **Puerto:** Configura la variable de entorno `PORT` (default: 5000)
- **Usuario/contraseña:** Edita el diccionario `USERS` en `app.py`

## 🛠️ Tecnologías

- **Python 3.10+**
- **Flask 3.0** - Framework web
- **Pandas** - Lectura del Excel
- **openpyxl** - Motor de lectura .xlsx
- **Bootstrap 5.3** - UI responsive
- **Bootstrap Icons** - Iconografía
