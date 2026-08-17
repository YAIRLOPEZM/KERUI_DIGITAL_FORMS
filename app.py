from flask import Flask, render_template, request, send_file, abort, url_for
import os
import base64
from datetime import date

from pdf_generator import generar_pdf
from onedrive_uploader import subir_pdf_a_onedrive

from models import (
    crear_base_datos,
    guardar_orden,
    obtener_siguiente_ot,
    obtener_historial,
    obtener_orden,
    guardar_firma_supervisor,
    guardar_firma_coordinador,
)

app = Flask(__name__)

crear_base_datos()


# ==========================================
# INCRUSTAR CSS DIRECTAMENTE EN EL HTML
# ==========================================
# Esto es necesario porque el PDF se genera con Playwright a
# partir de un HTML que no siempre se sirve por HTTP, así que
# la ruta /static/css/estilos.css no funcionaría ahí. Al
# incrustar el CSS dentro de un <style>, el PDF sale con el
# formato correcto sin importar cómo se genere el HTML.

def cargar_css_inline():

    ruta_css = os.path.join(app.static_folder, "css", "estilos.css")

    try:
        with open(ruta_css, "r", encoding="utf-8") as archivo_css:
            return archivo_css.read()
    except OSError:
        return ""


@app.context_processor
def inyectar_css_inline():
    return dict(css_inline=cargar_css_inline())


# ==========================================
# INCRUSTAR EL LOGO DIRECTAMENTE EN EL HTML
# ==========================================

def cargar_logo_base64():

    ruta_logo = os.path.join(app.static_folder, "img", "logo_kerui.png")

    try:
        with open(ruta_logo, "rb") as archivo_logo:
            return base64.b64encode(archivo_logo.read()).decode("utf-8")
    except OSError:
        return ""


@app.context_processor
def inyectar_logo_inline():
    return dict(logo_base64=cargar_logo_base64())


# ==========================================
# CONSTRUIR EL HTML DEL PDF A PARTIR DE UNA ORDEN
# ==========================================
# Se usa tanto al guardar la orden por primera vez, como al
# regenerar el PDF final cuando el coordinador firma. 'orden'
# es un diccionario con las llaves de la base de datos (ver
# models.py): nombre, apellidos, hora_inicio, equipo_sap, etc.

def construir_html_pdf(orden):

    return render_template(
        "orden_pdf.html",

        numero_ot=orden.get("numero_ot", ""),

        tecnico_nombre=orden.get("nombre", ""),
        tecnico_apellidos=orden.get("apellidos", ""),

        fecha=orden.get("fecha", ""),
        hora_inicio=orden.get("hora_inicio", ""),
        horometro=orden.get("horometro", ""),

        ubicacion=orden.get("ubicacion", ""),
        equipo=orden.get("equipo", ""),
        sap=orden.get("equipo_sap", ""),
        numero_serie=orden.get("numero_serie", ""),

        descripcion_orden=orden.get("descripcion_orden", ""),
        tipo_orden=orden.get("tipo_orden", ""),

        operacion1=orden.get("operacion1", ""),
        frecuencia1=orden.get("frecuencia1", ""),
        operacion2=orden.get("operacion2", ""),
        frecuencia2=orden.get("frecuencia2", ""),
        operacion3=orden.get("operacion3", ""),
        frecuencia3=orden.get("frecuencia3", ""),

        permiso_trabajo=orden.get("permiso_trabajo", ""),
        fecha_finalizacion=orden.get("fecha_finalizacion", ""),
        hora_final=orden.get("hora_final", ""),
        prioridad=orden.get("prioridad", ""),
        especialidad=orden.get("especialidad", ""),

        actividad_realizada=orden.get("actividad_realizada", ""),
        como_quedo=orden.get("como_quedo", ""),
        recomendaciones=orden.get("recomendaciones", ""),

        parte_fallo=orden.get("parte_fallo", ""),
        causa_falla=orden.get("causa_falla", ""),
        parada=orden.get("parada", ""),
        tiempo_fuera=orden.get("tiempo_fuera", ""),
        tiempo_reparacion=orden.get("tiempo_reparacion", ""),

        repuestos=orden.get("repuestos", []),
        tecnicos=orden.get("tecnicos", []),

        fecha_firma_tecnico=orden.get("fecha_firma_tecnico", ""),
        fecha_firma_supervisor=orden.get("fecha_firma_supervisor", ""),
        fecha_firma_coordinador=orden.get("fecha_firma_coordinador", ""),

        firma_tecnico=orden.get("firma_tecnico") or "",
        firma_supervisor=orden.get("firma_supervisor") or "",
        firma_coordinador=orden.get("firma_coordinador") or "",
    )


