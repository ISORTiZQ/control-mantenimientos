"""
Aplicación Web - Gestión de Solicitudes de Mantenimiento
========================================================
Aplicación Flask con base de datos PostgreSQL (o SQLite en desarrollo).
Maneja solicitudes de mantenimiento, estados, cotizaciones y cierre.

Usuario por defecto: admin
Contraseña por defecto: admin123
"""

import os
import logging
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect,
    url_for, session, flash, jsonify
)
from werkzeug.security import generate_password_hash, check_password_hash

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from database import db, init_db, User, Solicitud, HistorialEstado, Adjunto, Tienda

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get(
    "SECRET_KEY", "sk-xyz989gbc155def450"
)
app.jinja_env.auto_reload = True
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0

# Configuración de base de datos
# En desarrollo: SQLite local
# En producción: PostgreSQL vía DATABASE_URL
database_url = os.environ.get("DATABASE_URL", "")
if database_url:
    # PostgreSQL: usar psycopg3 como driver
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # SQLite local para desarrollo
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mantenimiento.db"

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Inicializar DB
init_db(app)


@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response


# ---------------------------------------------------------------------------
# Decoradores
# ---------------------------------------------------------------------------

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user" not in session:
            flash("Por favor inicia sesión para continuar.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------------------------------------------------------------------
# Helpers de datos
# ---------------------------------------------------------------------------

def get_all_solicitudes():
    """
    Obtiene todas las solicitudes de la BD y las devuelve en formato
    compatible con las plantillas (dicts como los del Excel).
    """
    solicitudes = Solicitud.query.order_by(Solicitud.id).all()

    records = []
    all_records = []

    for s in solicitudes:
        # Record simplificado para la tabla (OT, Tienda, Tipo de servicio, Estado)
        record = {
            "OT": s.ot or s.forms_id,
            "Tienda": s.tienda or "",
            "Tipo de servicio": s.tipo_servicio or "",
            "Estado": s.estado or "CREADO",
        }
        records.append(record)

        # Record completo para el modal de detalle
        full = {
            "Id": s.forms_id,
            "OT": s.ot or s.forms_id,
            "TIENDA": s.tienda or "",
            "TIPO DE SERVICIO": s.tipo_servicio or "",
            "DESCRIPCIÓN": s.descripcion or "",
            "PRIORIDAD": s.prioridad or "",
            "CO": s.co or "",
            "CIUDAD": s.ciudad or "",
            "CONCEPTO": s.concepto or "",
            "CORREO TIENDA": s.correo_tienda or "",
            "DIRECCION TIENDA": s.direccion_tienda or "",
            "Email": s.email_respondente or "",
            "Name": s.nombre_respondente or "",
            "ESTADO": s.estado or "CREADO",
            "FECHA_GESTION": s.fecha_gestion.strftime("%Y-%m-%d %H:%M:%S") if s.fecha_gestion else "",
            "PROVEEDOR": s.proveedor or "",
            "FECHA_APROBACION": s.fecha_aprobacion.strftime("%Y-%m-%d") if s.fecha_aprobacion else "",
            "MONTO": str(int(s.monto)) if s.monto else "",
            "PDF_COTIZACION": s.pdf_cotizacion or "",
            "COMENTARIO_CIERRE": s.comentario_cierre or "",
            "FECHA_FINALIZACION": s.fecha_finalizacion.strftime("%Y-%m-%d %H:%M:%S") if s.fecha_finalizacion else "",
            "EVIDENCIA FOTOGRAFICA": "",
        }

        # Buscar adjunto de evidencia
        adjunto_foto = Adjunto.query.filter_by(solicitud_id=s.id, tipo="foto").first()
        if adjunto_foto:
            full["EVIDENCIA FOTOGRAFICA"] = adjunto_foto.url_almacenamiento

        all_records.append(full)

    return records, all_records


def get_db_last_modified():
    """Devuelve la fecha de última modificación de la BD."""
    try:
        last = db.session.query(db.func.max(Solicitud.updated_at)).scalar()
        if last:
            return last.strftime("%d/%m/%Y %H:%M")
    except Exception:
        pass
    return "—"


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    if "user" in session:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        user = User.query.filter_by(username=username, active=True).first()
        if user and check_password_hash(user.password_hash, password):
            session["user"] = username
            flash(f"¡Bienvenido, {username}!", "success")
            return redirect(url_for("home"))
        else:
            flash("Usuario o contraseña incorrectos.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("login"))


@app.route("/home")
@login_required
def home():
    records, all_records = get_all_solicitudes()
    columns = ["OT", "Tienda", "Tipo de servicio", "Estado"]
    last_modified = get_db_last_modified()

    return render_template(
        "home.html",
        user=session.get("user"),
        records=records,
        columns=columns,
        error=None,
        all_records=all_records,
        last_modified=last_modified,
    )


@app.route("/dashboard")
@login_required
def dashboard():
    records, all_records = get_all_solicitudes()
    last_modified = get_db_last_modified()

    return render_template(
        "dashboard.html",
        user=session.get("user"),
        error=None,
        all_records=all_records,
        last_modified=last_modified,
    )


@app.route("/api/data")
@login_required
def api_data():
    records, all_records = get_all_solicitudes()
    columns = ["OT", "Tienda", "Tipo de servicio", "Estado"]
    return jsonify({"columns": columns, "data": records, "all_data": all_records})


@app.route("/api/update_state", methods=["POST"])
@login_required
def api_update_state():
    """Actualiza el estado de una solicitud."""
    data = request.get_json()
    ot_id = data.get("ot_id")
    new_state = data.get("state", "EN PROCESO DE COTIZACION")

    if not ot_id:
        return jsonify({"error": "Falta el ID de la orden"}), 400

    solicitud = Solicitud.query.filter_by(forms_id=str(ot_id)).first()
    if not solicitud:
        return jsonify({"error": f"No se encontró la orden con ID {ot_id}"}), 404

    estado_anterior = solicitud.estado
    solicitud.estado = new_state

    if "COTIZACION" in new_state.upper():
        solicitud.fecha_gestion = datetime.utcnow()

    # Registrar en historial
    historial = HistorialEstado(
        solicitud_id=solicitud.id,
        estado_anterior=estado_anterior,
        estado_nuevo=new_state,
        usuario=session.get("user"),
    )
    db.session.add(historial)
    db.session.commit()

    logger.info(f"Estado actualizado: OT {ot_id} -> {new_state}")
    return jsonify({"success": True, "ot_id": ot_id, "new_state": new_state})


@app.route("/api/aprobar", methods=["POST"])
@login_required
def api_aprobar():
    """Aprueba una cotización y guarda los datos."""
    data = request.get_json()
    ot_id = data.get("ot_id")
    proveedor = data.get("proveedor", "")
    fecha_aprobacion = data.get("fecha_aprobacion", "")
    monto = data.get("monto", 0)
    pdf_nombre = data.get("pdf_nombre", "")

    if not ot_id:
        return jsonify({"error": "Falta el ID de la orden"}), 400

    solicitud = Solicitud.query.filter_by(forms_id=str(ot_id)).first()
    if not solicitud:
        return jsonify({"error": f"No se encontró la orden con ID {ot_id}"}), 404

    estado_anterior = solicitud.estado
    solicitud.estado = "EN EJECUCION"
    solicitud.proveedor = proveedor or None
    solicitud.monto = float(monto) if monto else None
    solicitud.pdf_cotizacion = pdf_nombre or None

    if fecha_aprobacion:
        try:
            solicitud.fecha_aprobacion = datetime.strptime(fecha_aprobacion, "%Y-%m-%d")
        except ValueError:
            solicitud.fecha_aprobacion = datetime.utcnow()
    else:
        solicitud.fecha_aprobacion = datetime.utcnow()

    historial = HistorialEstado(
        solicitud_id=solicitud.id,
        estado_anterior=estado_anterior,
        estado_nuevo="EN EJECUCION",
        usuario=session.get("user"),
        comentario=f"Proveedor: {proveedor}, Monto: {monto}",
    )
    db.session.add(historial)
    db.session.commit()

    logger.info(f"Cotización aprobada: OT {ot_id} - Proveedor: {proveedor} - Monto: {monto}")
    return jsonify({
        "success": True,
        "ot_id": ot_id,
        "proveedor": proveedor,
        "monto": monto
    })


@app.route("/api/finalizar", methods=["POST"])
@login_required
def api_finalizar():
    """Finaliza un caso y guarda el comentario de cierre."""
    data = request.get_json()
    ot_id = data.get("ot_id")
    comentario = data.get("comentario", "")

    if not ot_id:
        return jsonify({"error": "Falta el ID de la orden"}), 400

    solicitud = Solicitud.query.filter_by(forms_id=str(ot_id)).first()
    if not solicitud:
        return jsonify({"error": f"No se encontró la orden con ID {ot_id}"}), 404

    estado_anterior = solicitud.estado
    solicitud.estado = "FINALIZADO"
    solicitud.comentario_cierre = comentario or None
    solicitud.fecha_finalizacion = datetime.utcnow()

    historial = HistorialEstado(
        solicitud_id=solicitud.id,
        estado_anterior=estado_anterior,
        estado_nuevo="FINALIZADO",
        usuario=session.get("user"),
        comentario=comentario,
    )
    db.session.add(historial)
    db.session.commit()

    logger.info(f"Caso finalizado: OT {ot_id}")
    return jsonify({"success": True, "ot_id": ot_id})


@app.route("/api/status")
@login_required
def api_status():
    """Devuelve el estado de la configuración de fuentes de datos."""
    db_url = os.environ.get("DATABASE_URL", "")
    return jsonify({
        "database": "PostgreSQL" if db_url else "SQLite (desarrollo)",
        "source": "database",
        "total_solicitudes": Solicitud.query.count(),
    })


# ---------------------------------------------------------------------------
# Endpoint para recibir datos de Power Automate (futuro)
# ---------------------------------------------------------------------------

@app.route("/api/ingest", methods=["POST"])
def api_ingest():
    """
    Endpoint para recibir respuestas de Microsoft Forms vía Power Automate.
    Autenticación por token compartido en header X-Webhook-Token.
    """
    # Validar token
    webhook_token = os.environ.get("WEBHOOK_TOKEN", "")
    if not webhook_token:
        return jsonify({"error": "Endpoint no configurado"}), 503

    received_token = request.headers.get("X-Webhook-Token", "")
    if received_token != webhook_token:
        return jsonify({"error": "No autorizado"}), 401

    data = request.get_json()
    if not data:
        return jsonify({"error": "No se recibieron datos"}), 400

    forms_id = data.get("forms_id") or data.get("Id") or data.get("id")
    if not forms_id:
        return jsonify({"error": "Falta el ID de la respuesta"}), 400

    # Evitar duplicados
    existing = Solicitud.query.filter_by(forms_id=str(forms_id)).first()
    if existing:
        return jsonify({"success": True, "message": "Ya existe", "ot_id": forms_id}), 200

    # Crear nueva solicitud
    solicitud = Solicitud(
        forms_id=str(forms_id),
        ot=str(forms_id),
        tienda=data.get("tienda"),
        tipo_servicio=data.get("tipo_servicio"),
        descripcion=data.get("descripcion"),
        prioridad=data.get("prioridad"),
        co=data.get("co"),
        ciudad=data.get("ciudad"),
        concepto=data.get("concepto"),
        correo_tienda=data.get("correo_tienda"),
        direccion_tienda=data.get("direccion_tienda"),
        email_respondente=data.get("email"),
        nombre_respondente=data.get("name"),
        estado="CREADO",
    )

    # ---------------------------------------------------------------
    # Enriquecimiento automático desde catálogo de tiendas
    # ---------------------------------------------------------------
    tienda_nombre = data.get("tienda")
    if tienda_nombre:
        # Buscar por nombre exacto primero, luego por coincidencia parcial
        tienda_cat = Tienda.query.filter_by(nombre=tienda_nombre.strip()).first()
        if not tienda_cat:
            # Búsqueda flexible: ignorar espacios extra
            tienda_cat = Tienda.query.filter(
                db.func.trim(Tienda.nombre) == db.func.trim(tienda_nombre)
            ).first()

        if tienda_cat:
            # Completar campos solo si vienen vacíos desde Forms
            if not solicitud.co:
                solicitud.co = tienda_cat.co
            if not solicitud.ciudad:
                solicitud.ciudad = tienda_cat.ciudad
            if not solicitud.concepto:
                solicitud.concepto = tienda_cat.concepto
            if not solicitud.correo_tienda:
                solicitud.correo_tienda = tienda_cat.correo_tienda
            if not solicitud.direccion_tienda:
                solicitud.direccion_tienda = tienda_cat.direccion_tienda
            logger.info(f"Tienda enriquecida desde catálogo: {tienda_nombre}")
        else:
            logger.warning(f"Tienda no encontrada en catálogo: {tienda_nombre}")

    # Fechas
    start_time = data.get("start_time")
    if start_time:
        try:
            solicitud.start_time = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

    completion_time = data.get("completion_time")
    if completion_time:
        try:
            solicitud.completion_time = datetime.fromisoformat(completion_time.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            pass

    db.session.add(solicitud)
    db.session.flush()

    # Guardar URL de evidencia como adjunto
    evidencia_url = data.get("evidencia_url") or data.get("evidencia_fotografica")
    if evidencia_url:
        adjunto = Adjunto(
            solicitud_id=solicitud.id,
            tipo="foto",
            nombre_archivo="evidencia",
            url_almacenamiento=evidencia_url,
        )
        db.session.add(adjunto)

    db.session.commit()

    logger.info(f"Nueva solicitud recibida vía webhook: {forms_id}")
    return jsonify({"success": True, "ot_id": forms_id}), 201


# ---------------------------------------------------------------------------
# Arranque
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
