def actualizar_orden(numero_ot, datos):
    """
    Actualiza los datos diligenciados de una orden ya existente.
    NO toca: estado, firma_tecnico, firma_supervisor, firma_coordinador,
    fecha_firma_tecnico, fecha_firma_coordinador.
    SÍ toca: fecha_firma_supervisor (puede diferir de cuándo el técnico
    diligenció la orden).
    """

    campos_editables = [
        "fecha", "hora_inicio", "horometro", "nombre", "apellidos",
        "ubicacion", "equipo", "equipo_sap", "numero_serie",
        "descripcion_orden", "tipo_orden",
        "operacion1", "frecuencia1", "operacion2", "frecuencia2",
        "operacion3", "frecuencia3", "permiso_trabajo",
        "fecha_finalizacion", "hora_final", "prioridad", "especialidad",
        "actividad_realizada", "como_quedo", "recomendaciones",
        "parte_fallo", "causa_falla", "parada", "tiempo_fuera",
        "tiempo_reparacion", "fecha_firma_supervisor",
    ]

    asignaciones = ", ".join(f"{campo} = %({campo})s" for campo in campos_editables)

    parametros = {campo: datos.get(campo) for campo in campos_editables}
    parametros["numero_ot"] = numero_ot
    parametros["repuestos_json"] = json.dumps(datos.get("repuestos", []))
    parametros["tecnicos_json"] = json.dumps(datos.get("tecnicos", []))

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute(f"""
        UPDATE ordenes
        SET {asignaciones},
            repuestos_json = %(repuestos_json)s,
            tecnicos_json = %(tecnicos_json)s
        WHERE numero_ot = %(numero_ot)s
    """, parametros)

    conexion.commit()
    cursor.close()
    conexion.close()