def _guardar_firma_como_archivo(numero_ot, rol, firma_data_uri):
    """Guarda una copia de la firma como PNG en la carpeta 'firmas'."""

    if not firma_data_uri or "," not in firma_data_uri:
        return

    encabezado, datos = firma_data_uri.split(",", 1)
    imagen = base64.b64decode(datos)

    if os.path.exists("firmas") and not os.path.isdir("firmas"):
        os.remove("firmas")

    os.makedirs("firmas", exist_ok=True)

    ruta_firma = os.path.join("firmas", f"{numero_ot}_{rol}.png")

    with open(ruta_firma, "wb") as archivo:
        archivo.write(imagen)


@app.route("/", methods=["GET", "POST"])
def inicio():

    if request.method == "POST":

        form = request.form

        repuestos = [
            {
                "item": form.get(f"repuesto{i}_item") or "",
                "descripcion": form.get(f"repuesto{i}_descripcion") or "",
                "parte": form.get(f"repuesto{i}_parte") or "",
                "cantidad": form.get(f"repuesto{i}_cantidad") or "",
            }
            for i in range(1, 6)
        ]

        tecnicos = [
            {
                "nombre": form.get("tecnico_nombre") or "",
                "apellidos": form.get("tecnico_apellidos") or "",
                "fecha": form.get("tecnico1_fecha") or "",
                "horas": form.get("tecnico1_horas") or "",
                "extra": form.get("tecnico1_extra") or "",
            }
        ]

        for i in range(2, 5):
            tecnicos.append({
                "nombre": form.get(f"tecnico_nombre{i}") or "",
                "apellidos": form.get(f"tecnico_apellidos{i}") or "",
                "fecha": form.get(f"tecnico{i}_fecha") or "",
                "horas": form.get(f"tecnico{i}_horas") or "",
                "extra": form.get(f"tecnico{i}_extra") or "",
            })

        numero_ot = obtener_siguiente_ot()

        firma_tecnico = form.get("firma_tecnico") or ""
        if "," not in firma_tecnico:
            firma_tecnico = ""

        _guardar_firma_como_archivo(numero_ot, "tecnico", firma_tecnico)

        datos = {
            "numero_ot": numero_ot,
            "fecha": form.get("fecha") or "",
            "hora_inicio": form.get("hora_inicio") or "",
            "horometro": form.get("horometro") or "",
            "nombre": form.get("tecnico_nombre") or "",
            "apellidos": form.get("tecnico_apellidos") or "",
            "ubicacion": form.get("ubicacion") or "",
            "equipo": form.get("equipo") or "",
            "equipo_sap": form.get("sap") or "",
            "numero_serie": form.get("serie") or "",

            "descripcion_orden": form.get("descripcion_orden") or "",
            "tipo_orden": form.get("tipo_orden") or "",
            "operacion1": form.get("operacion1") or "",
            "frecuencia1": form.get("frecuencia1") or "",
            "operacion2": form.get("operacion2") or "",
            "frecuencia2": form.get("frecuencia2") or "",
            "operacion3": form.get("operacion3") or "",
            "frecuencia3": form.get("frecuencia3") or "",

            "permiso_trabajo": form.get("permiso_trabajo") or "",
            "fecha_finalizacion": form.get("fecha_finalizacion") or "",
            "hora_final": form.get("hora_final") or "",
            "prioridad": form.get("prioridad") or "",
            "especialidad": form.get("especialidad") or "",

            "actividad_realizada": form.get("actividad_realizada") or "",
            "como_quedo": form.get("como_quedo") or "",
            "recomendaciones": form.get("recomendaciones") or "",

            "parte_fallo": form.get("parte_fallo") or "",
            "causa_falla": form.get("causa_falla") or "",
            "parada": form.get("parada") or "",
            "tiempo_fuera": form.get("tiempo_fuera") or "",
            "tiempo_reparacion": form.get("tiempo_reparacion") or "",

            "repuestos": repuestos,
            "tecnicos": tecnicos,

            "firma_tecnico": firma_tecnico,
            "fecha_firma_tecnico": form.get("fecha_firma_tecnico") or date.today().isoformat(),
        }

        guardar_orden(datos)

        # PDF preliminar: ya tiene la firma del técnico, las
        # de supervisor/coordinador quedan en blanco hasta que
        # ellos aprueben desde su propio enlace.
        html_pdf = construir_html_pdf(datos)

        ruta_pdf_generado = generar_pdf(numero_ot, html_pdf)

        return render_template(
            "confirmacion.html",
            numero_ot=numero_ot,
            pdf_link=url_for("pdf_descarga", numero_ot=numero_ot),
            link_supervisor=url_for(
                "aprobar_supervisor", numero_ot=numero_ot, _external=True
            ),
        )

    numero_ot = obtener_siguiente_ot()

    return render_template(
        "orden_mantenimiento.html",
        numero_ot=numero_ot
    )


