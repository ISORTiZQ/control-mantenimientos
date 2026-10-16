"""
Modelos de base de datos con SQLAlchemy
=======================================
Define las tablas para usuarios, solicitudes, historial de estados,
cotizaciones y adjuntos (referencias a archivos, no los archivos en sí).
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Usuarios del sistema."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default="admin", nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"


class Solicitud(db.Model):
    """Solicitudes de mantenimiento (equivalente a las filas del Excel)."""
    __tablename__ = "solicitudes"

    id = db.Column(db.Integer, primary_key=True)
    # Id de Forms / OT — identificador único externo
    forms_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    ot = db.Column(db.String(50), nullable=True, index=True)

    # Datos del formulario
    tienda = db.Column(db.String(200), nullable=True)
    tipo_servicio = db.Column(db.String(200), nullable=True)
    descripcion = db.Column(db.Text, nullable=True)
    prioridad = db.Column(db.String(50), nullable=True)
    co = db.Column(db.String(100), nullable=True)
    ciudad = db.Column(db.String(100), nullable=True)
    concepto = db.Column(db.String(200), nullable=True)
    correo_tienda = db.Column(db.String(200), nullable=True)
    direccion_tienda = db.Column(db.String(500), nullable=True)

    # Datos del formulario de Forms
    email_respondente = db.Column(db.String(200), nullable=True)
    nombre_respondente = db.Column(db.String(200), nullable=True)
    start_time = db.Column(db.DateTime, nullable=True)
    completion_time = db.Column(db.DateTime, nullable=True)

    # Gestión de estados
    estado = db.Column(db.String(50), default="CREADO", nullable=False, index=True)
    fecha_gestion = db.Column(db.DateTime, nullable=True)
    fecha_aprobacion = db.Column(db.DateTime, nullable=True)
    fecha_finalizacion = db.Column(db.DateTime, nullable=True)

    # Cotización
    proveedor = db.Column(db.String(200), nullable=True)
    monto = db.Column(db.Numeric(12, 2), nullable=True)
    pdf_cotizacion = db.Column(db.String(500), nullable=True)

    # Cierre
    comentario_cierre = db.Column(db.Text, nullable=True)

    # Metadatos
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación con adjuntos
    adjuntos = db.relationship("Adjunto", backref="solicitud", lazy=True,
                               cascade="all, delete-orphan")
    historial = db.relationship("HistorialEstado", backref="solicitud", lazy=True,
                                cascade="all, delete-orphan",
                                order_by="HistorialEstado.created_at.desc()")

    def __repr__(self):
        return f"<Solicitud {self.forms_id} - {self.tienda} - {self.estado}>"


class HistorialEstado(db.Model):
    """Historial de cambios de estado de cada solicitud."""
    __tablename__ = "historial_estados"

    id = db.Column(db.Integer, primary_key=True)
    solicitud_id = db.Column(db.Integer, db.ForeignKey("solicitudes.id"), nullable=False, index=True)
    estado_anterior = db.Column(db.String(50), nullable=True)
    estado_nuevo = db.Column(db.String(50), nullable=False)
    usuario = db.Column(db.String(80), nullable=True)
    comentario = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)


class Adjunto(db.Model):
    """
    Referencias a archivos adjuntos (fotos, PDFs).
    NO almacena el archivo en sí, solo su ubicación y metadatos.
    """
    __tablename__ = "adjuntos"

    id = db.Column(db.Integer, primary_key=True)
    solicitud_id = db.Column(db.Integer, db.ForeignKey("solicitudes.id"), nullable=False, index=True)
    tipo = db.Column(db.String(20), nullable=False)  # 'foto' o 'pdf'
    nombre_archivo = db.Column(db.String(255), nullable=False)
    # URL o ruta en almacenamiento privado (S3, disco, etc.)
    url_almacenamiento = db.Column(db.String(1000), nullable=False)
    mime_type = db.Column(db.String(100), nullable=True)
    tamano_bytes = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Tienda(db.Model):
    """
    Catálogo de tiendas (equivalente a Hoja2 del Excel).
    Se usa para enriquecer automáticamente las solicitudes entrantes.
    """
    __tablename__ = "tiendas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(200), nullable=False, index=True)
    co = db.Column(db.String(100), nullable=True)
    ciudad = db.Column(db.String(100), nullable=True)
    concepto = db.Column(db.String(200), nullable=True)
    correo_tienda = db.Column(db.String(200), nullable=True)
    direccion_tienda = db.Column(db.String(500), nullable=True)

    def __repr__(self):
        return f"<Tienda {self.nombre}>"


def init_db(app):
    """Inicializa la base de datos y crea las tablas."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Crear usuario admin por defecto si no existe
        from werkzeug.security import generate_password_hash
        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin)
            db.session.commit()
