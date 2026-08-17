from flask import Flask, render_template, request, send_file
import os
import base64
from pdf_generator import generar_pdf
from onedrive_uploader import subir_pdf_a_onedrive


from models import (

    crear_base_datos,

    guardar_orden,

    obtener_siguiente_ot,

    obtener_historial,

    obtener_orden

)
from pdf_generator import generar_pdf

app = Flask(__name__)

crear_base_datos()


# ==========================================
# INCRUSTAR CSS DIRECTAMENTE EN EL HTML
# ==========================================
# Esto es necesario porque el PDF se genera abriendo un
# archivo HTML temporal desde el disco (file:///...), y en
# ese caso la ruta /static/css/estilos.css no funciona (solo
# funciona cuando Flask sirve la página por HTTP). Al incrustar
# el CSS dentro de un <style>, el PDF sale con el formato
# correcto sin importar cómo se abra el HTML.

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
# Igual que con el CSS: al generar el PDF con Playwright
# el HTML no se sirve por HTTP, así que las rutas tipo
# /static/img/logo_kerui.png no cargarían. Se incrusta la
# imagen como base64 para que siempre se vea, sin importar
# cómo se genere el HTML.

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


@app.route("/", methods=["GET", "POST"])
def inicio():

    if request.method == "POST":

        tecnico_nombre = request.form.get("tecnico_nombre")
        tecnico_apellidos = request.form.get("tecnico_apellidos")
        fecha = request.form.get("fecha")
        horometro = request.form.get("horometro")
        hora_inicio = request.form.get("hora_inicio")
        ubicacion = request.form.get("ubicacion")
        equipo_desc = request.form.get("equipo")
        sap = request.form.get("sap")
        serie = request.form.get("serie")

        # ==========================================
        # INFORMACIÓN GENERAL
        # ==========================================

        descripcion_orden = request.form.get("descripcion_orden")
        tipo_orden = request.form.get("tipo_orden")

        operacion1 = request.form.get("operacion1")
        frecuencia1 = request.form.get("frecuencia1")

        operacion2 = request.form.get("operacion2")
        frecuencia2 = request.form.get("frecuencia2")

        operacion3 = request.form.get("operacion3")
        frecuencia3 = request.form.get("frecuencia3")

        permiso_trabajo = request.form.get("permiso_trabajo")
        fecha_finalizacion = request.form.get("fecha_finalizacion")
        hora_final = request.form.get("hora_final")
        prioridad = request.form.get("prioridad")
        especialidad = request.form.get("especialidad")

        # ==========================================
        # REPORTE TÉCNICO
        # ==========================================

        actividad_realizada = request.form.get("actividad_realizada")
        como_quedo = request.form.get("como_quedo")
        recomendaciones = request.form.get("recomendaciones")

        # ==========================================
        # INFORME DE FALLA
        # ==========================================

        parte_fallo = request.form.get("parte_fallo")
        causa_falla = request.form.get("causa_falla")
        parada = request.form.get("parada")
        tiempo_fuera = request.form.get("tiempo_fuera")
        tiempo_reparacion = request.form.get("tiempo_reparacion")

        # ==========================================
        # REPUESTOS UTILIZADOS (5 filas)
        # ==========================================

        repuestos = []

        for i in range(1, 6):
            repuestos.append({
                "item": request.form.get(f"repuesto{i}_item") or "",
                "descripcion": request.form.get(f"repuesto{i}_descripcion") or "",
                "parte": request.form.get(f"repuesto{i}_parte") or "",
                "cantidad": request.form.get(f"repuesto{i}_cantidad") or "",
            })

        # ==========================================
        # PERSONAL TÉCNICO (4 filas)
        # ==========================================

        tecnicos = [
            {
                "nombre": tecnico_nombre or "",
                "apellidos": tecnico_apellidos or "",
                "fecha": request.form.get("tecnico1_fecha") or "",
                "horas": request.form.get("tecnico1_horas") or "",
                "extra": request.form.get("tecnico1_extra") or "",
            }
        ]

        for i in range(2, 5):
            tecnicos.append({
                "nombre": request.form.get(f"tecnico_nombre{i}") or "",
                "apellidos": request.form.get(f"tecnico_apellidos{i}") or "",
                "fecha": request.form.get(f"tecnico{i}_fecha") or "",
                "horas": request.form.get(f"tecnico{i}_horas") or "",
                "extra": request.form.get(f"tecnico{i}_extra") or "",
            })

        # ==========================================
        # FIRMAS
        # ==========================================

        firma_tecnico = request.form.get("firma_tecnico")
        firma_supervisor = request.form.get("firma_supervisor")
        firma_coordinador = request.form.get("firma_coordinador")

        fecha_firma_tecnico = request.form.get("fecha_firma_tecnico")
        fecha_firma_supervisor = request.form.get("fecha_firma_supervisor")
        fecha_firma_coordinador = request.form.get("fecha_firma_coordinador")

        # Si algún campo de texto no se llenó, que quede vacío
        # en vez de aparecer como la palabra "None" en el PDF.
        tecnico_nombre = tecnico_nombre or ""
        tecnico_apellidos = tecnico_apellidos or ""
        fecha = fecha or ""
        horometro = horometro or ""
        hora_inicio = hora_inicio or ""
        ubicacion = ubicacion or ""
        equipo_desc = equipo_desc or ""
        sap = sap or ""
        serie = serie or ""
        descripcion_orden = descripcion_orden or ""
        tipo_orden = tipo_orden or ""
        operacion1 = operacion1 or ""
        frecuencia1 = frecuencia1 or ""
        operacion2 = operacion2 or ""
        frecuencia2 = frecuencia2 or ""
        operacion3 = operacion3 or ""
        frecuencia3 = frecuencia3 or ""
        permiso_trabajo = permiso_trabajo or ""
        fecha_finalizacion = fecha_finalizacion or ""
        hora_final = hora_final or ""
        prioridad = prioridad or ""
        especialidad = especialidad or ""
        actividad_realizada = actividad_realizada or ""
        como_quedo = como_quedo or ""
        recomendaciones = recomendaciones or ""
        parte_fallo = parte_fallo or ""
        causa_falla = causa_falla or ""
        parada = parada or ""
        tiempo_fuera = tiempo_fuera or ""
        tiempo_reparacion = tiempo_reparacion or ""
        fecha_firma_tecnico = fecha_firma_tecnico or ""
        fecha_firma_supervisor = fecha_firma_supervisor or ""
        fecha_firma_coordinador = fecha_firma_coordinador or ""

        numero_ot = obtener_siguiente_ot()

        print("TIPO:", tipo_orden)
        print("OPERACIÓN 1:", operacion1)
        print("FRECUENCIA 1:", frecuencia1)
        print("OPERACIÓN 2:", operacion2)
        print("FRECUENCIA 2:", frecuencia2)
        print("OPERACIÓN 3:", operacion3)
        print("FRECUENCIA 3:", frecuencia3)

        print((firma_tecnico or "")[:50])

        # ==========================
        # GUARDAR FIRMA DEL TÉCNICO
        # ==========================

        if firma_tecnico:

            if "," in firma_tecnico:

                encabezado, datos = firma_tecnico.split(",", 1)

                imagen = base64.b64decode(datos)

                if os.path.exists("firmas") and not os.path.isdir("firmas"):
                    os.remove("firmas")

                os.makedirs("firmas", exist_ok=True)

                ruta_firma = os.path.join(
                    "firmas",
                    f"{numero_ot}_tecnico.png"
                )

                with open(ruta_firma, "wb") as archivo:

                    archivo.write(imagen)

                print("✅ Firma guardada:", ruta_firma)

        guardar_orden(
            numero_ot=numero_ot,
            fecha=fecha,
            hora=hora_inicio,
            horometro=horometro,
            nombre=tecnico_nombre,
            apellidos=tecnico_apellidos,
            ubicacion=ubicacion,
            equipo=equipo_desc,
            equipo_sap=sap,
            numero_serie=serie
        )

        # ==========================================
        # CREAR HTML PARA EL PDF
        # ==========================================

        html_pdf = render_template(
            "orden_pdf.html",

            numero_ot=numero_ot,

            tecnico_nombre=tecnico_nombre,

            tecnico_apellidos=tecnico_apellidos,

            fecha=fecha,

            hora_inicio=hora_inicio,

            horometro=horometro,

            ubicacion=ubicacion,

            equipo=equipo_desc,

            sap=sap,

            numero_serie=serie,
            descripcion_orden=descripcion_orden,

            tipo_orden=tipo_orden,

            operacion1=operacion1,
            frecuencia1=frecuencia1,

            operacion2=operacion2,
            frecuencia2=frecuencia2,

            operacion3=operacion3,
            frecuencia3=frecuencia3,

            permiso_trabajo=permiso_trabajo,
            fecha_finalizacion=fecha_finalizacion,
            hora_final=hora_final,
            prioridad=prioridad,
            especialidad=especialidad,

            actividad_realizada=actividad_realizada,
            como_quedo=como_quedo,
            recomendaciones=recomendaciones,

            parte_fallo=parte_fallo,
            causa_falla=causa_falla,
            parada=parada,
            tiempo_fuera=tiempo_fuera,
            tiempo_reparacion=tiempo_reparacion,

            repuestos=repuestos,
            tecnicos=tecnicos,

            fecha_firma_tecnico=fecha_firma_tecnico,
            fecha_firma_supervisor=fecha_firma_supervisor,
            fecha_firma_coordinador=fecha_firma_coordinador,

            firma_tecnico=
                firma_tecnico
                if firma_tecnico and "," in firma_tecnico
                else "",
            firma_supervisor=
                firma_supervisor
                if firma_supervisor and "," in firma_supervisor
                else "",
            firma_coordinador=
                firma_coordinador
                if firma_coordinador and "," in firma_coordinador
                else ""
        )


        # ==========================================
        # GENERAR PDF
        # ==========================================

        ruta_pdf_generado = generar_pdf(

            numero_ot,

            html_pdf

        )

        # ==========================================
        # SUBIR EL PDF A SHAREPOINT/ONEDRIVE
        # ==========================================
        # Se organiza en una carpeta por equipo/máquina.
        # Si falla o no está configurado, no interrumpe
        # la generación ni la entrega del PDF al usuario.

        subir_pdf_a_onedrive(
            ruta_pdf_generado,
            numero_ot,
            equipo_desc
        )

        return send_file(
            ruta_pdf_generado,
            mimetype="application/pdf",
            as_attachment=False,
            download_name=f"{numero_ot}.pdf"
        )

    numero_ot = obtener_siguiente_ot()

    return render_template(
        "orden_mantenimiento.html",
        numero_ot=numero_ot
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

    return render_template(
        "ver_orden.html",
        orden=orden
    )

# ==========================================
# RUTA PARA GENERAR PDF
# ==========================================

@app.route("/pdf/<numero_ot>")
def vista_pdf(numero_ot):

    orden = obtener_orden(numero_ot)

    return render_template(
        "orden_pdf.html",

        numero_ot=numero_ot,

        tecnico_nombre=orden["nombre"],
        tecnico_apellidos=orden["apellidos"],

        fecha=orden["fecha"],
        hora_inicio=orden["hora"],

        horometro=orden["horometro"],

        ubicacion=orden["ubicacion"],

        sap=orden["equipo_sap"],

        numero_serie=orden["numero_serie"]
    )


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=True
    )