@app.route("/pdf-descarga/<numero_ot>")
def pdf_descarga(numero_ot):

    ruta_pdf = os.path.join("pdf", f"{numero_ot}.pdf")

    if not os.path.exists(ruta_pdf):
        abort(404)

    return send_file(
        ruta_pdf,
        mimetype="application/pdf",
        as_attachment=False,
        download_name=f"{numero_ot}.pdf"
    )


# ==========================================
# APROBACIÓN DEL SUPERVISOR
# ==========================================

@app.route("/orden/<numero_ot>/aprobar/supervisor", methods=["GET", "POST"])
def aprobar_supervisor(numero_ot):

    orden = obtener_orden(numero_ot)

    if orden is None:
        abort(404)

    if request.method == "POST":

        if orden["estado"] != "PENDIENTE_SUPERVISOR":
            return render_template(
                "aprobar_estado.html",
                mensaje="Esta orden ya no está pendiente de la firma del supervisor.",
                numero_ot=numero_ot
            )

        firma = request.form.get("firma") or ""

        if "," not in firma:
            return render_template(
                "aprobar_estado.html",
                mensaje="No se recibió ninguna firma. Vuelve a intentarlo.",
                numero_ot=numero_ot
            )

        _guardar_firma_como_archivo(numero_ot, "supervisor", firma)

        guardar_firma_supervisor(
            numero_ot,
            firma,
            date.today().isoformat()
        )

        return render_template(
            "aprobar_estado.html",
            mensaje="✅ Firma de supervisor registrada. La orden queda pendiente del coordinador de operaciones.",
            numero_ot=numero_ot,
            siguiente_link=url_for(
                "aprobar_coordinador", numero_ot=numero_ot, _external=True
            )
        )

    if orden["estado"] != "PENDIENTE_SUPERVISOR":
        return render_template(
            "aprobar_estado.html",
            mensaje="Esta orden ya no está pendiente de la firma del supervisor "
                    f"(estado actual: {orden['estado']}).",
            numero_ot=numero_ot
        )

    return render_template(
        "aprobar.html",
        orden=orden,
        rol="supervisor",
        titulo="Firma del Supervisor / Ing. Mtto"
    )


# ==========================================
# APROBACIÓN DEL COORDINADOR
# ==========================================

@app.route("/orden/<numero_ot>/aprobar/coordinador", methods=["GET", "POST"])
def aprobar_coordinador(numero_ot):

    orden = obtener_orden(numero_ot)

    if orden is None:
        abort(404)

    if request.method == "POST":

        if orden["estado"] != "PENDIENTE_COORDINADOR":
            return render_template(
                "aprobar_estado.html",
                mensaje="Esta orden ya no está pendiente de la firma del coordinador.",
                numero_ot=numero_ot
            )

        firma = request.form.get("firma") or ""

        if "," not in firma:
            return render_template(
                "aprobar_estado.html",
                mensaje="No se recibió ninguna firma. Vuelve a intentarlo.",
                numero_ot=numero_ot
            )

        _guardar_firma_como_archivo(numero_ot, "coordinador", firma)

        guardar_firma_coordinador(
            numero_ot,
            firma,
            date.today().isoformat()
        )

        # ==========================================
        # REGENERAR EL PDF FINAL (con las 3 firmas)
        # ==========================================

        orden_actualizada = obtener_orden(numero_ot)

        html_pdf = construir_html_pdf(orden_actualizada)

        ruta_pdf_generado = generar_pdf(numero_ot, html_pdf)

        # Ahora que la orden está 100% aprobada, se sube la
        # versión definitiva a SharePoint/OneDrive.
        subir_pdf_a_onedrive(
            ruta_pdf_generado,
            numero_ot,
            orden_actualizada.get("equipo", "")
        )

        return render_template(
            "aprobar_estado.html",
            mensaje="✅ Orden aprobada por completo. El PDF final ya quedó generado.",
            numero_ot=numero_ot,
            pdf_link=url_for("pdf_descarga", numero_ot=numero_ot)
        )

    if orden["estado"] != "PENDIENTE_COORDINADOR":
        return render_template(
            "aprobar_estado.html",
            mensaje="Esta orden todavía no está lista para la firma del coordinador "
                    f"(estado actual: {orden['estado']}).",
            numero_ot=numero_ot
        )

    return render_template(
        "aprobar.html",
        orden=orden,
        rol="coordinador",
        titulo="Firma del Coordinador de Operaciones"
    )


@app.route("/historial")
def historial():

    ordenes = obtener_historial()

    return render_template(
        "historial.html",
        ordenes=ordenes
    )


@app.route("/orden/<numero_ot>")
def ver_orden(numero_ot):

    orden = obtener_orden(numero_ot)

    if orden is None:
        abort(404)

    return render_template(
        "ver_orden.html",
        orden=orden
    )


@app.route("/pdf/<numero_ot>")
def vista_pdf(numero_ot):

    orden = obtener_orden(numero_ot)

    if orden is None:
        abort(404)

    return construir_html_pdf(orden)


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )
