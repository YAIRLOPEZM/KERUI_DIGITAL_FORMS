import os
import json

import psycopg2
import psycopg2.extras

# ==========================================
# CONEXIÓN A POSTGRES (Neon / Supabase)
# ==========================================
# La URL completa de conexión viene de la variable de entorno
# DATABASE_URL (ej: postgresql://usuario:password@host/basedatos).
# En Render se configura en Settings > Environment.
# En local (Windows), como variable de entorno del sistema.

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def _conectar():
    if not DATABASE_URL:
        raise RuntimeError(
            "Falta configurar la variable de entorno DATABASE_URL "
            "(connection string de Neon/Supabase)."
        )
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def crear_base_datos():

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS ordenes (

        id SERIAL PRIMARY KEY,

        numero_ot TEXT UNIQUE,

        fecha TEXT,
        hora_inicio TEXT,
        horometro TEXT,
        nombre TEXT,
        apellidos TEXT,
        ubicacion TEXT,
        equipo TEXT,
        equipo_sap TEXT,
        numero_serie TEXT,

        descripcion_orden TEXT,
        tipo_orden TEXT,
        operacion1 TEXT,
        frecuencia1 TEXT,
        operacion2 TEXT,
        frecuencia2 TEXT,
        operacion3 TEXT,
        frecuencia3 TEXT,

        permiso_trabajo TEXT,
        fecha_finalizacion TEXT,
        hora_final TEXT,
        prioridad TEXT,
        especialidad TEXT,

        actividad_realizada TEXT,
        como_quedo TEXT,
        recomendaciones TEXT,

        parte_fallo TEXT,
        causa_falla TEXT,
        parada TEXT,
        tiempo_fuera TEXT,
        tiempo_reparacion TEXT,

        repuestos_json TEXT,
        tecnicos_json TEXT,

        firma_tecnico TEXT,
        fecha_firma_tecnico TEXT,

        firma_supervisor TEXT,
        fecha_firma_supervisor TEXT,

        firma_coordinador TEXT,
        fecha_firma_coordinador TEXT,

        estado TEXT DEFAULT 'PENDIENTE_SUPERVISOR'

    )

     """)

    conexion.commit()

    # ==========================================
    # AUTO-MIGRACIÓN
    # ==========================================
    # Igual que antes: si la tabla ya existía con menos columnas,
    # agrega las que falten sin borrar los datos. Postgres soporta
    # "ADD COLUMN IF NOT EXISTS" directamente, así que es incluso
    # más simple que la versión de SQLite.

    columnas_necesarias = {
        "fecha": "TEXT",
        "hora_inicio": "TEXT",
        "horometro": "TEXT",
        "nombre": "TEXT",
        "apellidos": "TEXT",
        "ubicacion": "TEXT",
        "equipo": "TEXT",
        "equipo_sap": "TEXT",
        "numero_serie": "TEXT",
        "descripcion_orden": "TEXT",
        "tipo_orden": "TEXT",
        "operacion1": "TEXT",
        "frecuencia1": "TEXT",
        "operacion2": "TEXT",
        "frecuencia2": "TEXT",
        "operacion3": "TEXT",
        "frecuencia3": "TEXT",
        "permiso_trabajo": "TEXT",
        "fecha_finalizacion": "TEXT",
        "hora_final": "TEXT",
        "prioridad": "TEXT",
        "especialidad": "TEXT",
        "actividad_realizada": "TEXT",
        "como_quedo": "TEXT",
        "recomendaciones": "TEXT",
        "parte_fallo": "TEXT",
        "causa_falla": "TEXT",
        "parada": "TEXT",
        "tiempo_fuera": "TEXT",
        "tiempo_reparacion": "TEXT",
        "repuestos_json": "TEXT",
        "tecnicos_json": "TEXT",
        "firma_tecnico": "TEXT",
        "fecha_firma_tecnico": "TEXT",
        "firma_supervisor": "TEXT",
        "fecha_firma_supervisor": "TEXT",
        "firma_coordinador": "TEXT",
        "fecha_firma_coordinador": "TEXT",
        "estado": "TEXT DEFAULT 'PENDIENTE_SUPERVISOR'",
    }

    for columna, tipo in columnas_necesarias.items():
        cursor.execute(
            f"ALTER TABLE ordenes ADD COLUMN IF NOT EXISTS {columna} {tipo}"
        )

    conexion.commit()

    # ==========================================
    # TABLA DEL CONSECUTIVO (independiente de "ordenes")
    # ==========================================
    # Guarda el último número de OT usado en una sola fila.
    # Así el consecutivo no depende de cuántas órdenes de
    # prueba existan ni de si se borran o no.

    cursor.execute("""

        CREATE TABLE IF NOT EXISTS contador_ot (
            id SERIAL PRIMARY KEY,
            valor INTEGER NOT NULL
        )

    """)

    cursor.execute("SELECT COUNT(*) FROM contador_ot")

    if cursor.fetchone()[0] == 0:
        # Primera vez que corre: arranca en 216, igual que antes.
        # Ajusta este valor UNA sola vez, la primera vez que
        # despliegues este cambio, si necesitas otro punto de partida.
        cursor.execute("INSERT INTO contador_ot (valor) VALUES (216)")

    conexion.commit()

    cursor.close()
    conexion.close()


def guardar_orden(datos):
    """
    Guarda una orden completa. 'datos' es un diccionario con
    todas las llaves que necesita la orden. 'repuestos' y
    'tecnicos' deben venir como listas de diccionarios (se
    convierten a JSON aquí).
    """

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        INSERT INTO ordenes (
            numero_ot, fecha, hora_inicio, horometro, nombre, apellidos,
            ubicacion, equipo, equipo_sap, numero_serie,
            descripcion_orden, tipo_orden,
            operacion1, frecuencia1, operacion2, frecuencia2, operacion3, frecuencia3,
            permiso_trabajo, fecha_finalizacion, hora_final, prioridad, especialidad,
            actividad_realizada, como_quedo, recomendaciones,
            parte_fallo, causa_falla, parada, tiempo_fuera, tiempo_reparacion,
            repuestos_json, tecnicos_json,
            firma_tecnico, fecha_firma_tecnico,
            estado
        )
        VALUES (
            %(numero_ot)s, %(fecha)s, %(hora_inicio)s, %(horometro)s, %(nombre)s, %(apellidos)s,
            %(ubicacion)s, %(equipo)s, %(equipo_sap)s, %(numero_serie)s,
            %(descripcion_orden)s, %(tipo_orden)s,
            %(operacion1)s, %(frecuencia1)s, %(operacion2)s, %(frecuencia2)s, %(operacion3)s, %(frecuencia3)s,
            %(permiso_trabajo)s, %(fecha_finalizacion)s, %(hora_final)s, %(prioridad)s, %(especialidad)s,
            %(actividad_realizada)s, %(como_quedo)s, %(recomendaciones)s,
            %(parte_fallo)s, %(causa_falla)s, %(parada)s, %(tiempo_fuera)s, %(tiempo_reparacion)s,
            %(repuestos_json)s, %(tecnicos_json)s,
            %(firma_tecnico)s, %(fecha_firma_tecnico)s,
            'PENDIENTE_SUPERVISOR'
        )

    """, {
        **datos,
        "repuestos_json": json.dumps(datos.get("repuestos", [])),
        "tecnicos_json": json.dumps(datos.get("tecnicos", [])),
    })

    conexion.commit()
    cursor.close()
    conexion.close()


