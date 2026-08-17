import os
import re
import time
import requests

# ==========================================
# CONFIGURACIÓN (se llena con variables de entorno)
# ==========================================
# Estos 5 valores los da TI/administrador de Microsoft 365:
#
#   MS_TENANT_ID       -> Tenant ID de Azure AD
#   MS_CLIENT_ID        -> Application (client) ID del App Registration
#   MS_CLIENT_SECRET    -> Client secret generado para esa app
#   MS_SITE_HOSTNAME    -> ej: "shandongkerui.sharepoint.com"
#   MS_SITE_PATH        -> ej: "/sites/Mantenimiento"
#
# En Windows/local: se configuran como variables de entorno del sistema,
# o en un archivo .env (ver más abajo cómo cargarlas).
# En Render: se configuran en Settings > Environment.

TENANT_ID = os.environ.get("MS_TENANT_ID", "")
CLIENT_ID = os.environ.get("MS_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("MS_CLIENT_SECRET", "")
SITE_HOSTNAME = os.environ.get("MS_SITE_HOSTNAME", "")
SITE_PATH = os.environ.get("MS_SITE_PATH", "")

# Carpeta raíz dentro del sitio de SharePoint donde se van a
# organizar las subcarpetas por equipo/máquina.
CARPETA_RAIZ = "Ordenes de Mantenimiento"

GRAPH_URL = "https://graph.microsoft.com/v1.0"

# Cache simple del token en memoria (para no pedir uno nuevo en cada PDF)
_token_cache = {"token": None, "expira": 0}
_site_id_cache = {"id": None}


def _credenciales_configuradas():
    return all([TENANT_ID, CLIENT_ID, CLIENT_SECRET, SITE_HOSTNAME, SITE_PATH])


def _obtener_token():

    ahora = time.time()

    if _token_cache["token"] and ahora < _token_cache["expira"] - 60:
        return _token_cache["token"]

    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    datos = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
    }

    respuesta = requests.post(url, data=datos, timeout=15)
    respuesta.raise_for_status()

    cuerpo = respuesta.json()

    _token_cache["token"] = cuerpo["access_token"]
    _token_cache["expira"] = ahora + cuerpo.get("expires_in", 3600)

    return _token_cache["token"]


def _obtener_site_id(token):

    if _site_id_cache["id"]:
        return _site_id_cache["id"]

    url = f"{GRAPH_URL}/sites/{SITE_HOSTNAME}:{SITE_PATH}"

    headers = {"Authorization": f"Bearer {token}"}

    respuesta = requests.get(url, headers=headers, timeout=15)
    respuesta.raise_for_status()

    site_id = respuesta.json()["id"]

    _site_id_cache["id"] = site_id

    return site_id


def _sanear_nombre_carpeta(nombre):

    nombre = (nombre or "SIN_EQUIPO").strip()

    if not nombre:
        nombre = "SIN_EQUIPO"

    # Quitar caracteres no permitidos en nombres de carpeta de SharePoint
    nombre = re.sub(r'[\\/:*?"<>|#%]', "-", nombre)

    return nombre[:100]


def subir_pdf_a_onedrive(ruta_pdf_local, numero_ot, nombre_equipo):
    """
    Sube el PDF ya generado a una carpeta de SharePoint,
    organizada por equipo/máquina.

    Si las credenciales no están configuradas, o si algo falla,
    NO lanza error hacia afuera (para no romper la generación
    del PDF ni la respuesta al usuario) — solo lo avisa por consola.
    """

    if not _credenciales_configuradas():
        print(
            "⚠️  OneDrive/SharePoint no está configurado todavía "
            "(faltan variables de entorno MS_...). Se omite la subida."
        )
        return False

    try:
        token = _obtener_token()
        site_id = _obtener_site_id(token)

        carpeta_equipo = _sanear_nombre_carpeta(nombre_equipo)
        nombre_archivo = os.path.basename(ruta_pdf_local)

        ruta_destino = f"{CARPETA_RAIZ}/{carpeta_equipo}/{nombre_archivo}"

        url = (
            f"{GRAPH_URL}/sites/{site_id}/drive/root:/"
            f"{ruta_destino}:/content"
        )

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/pdf",
        }

        with open(ruta_pdf_local, "rb") as archivo:
            respuesta = requests.put(
                url,
                headers=headers,
                data=archivo,
                timeout=30
            )

        respuesta.raise_for_status()

        print(
            f"✅ PDF subido a SharePoint: {ruta_destino}"
        )

        return True

    except Exception as error:

        print(
            f"⚠️  No se pudo subir el PDF a SharePoint "
            f"({numero_ot}): {error}"
        )

        return False
