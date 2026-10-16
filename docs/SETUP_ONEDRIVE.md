# 📖 Guía: Integración con Microsoft Graph API (OneDrive)

Esta guía explica cómo configurar la app para leer el Excel directamente desde OneDrive, generado por Microsoft Forms.

---

## Paso 1: Registrar la aplicación en Azure

1. Ve a [Azure Portal](https://portal.azure.com)
2. Inicia sesión con tu cuenta de Microsoft 365
3. En la barra de búsqueda, escribe **"App registrations"** y selecciónalo
4. Click en **"New registration"**

### Datos del formulario:

| Campo | Valor |
|-------|-------|
| Name | `Excel Reader App` (o el nombre que prefieras) |
| Supported account types | **Accounts in this organizational directory only** |
| Redirect URI | Dejar vacío (no necesitamos interacción del usuario) |

5. Click **"Register"**

---

## Paso 2: Obtener IDs

Una vez registrada, en la página de la app verás:

- **Application (client) ID** → Este es tu `MS_CLIENT_ID`
- **Directory (tenant) ID** → Este es tu `MS_TENANT_ID`

Copia ambos valores.

---

## Paso 3: Crear el Client Secret

1. En el menú izquierdo, click **"Certificates & secrets"**
2. Click **"New client secret"**
3. Descripción: `Excel Reader Secret`
4. Expira: Elige 12 o 24 meses
5. Click **"Add"**
6. **IMPORTANTE:** Copia el **Value** (no el Secret ID) → Este es tu `MS_CLIENT_SECRET`

> ⚠️ El valor solo se muestra una vez. Si no lo copias, tendrás que crear otro.

---

## Paso 4: Dar permisos a la aplicación

1. En el menú izquierdo, click **"API permissions"**
2. Click **"Add a permission"**
3. Selecciona **"Microsoft Graph"**
4. Selecciona **"Application permissions"** (no Delegated)
5. Busca y marca: **`Files.Read.All`**
6. Click **"Add permissions"**

### ⚠️ Importante: Admin consent

7. Verás tus permisos listados. Click **"Grant admin consent for [tu dominio]"**
8. Confirma. El estado debe cambiar a **"Granted"** (check verde)

> Si no eres admin del tenant, necesitas que un admin haga este paso.

---

## Paso 5: Identificar el usuario de OneDrive

El Excel de Forms se guarda en el OneDrive del usuario que creó el formulario.

`MS_DRIVE_USER` = el email de esa persona (UPN)

Ejemplo: `juan.perez@midominio.onmicrosoft.com`

---

## Paso 6: Encontrar la ruta del Excel en OneDrive

El archivo de respuestas de Forms se guarda por defecto en:

```
Documentos/Respuestas de formulario "[nombre del formulario]".xlsx
```

Para confirmar la ruta exacta:

1. Ve a [OneDrive Online](https://onedrive.live.com)
2. Navega a la carpeta donde está el archivo
3. La ruta relativa desde la raíz de OneDrive es el valor de `MS_EXCEL_PATH`

Ejemplos:
- `Documentos/Respuestas de formulario "Solicitudes de mantenimiento".xlsx`
- `Apps/Forms/Respuestas de formulario.xlsx`

---

## Paso 7: Configurar el archivo .env

Crea un archivo `.env` en la raíz del proyecto (copia de `.env.example`):

```env
SECRET_KEY=una-clave-muy-secreta-y-aleatoria

EXCEL_SOURCE=auto

MS_TENANT_ID=11111111-2222-3333-4444-555555555555
MS_CLIENT_ID=aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee
MS_CLIENT_SECRET=tu-client-secret-value
MS_DRIVE_USER=juan.perez@midominio.onmicrosoft.com
MS_EXCEL_PATH=Documentos/Respuestas de formulario "Solicitudes".xlsx
```

---

## Paso 8: Probar

1. Instala las nuevas dependencias:
   ```bash
   pip install -r requirements.txt
   ```

2. Reinicia la app:
   ```bash
   python app.py
   ```

3. Inicia sesión y ve a la home. Los datos deberían cargarse desde OneDrive.

4. Verifica el estado de la fuente:
   ```
   GET http://localhost:5000/api/status
   ```
   Debe responder:
   ```json
   {"onedrive_configured": true, "local_file": "datos.xlsx", "source": "auto"}
   ```

---

## Modos de operación

| `EXCEL_SOURCE` | Comportamiento |
|----------------|---------------|
| `auto` (default) | Intenta OneDrive primero. Si falla, usa archivo local. |
| `onedrive` | Solo OneDrive. Error si no disponible. |
| `local` | Solo archivo local. Ignora OneDrive. |

---

## Troubleshooting

### Error: "Error al obtener token de Graph API: 401"
- Verifica que `MS_TENANT_ID`, `MS_CLIENT_ID` y `MS_CLIENT_SECRET` sean correctos
- El client secret puede haber expirado

### Error: "Error al obtener drive del usuario: 404"
- El `MS_DRIVE_USER` no es correcto o el usuario no existe
- Verifica que sea el UPN (email) del usuario correcto

### Error: "Error al descargar Excel: 404"
- La ruta `MS_EXCEL_PATH` no es correcta
- Verifica la ruta exacta en OneDrive Online

### Error: "Insufficient privileges"
- Falta el admin consent en API permissions
- Ve a Azure > API permissions > "Grant admin consent"

### El archivo está abierto en Excel desktop
- Graph API puede leerlo sin problema (no bloquea como el acceso local)

---

## Seguridad

- **Nunca** subas el `.env` a git (ya está en `.gitignore`)
- En producción, configura las variables de entorno en el panel de tu hosting
- El `client_secret` es sensible: trátalo como una contraseña
- Los permisos `Files.Read.All` dan acceso a TODOS los archivos del tenant. Para más seguridad, usa permisos delegados con consent del usuario.
