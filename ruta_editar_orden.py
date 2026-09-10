# ==========================================
# EDICIÓN DE ORDEN (solo supervisor, vía /historial)
# ==========================================
# No se toca estado, firmas, ni fecha_firma_tecnico/coordinador.
# fecha_firma_supervisor SÍ es editable (ver actualizar_orden()).

@app.route("/orden/<numero_ot>/editar", methods=["GET", "POST"])
def editar_orden(numero_ot):

    orden = obtener_orden(numero_ot)

    if orden is None:
        abort(404)

    if not session.get("supervisor_autenticado"):
        return redirect(url_for("verificar_supervisor", numero_ot=numero_ot))

    if request.method == "POST":

        form = request.form

        # Mismo armado que en inicio() — repuestos y técnicos vienen
        # como campos sueltos repuestoN_*, tecnico_nombreN, etc., no
        # como un JSON ya armado.
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

        datos = {
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
            "fecha_firma_supervisor": form.get("fecha_firma_supervisor") or "",
        }

        actualizar_orden(numero_ot, datos)

        # ==========================================
        # REGENERAR EL PDF CON LOS DATOS CORREGIDOS
        # ==========================================
        # obtener_orden ya trae las firmas y demás fechas de firma tal
        # cual estaban — no se tocan, solo cambian los datos de texto
        # y (si aplica) la fecha de aprobación del supervisor.

        orden_actualizada = obtener_orden(numero_ot)

        html_pdf = construir_html_pdf(orden_actualizada)

        ruta_pdf_generado = generar_pdf(numero_ot, html_pdf)

        with open(ruta_pdf_generado, "rb") as f:
            guardar_pdf(numero_ot, f.read())

        return render_template(
            "aprobar_estado.html",
            mensaje="✅ Orden actualizada. El PDF fue regenerado con los datos corregidos.",
            numero_ot=numero_ot,
            pdf_link=url_for("pdf_descarga", numero_ot=numero_ot)
        )

    # GET: reutiliza el mismo formulario de creación, precargado.
    return render_template(
        "orden_mantenimiento.html",
        numero_ot=numero_ot,
        orden=orden,
        modo="editar"
    )


@app.route("/orden/<numero_ot>/editar/verificar", methods=["GET", "POST"])
def verificar_supervisor(numero_ot):

    if request.method == "POST":

        clave_ingresada = request.form.get("password", "")

        if clave_ingresada == os.environ.get("SUPERVISOR_PASSWORD"):
            session["supervisor_autenticado"] = True
            return redirect(url_for("editar_orden", numero_ot=numero_ot))

        return render_template(
            "verificar_password.html",
            numero_ot=numero_ot,
            error="Contraseña incorrecta."
        )

    return render_template(
        "verificar_password.html",
        numero_ot=numero_ot,
        error=None
    )
