import sqlite3
import os

# Ruta donde estará la base de datos
DB_PATH = os.path.join("database", "ordenes.db")


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

        numero_ot TEXT,

        fecha TEXT,

        hora TEXT,

        horometro TEXT,

        nombre TEXT,

        apellidos TEXT,

        ubicacion TEXT,

        equipo TEXT,

        equipo_sap TEXT,

        numero_serie TEXT


    )

     """)

    conexion.commit()

    conexion.close()

def guardar_orden(

    numero_ot,

    fecha,

    hora,

    horometro,

    nombre,

    apellidos,

    ubicacion,

    equipo,

    equipo_sap,

    numero_serie

):

    conexion = sqlite3.connect(DB_PATH)

    cursor = conexion.cursor()

    cursor.execute("""

        INSERT INTO ordenes (
            numero_ot,
            fecha,
            hora,
            horometro,
            nombre,
            apellidos,
            ubicacion,
            equipo,
            equipo_sap,
            numero_serie

        )

        VALUES (?, ?, ?, ?, ?, ?, ?, ?,?,?)

    """, (
        numero_ot,
        fecha,
        hora,
        horometro,
        nombre,
        apellidos,
        ubicacion,
        equipo,
        equipo_sap,
        numero_serie

    ))

    conexion.commit()

    conexion.close()

def obtener_siguiente_ot():

    conexion = sqlite3.connect(DB_PATH)

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

    numero = int(ultimo[0].split("-")[1])

    siguiente = numero + 1

    return f"OM26-{siguiente}"

def obtener_historial():

    conexion = sqlite3.connect(DB_PATH)

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM ordenes

        ORDER BY id DESC

    """)

    datos = cursor.fetchall()

    conexion.close()

    return datos

def obtener_orden(numero_ot):

    conexion = sqlite3.connect(DB_PATH)

    conexion.row_factory = sqlite3.Row

    cursor = conexion.cursor()

    cursor.execute("""

        SELECT *

        FROM ordenes

        WHERE numero_ot = ?

    """, (numero_ot,))

    orden = cursor.fetchone()

    conexion.close()

    return orden