def obtener_siguiente_ot():
    """
    Toma el consecutivo de la tabla contador_ot (no de las
    órdenes existentes) y lo incrementa en una sola operación
    atómica, para que dos personas no puedan recibir el mismo
    número si guardan al mismo tiempo.
    """

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE contador_ot
        SET valor = valor + 1
        RETURNING valor

    """)

    nuevo_valor = cursor.fetchone()[0]

    conexion.commit()
    cursor.close()
    conexion.close()

    return f"OM26-{nuevo_valor}"


def establecer_consecutivo(numero):
    """
    Ajusta manualmente el consecutivo. Después de llamar esto
    con, por ejemplo, establecer_consecutivo(250), la SIGUIENTE
    orden que se cree será OM26-251 (el consecutivo siempre
    entrega valor + 1, nunca el valor que le pongas tal cual).
    """

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE contador_ot
        SET valor = %s

    """, (numero,))

    conexion.commit()
    cursor.close()
    conexion.close()


def previsualizar_siguiente_ot():
    """
    Muestra cuál SERÍA el próximo número de OT, SIN gastarlo
    (solo lee, no incrementa). Se usa únicamente para mostrar
    un número de referencia en el formulario en blanco, antes
    de que el técnico guarde algo. El número real y definitivo
    se asigna con obtener_siguiente_ot(), solo al guardar.
    """

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("SELECT valor FROM contador_ot")

    valor_actual = cursor.fetchone()[0]

    cursor.close()
    conexion.close()

    return f"OM26-{valor_actual + 1}"


