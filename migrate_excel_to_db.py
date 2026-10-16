"""
Script de migración: Excel → PostgreSQL/SQLite
==============================================
Lee el archivo data/datos.xlsx e importa todos los registros a la base de datos.
Conserva los OT, estados, fechas y datos históricos.

Uso:
    python migrate_excel_to_db.py
"""

import os
import sys
from datetime import datetime

import pandas as pd
from werkzeug.security import generate_password_hash

# Asegurar que el directorio del proyecto está en el path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from database import db, User, Solicitud, HistorialEstado, Adjunto


def parse_datetime(val):
    """Intenta convertir un valor a datetime, devuelve None si no puede."""
    if val is None or val == "" or str(val) == "nan" or str(val) == "NaT":
        return None
    if isinstance(val, datetime):
        return val
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d",
                "%d/%m/%Y %H:%M", "%d/%m/%Y"]:
        try:
            return datetime.strptime(str(val), fmt)
        except ValueError:
            continue
    try:
        return pd.to_datetime(val)
    except Exception:
        return None


def clean_str(val):
    """Limpia un valor para string: None si vacío/nan."""
    if val is None:
        return None
    s = str(val).strip()
    if s in ("", "nan", "NaT", "None"):
        return None
    return s


def find_excel_file():
    """Busca el archivo Excel."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(base_dir, "data", "datos.xlsx")
    if os.path.exists(excel_file):
        return excel_file
    # Buscar cualquier .xlsx en data/
    import glob
    xlsx = glob.glob(os.path.join(base_dir, "data", "*.xlsx"))
    xlsx = [f for f in xlsx if not os.path.basename(f).startswith("~$")]
    if xlsx:
        return xlsx[0]
    return None


def migrate():
    """Ejecuta la migración."""
    filepath = find_excel_file()
    if not filepath:
        print("ERROR: No se encontró el archivo Excel en data/")
        sys.exit(1)

    print(f"Leyendo Excel: {filepath}")

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

    df = pd.read_excel(filepath, engine=engine) if engine else pd.read_excel(filepath)
    df.columns = [str(c).strip() for c in df.columns]

    print(f"Registros en Excel: {len(df)}")
    print(f"Columnas: {list(df.columns)}")

    # Mapeo de columnas
    def get_col(candidates):
        for c in candidates:
            if c in df.columns:
                return c
        return None

    col_id = get_col(["Id", "ID", "id", "OT", "ot"])
    col_start = get_col(["Start time", "start_time", "Start Time"])
    col_completion = get_col(["Completion time", "completion_time", "Completion Time"])
    col_email = get_col(["Email", "email"])
    col_name = get_col(["Name", "name", "Nombre"])
    col_tienda = get_col(["TIENDA", "Tienda", "tienda"])
    col_servicio = get_col(["TIPO DE SERVICIO", "Tipo de servicio", "Tipo de Servicio"])
    col_desc = get_col(["DESCRIPCIÓN", "Descripcion", "DESCRIPCION", "Descripción"])
    col_prioridad = get_col(["PRIORIDAD", "Prioridad"])
    col_evidencia = get_col(["EVIDENCIA FOTOGRAFICA", "Evidencia Fotografica",
                             "Evidencia Fotográfica", "EVIDENCIA FOTOGRÁFICA"])
    col_co = get_col(["CO", "co", "Co"])
    col_ciudad = get_col(["CIUDAD", "Ciudad", "ciudad"])
    col_concepto = get_col(["CONCEPTO", "Concepto", "concepto"])
    col_correo_tienda = get_col(["CORREO TIENDA", "Correo Tienda", "correo tienda"])
    col_direccion = get_col(["DIRECCION TIENDA", "Direccion Tienda",
                             "DIRECCIÓN TIENDA", "Dirección Tienda"])
    col_estado = get_col(["ESTADO", "Estado", "estado", "Status"])
    col_fecha_gestion = get_col(["FECHA_GESTION", "Fecha Gestion", "fecha_gestion"])
    col_proveedor = get_col(["PROVEEDOR", "Proveedor", "proveedor"])
    col_fecha_aprob = get_col(["FECHA_APROBACION", "Fecha Aprobacion", "fecha_aprobacion"])
    col_monto = get_col(["MONTO", "Monto", "monto"])
    col_pdf = get_col(["PDF_COTIZACION", "Pdf Cotizacion", "pdf_cotizacion"])
    col_comentario = get_col(["COMENTARIO_CIERRE", "Comentario Cierre", "comentario_cierre"])
    col_fecha_fin = get_col(["FECHA_FINALIZACION", "Fecha Finalizacion", "fecha_finalizacion"])

    with app.app_context():
        # Crear tablas
        db.create_all()

        # Crear usuario admin si no existe
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
            print("Usuario admin creado.")
        else:
            print("Usuario admin ya existe.")

        # Importar solicitudes
        importados = 0
        actualizados = 0
        saltados = 0

        for idx, row in df.iterrows():
            forms_id = clean_str(row[col_id]) if col_id else None
            if not forms_id:
                saltados += 1
                continue

            # Buscar si ya existe
            existing = Solicitud.query.filter_by(forms_id=forms_id).first()

            # Construir objeto de datos
            data = {
                "forms_id": forms_id,
                "ot": forms_id,
                "tienda": clean_str(row[col_tienda]) if col_tienda else None,
                "tipo_servicio": clean_str(row[col_servicio]) if col_servicio else None,
                "descripcion": clean_str(row[col_desc]) if col_desc else None,
                "prioridad": clean_str(row[col_prioridad]) if col_prioridad else None,
                "co": clean_str(row[col_co]) if col_co else None,
                "ciudad": clean_str(row[col_ciudad]) if col_ciudad else None,
                "concepto": clean_str(row[col_concepto]) if col_concepto else None,
                "correo_tienda": clean_str(row[col_correo_tienda]) if col_correo_tienda else None,
                "direccion_tienda": clean_str(row[col_direccion]) if col_direccion else None,
                "email_respondente": clean_str(row[col_email]) if col_email else None,
                "nombre_respondente": clean_str(row[col_name]) if col_name else None,
                "start_time": parse_datetime(row[col_start]) if col_start else None,
                "completion_time": parse_datetime(row[col_completion]) if col_completion else None,
                "estado": clean_str(row[col_estado]) if col_estado else "CREADO",
                "fecha_gestion": parse_datetime(row[col_fecha_gestion]) if col_fecha_gestion else None,
                "fecha_aprobacion": parse_datetime(row[col_fecha_aprob]) if col_fecha_aprob else None,
                "fecha_finalizacion": parse_datetime(row[col_fecha_fin]) if col_fecha_fin else None,
                "proveedor": clean_str(row[col_proveedor]) if col_proveedor else None,
                "pdf_cotizacion": clean_str(row[col_pdf]) if col_pdf else None,
                "comentario_cierre": clean_str(row[col_comentario]) if col_comentario else None,
            }

            # Monto numérico
            if col_monto:
                monto_val = row[col_monto]
                if monto_val is not None and str(monto_val) not in ("", "nan", "None"):
                    try:
                        data["monto"] = float(str(monto_val).replace(",", "").replace("$", ""))
                    except (ValueError, TypeError):
                        data["monto"] = None
                else:
                    data["monto"] = None

            # URL de evidencia como adjunto
            evidencia_url = clean_str(row[col_evidencia]) if col_evidencia else None

            if existing:
                # Actualizar registro existente
                for key, value in data.items():
                    setattr(existing, key, value)
                actualizados += 1
                solicitud = existing
            else:
                # Crear nuevo
                solicitud = Solicitud(**data)
                db.session.add(solicitud)
                db.session.flush()  # Obtener ID
                importados += 1

            # Agregar adjunto de evidencia si existe
            if evidencia_url:
                # Verificar si ya existe el adjunto
                adj_exist = Adjunto.query.filter_by(
                    solicitud_id=solicitud.id,
                    url_almacenamiento=evidencia_url
                ).first()
                if not adj_exist:
                    adj = Adjunto(
                        solicitud_id=solicitud.id,
                        tipo="foto",
                        nombre_archivo="evidencia",
                        url_almacenamiento=evidencia_url,
                    )
                    db.session.add(adj)

        db.session.commit()

        print(f"\n--- Migración completada ---")
        print(f"Importados: {importados}")
        print(f"Actualizados: {actualizados}")
        print(f"Saltados (sin ID): {saltados}")

        total = Solicitud.query.count()
        print(f"Total de solicitudes en BD: {total}")

        # Mostrar resumen por estado
        from sqlalchemy import func
        estados = db.session.query(Solicitud.estado, func.count(Solicitud.id))\
            .group_by(Solicitud.estado).all()
        print("\nDistribución por estado:")
        for estado, count in estados:
            print(f"  {estado}: {count}")


if __name__ == "__main__":
    migrate()
