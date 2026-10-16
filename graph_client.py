"""
Cliente de Microsoft Graph API para leer Excel desde OneDrive.
=================================================================

Este módulo se conecta a OneDrive/SharePoint mediante Microsoft Graph API
y descarga el archivo Excel generado por Microsoft Forms.

Requisitos:
  1. Registrar una app en Azure AD (Entra ID)
  2. Otener: client_id, client_secret, tenant_id
  3. Dar permisos Files.Read.All (delegated) a la app
  4. Configurar las variables de entorno en .env
"""

import os
import io
import tempfile
import logging

import requests
import pandas as pd

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuración desde variables de entorno
# ---------------------------------------------------------------------------
GRAPH_BASE_URL = "https://graph.microsoft.com/v1.0"
AUTH_URL = "https://login.microsoftonline.com"

TENANT_ID = os.environ.get("MS_TENANT_ID", "")
CLIENT_ID = os.environ.get("MS_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("MS_CLIENT_SECRET", "")

# ID del usuario de OneDrive donde está el Excel (su email o UPN)
DRIVE_USER = os.environ.get("MS_DRIVE_USER", "")

# Ruta relativa del archivo Excel en OneDrive
# Ej: "Documentos/Respuestas de formulario.xlsx"
EXCEL_PATH = os.environ.get("MS_EXCEL_PATH", "Documentos/Respuestas de formulario.xlsx")


class GraphExcelClient:
    """Cliente para leer Excel desde OneDrive vía Microsoft Graph API."""

    def __init__(self, tenant_id=None, client_id=None, client_secret=None,
                 drive_user=None, excel_path=None):
        self.tenant_id = tenant_id or TENANT_ID
        self.client_id = client_id or CLIENT_ID
        self.client_secret = client_secret or CLIENT_SECRET
        self.drive_user = drive_user or DRIVE_USER
        self.excel_path = excel_path or EXCEL_PATH
        self._access_token = None

    # -----------------------------------------------------------------------
    # Autenticación
    # -----------------------------------------------------------------------
    def is_configured(self):
        """Verifica si todos los parámetros necesarios están configurados."""
        return all([
            self.tenant_id,
            self.client_id,
            self.client_secret,
            self.drive_user,
        ])

    def get_access_token(self):
        """Obtiene un access token usando client_credentials flow."""
        if self._access_token:
            return self._access_token

        url = f"{AUTH_URL}/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }

        resp = requests.post(url, data=data, timeout=30)
        if resp.status_code != 200:
            raise Exception(
                f"Error al obtener token de Graph API: {resp.status_code} - {resp.text}"
            )

        self._access_token = resp.json()["access_token"]
        return self._access_token

    # -----------------------------------------------------------------------
    # Descargar Excel
    # -----------------------------------------------------------------------
    def download_excel(self, save_path=None):
        """
        Descarga el archivo Excel desde OneDrive.

        Args:
            save_path: Ruta donde guardar el archivo. Si es None, usa un temp file.

        Returns:
            Ruta al archivo descargado.
        """
        token = self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}

        # Obtener el drive (OneDrive) del usuario
        drive_url = (
            f"{GRAPH_BASE_URL}/users/{self.drive_user}/drive"
        )
        resp = requests.get(drive_url, headers=headers, timeout=30)
        if resp.status_code != 200:
            raise Exception(
                f"Error al obtener drive del usuario '{self.drive_user}': "
                f"{resp.status_code} - {resp.text}"
            )
        drive_id = resp.json()["id"]

        # Descargar el archivo por ruta
        # Codificar la ruta para la URL
        from urllib.parse import quote
        encoded_path = quote(self.excel_path)
        download_url = (
            f"{GRAPH_BASE_URL}/drives/{drive_id}"
            f"/root:/{encoded_path}:/content"
        )

        resp = requests.get(download_url, headers=headers, timeout=60)
        if resp.status_code != 200:
            raise Exception(
                f"Error al descargar Excel '{self.excel_path}': "
                f"{resp.status_code} - {resp.text}"
            )

        # Guardar el archivo
        if save_path is None:
            fd, save_path = tempfile.mkstemp(suffix=".xlsx")
            os.close(fd)

        with open(save_path, "wb") as f:
            f.write(resp.content)

        logger.info(f"Excel descargado desde OneDrive: {save_path}")
        return save_path

    # -----------------------------------------------------------------------
    # Leer datos
    # -----------------------------------------------------------------------
    def read_excel_data(self, column_mapping):
        """
        Descarga el Excel desde OneDrive y lee las columnas solicitadas.

        Args:
            column_mapping: Dict con el mapeo de columnas a buscar.
                           Ej: {"OT": ["OT", "N° OT"], ...}

        Returns:
            (records, display_names, error)
        """
        if not self.is_configured():
            return [], [], None  # No configurado, no es un error

        try:
            filepath = self.download_excel()

            # Detectar formato
            with open(filepath, "rb") as f:
                magic = f.read(4)
            if magic == b"\xd0\xcf\x11\xe0":
                try:
                    import xlrd
                    engine = "xlrd"
                except ImportError:
                    engine = None
            else:
                engine = "openpyxl"

            if engine:
                df = pd.read_excel(filepath, engine=engine)
            else:
                df = pd.read_excel(filepath)

            df.columns = [str(c).strip() for c in df.columns]

            # Resolver columnas
            resolved = {}
            df_cols_normalized = {str(c).strip(): c for c in df.columns}
            for display_name, candidates in column_mapping.items():
                for candidate in candidates:
                    if candidate in df_cols_normalized:
                        resolved[display_name] = df_cols_normalized[candidate]
                        break

            if not resolved:
                return [], [], f"El Excel de OneDrive no contiene columnas reconocibles. Columnas: {list(df.columns)}"

            display_names = list(resolved.keys())
            source_cols = [resolved[name] for name in display_names]
            df_selected = df[source_cols].copy()
            df_selected.columns = display_names
            df_selected = df_selected.fillna("")

            records = df_selected.to_dict(orient="records")

            # Limpiar temp file
            try:
                os.unlink(filepath)
            except OSError:
                pass

            return records, display_names, None

        except Exception as exc:
            logger.error(f"Error leyendo Excel desde OneDrive: {exc}")
            return [], [], f"Error OneDrive: {exc}"