def obtener_todas_las_ordenes():
    """
    Devuelve TODAS las órdenes con TODOS sus campos (para el
    export a Excel) — a diferencia de obtener_historial(), que
    solo trae las columnas necesarias para la tabla en pantalla.
    """

    conexion = _conectar()
    cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""

        SELECT *

        FROM ordenes

        ORDER BY id DESC

    """)

    filas = cursor.fetchall()

    cursor.close()
    conexion.close()

    ordenes = []

    for fila in filas:
        orden = dict(fila)
        orden["repuestos"] = json.loads(orden.get("repuestos_json") or "[]")
        orden["tecnicos"] = json.loads(orden.get("tecnicos_json") or "[]")
        ordenes.append(orden)

    return ordenes


def obtener_historial():
    # OJO: historial.html accede a las columnas por posición
    # (orden[1], orden[2]...), igual que hacía sqlite3.Row. Por
    # eso aquí se usa el cursor normal (tuplas), NO RealDictCursor
    # — RealDictCursor no soporta acceso por índice numérico y
    # rompería esa plantilla.

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT id, numero_ot, fecha, nombre, apellidos, equipo, estado

        FROM ordenes

        ORDER BY id DESC

    """)

    datos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return datos


def obtener_orden(numero_ot):
    """
    Devuelve la orden como diccionario, con 'repuestos' y
    'tecnicos' ya convertidos de JSON a listas de Python.
    None si no existe.
    """

    conexion = _conectar()
    cursor = conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("""

        SELECT *

        FROM ordenes

        WHERE numero_ot = %s

    """, (numero_ot,))

    fila = cursor.fetchone()

    cursor.close()
    conexion.close()

    if fila is None:
        return None

    orden = dict(fila)

    orden["repuestos"] = json.loads(orden.get("repuestos_json") or "[]")
    orden["tecnicos"] = json.loads(orden.get("tecnicos_json") or "[]")

    return orden


def guardar_firma_supervisor(numero_ot, firma, fecha):

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE ordenes
        SET firma_supervisor = %s,
            fecha_firma_supervisor = %s,
            estado = 'PENDIENTE_COORDINADOR'
        WHERE numero_ot = %s

    """, (firma, fecha, numero_ot))

    conexion.commit()
    cursor.close()
    conexion.close()


def guardar_firma_coordinador(numero_ot, firma, fecha):

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE ordenes
        SET firma_coordinador = %s,
            fecha_firma_coordinador = %s,
            estado = 'APROBADA'
        WHERE numero_ot = %s

    """, (firma, fecha, numero_ot))

    conexion.commit()
    cursor.close()
    conexion.close()


def eliminar_orden(numero_ot):
    """
    Borra una orden por completo de la base de datos.
    No borra el PDF en OneDrive/SharePoint, solo el registro.
    """

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        DELETE FROM ordenes
        WHERE numero_ot = %s

    """, (numero_ot,))

    conexion.commit()
    cursor.close()
    conexion.close()
