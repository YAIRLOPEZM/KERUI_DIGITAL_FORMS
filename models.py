import sqlite3
import os
import json

# Ruta donde estará la base de datos
DB_PATH = os.path.join("database", "ordenes.db")


def _conectar():
    conexion = sqlite3.connect(DB_PATH)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_base_datos():

    # Crear la carpeta si no existe. Si por algún motivo ya
    # existe un ARCHIVO (no carpeta) llamado "database", se
    # elimina primero para poder crear la carpeta correctamente.
    if os.path.exists("database") and not os.path.isdir("database"):
        os.remove("database")

    os.makedirs("database", exist_ok=True)

    conexion = sqlite3.connect(DB_PATH)

    cursor = conexion.cursor()

    cursor.execute("""

    CREATE TABLE IF NOT EXISTS ordenes (

        id INTEGER PRIMARY KEY AUTOINCREMENT,

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

    conexion.close()


def guardar_orden(datos):
    """
    Guarda una orden completa. 'datos' es un diccionario con
    todas las llaves que necesita la orden (ver la lista de
    columnas de la tabla). 'repuestos' y 'tecnicos' deben venir
    como listas de diccionarios (se convierten a JSON aquí).
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
            :numero_ot, :fecha, :hora_inicio, :horometro, :nombre, :apellidos,
            :ubicacion, :equipo, :equipo_sap, :numero_serie,
            :descripcion_orden, :tipo_orden,
            :operacion1, :frecuencia1, :operacion2, :frecuencia2, :operacion3, :frecuencia3,
            :permiso_trabajo, :fecha_finalizacion, :hora_final, :prioridad, :especialidad,
            :actividad_realizada, :como_quedo, :recomendaciones,
            :parte_fallo, :causa_falla, :parada, :tiempo_fuera, :tiempo_reparacion,
            :repuestos_json, :tecnicos_json,
            :firma_tecnico, :fecha_firma_tecnico,
            'PENDIENTE_SUPERVISOR'
        )

    """, {
        **datos,
        "repuestos_json": json.dumps(datos.get("repuestos", [])),
        "tecnicos_json": json.dumps(datos.get("tecnicos", [])),
    })

    conexion.commit()
    conexion.close()


def obtener_siguiente_ot():

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT numero_ot

        FROM ordenes

        ORDER BY id DESC

        LIMIT 1

    """)

    ultimo = cursor.fetchone()

    conexion.close()

    if ultimo is None:

        return "OM26-216"

    numero = int(ultimo["numero_ot"].split("-")[1])

    siguiente = numero + 1

    return f"OM26-{siguiente}"


def obtener_historial():

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT id, numero_ot, fecha, nombre, apellidos, equipo, estado

        FROM ordenes

        ORDER BY id DESC

    """)

    datos = cursor.fetchall()

    conexion.close()

    return datos


def obtener_orden(numero_ot):
    """
    Devuelve la orden como diccionario, con 'repuestos' y
    'tecnicos' ya convertidos de JSON a listas de Python.
    None si no existe.
    """

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM ordenes

        WHERE numero_ot = ?

    """, (numero_ot,))

    fila = cursor.fetchone()

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
        SET firma_supervisor = ?,
            fecha_firma_supervisor = ?,
            estado = 'PENDIENTE_COORDINADOR'
        WHERE numero_ot = ?

    """, (firma, fecha, numero_ot))

    conexion.commit()
    conexion.close()


def guardar_firma_coordinador(numero_ot, firma, fecha):

    conexion = _conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        UPDATE ordenes
        SET firma_coordinador = ?,
            fecha_firma_coordinador = ?,
            estado = 'APROBADA'
        WHERE numero_ot = ?

    """, (firma, fecha, numero_ot))

    conexion.commit()
    conexion.close()
