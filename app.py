import json

import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import pandas as pd
import plotly.express as px
import psycopg2

st.set_page_config(
    page_title="Seguimiento de RQ",
    page_icon="📦",
    layout="wide",
)

# ==========================================
# LOGIN
# ==========================================

# Local: lee credentials.yaml. En Streamlit Cloud: lee de Secrets.
if "credentials" in st.secrets:
    config = {
        "credentials": json.loads(st.secrets["credentials"]),
        "cookie": {
            "name": st.secrets["cookie_name"],
            "key": st.secrets["cookie_key"],
            "expiry_days": st.secrets["cookie_expiry_days"],
        },
    }
else:
    with open("credentials.yaml") as f:
        config = yaml.load(f, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

try:
    authenticator.login()
except Exception as e:
    st.error(e)

if st.session_state.get("authentication_status") is False:
    st.error("Usuario o contraseña incorrectos")
    st.stop()
elif st.session_state.get("authentication_status") is None:
    st.warning("Por favor ingresa tu usuario y contraseña")
    st.stop()

# ==========================================
# A PARTIR DE AQUI, SOLO SE EJECUTA SI EL LOGIN FUE EXITOSO
# (todo el dashboard original, indentado dentro de este bloque)
# ==========================================

authenticator.logout("Cerrar sesión", "sidebar")
st.sidebar.write(f"Bienvenido, **{st.session_state.get('name')}**")


@st.cache_data(ttl=300)  # se refresca solo cada 5 minutos, no en cada clic
def cargar_datos():
    database_url = st.secrets["DATABASE_URL"]
    conexion = psycopg2.connect(database_url, sslmode="require")
    df = pd.read_sql(
        "SELECT * FROM seguimiento_rq",
        conexion,
        parse_dates=["fecha_rq", "fecha_po", "fecha_ea", "fecha_factura"],
    )
    conexion.close()
    return df


@st.cache_data(ttl=300)  # misma frecuencia de refresco que los datos
def obtener_ultima_actualizacion():
    database_url = st.secrets["DATABASE_URL"]
    conexion = psycopg2.connect(database_url, sslmode="require")
    cur = conexion.cursor()
    cur.execute(
        "SELECT ultima_actualizacion FROM metadata_actualizacion "
        "ORDER BY id DESC LIMIT 1;"
    )
    resultado = cur.fetchone()
    conexion.close()
    return resultado[0] if resultado else None


df = cargar_datos()
ultima_actualizacion = obtener_ultima_actualizacion()

# ==========================================
# BARRA LATERAL: FILTROS (equivalentes a los
# "slicers" del dashboard original de Power BI)
# ==========================================

st.sidebar.title("📦 Filtros")

anios = sorted(df["anio"].dropna().unique(), reverse=True)
anio_sel = st.sidebar.multiselect("Año", anios, default=anios)

bodegas = sorted(df["bodega"].dropna().unique())
bodega_sel = st.sidebar.multiselect("Bodega", bodegas)

proveedores = sorted(df["proveedor"].dropna().unique())
proveedor_sel = st.sidebar.multiselect("Proveedor", proveedores)

requisitores = sorted(df["requisitor"].dropna().unique())
requisitor_sel = st.sidebar.multiselect("Requisitor", requisitores)

estados = sorted(df["estado_proceso"].dropna().unique())
estado_sel = st.sidebar.multiselect("Estado del proceso", estados)

numero_rq_busqueda = st.sidebar.text_input("Buscar N° de RQ")
numero_po_busqueda = st.sidebar.text_input("Buscar N° de PO")
item_busqueda = st.sidebar.text_input("Buscar descripción de ítem")

# ==========================================
# APLICAR FILTROS
# ==========================================

df_filtrado = df.copy()

if anio_sel:
    df_filtrado = df_filtrado[df_filtrado["anio"].isin(anio_sel)]
if bodega_sel:
    df_filtrado = df_filtrado[df_filtrado["bodega"].isin(bodega_sel)]
if proveedor_sel:
    df_filtrado = df_filtrado[df_filtrado["proveedor"].isin(proveedor_sel)]
if requisitor_sel:
    df_filtrado = df_filtrado[df_filtrado["requisitor"].isin(requisitor_sel)]
if estado_sel:
    df_filtrado = df_filtrado[df_filtrado["estado_proceso"].isin(estado_sel)]
if numero_rq_busqueda:
    df_filtrado = df_filtrado[
        df_filtrado["numero_rq"].str.contains(numero_rq_busqueda, case=False, na=False)
    ]
if numero_po_busqueda:
    df_filtrado = df_filtrado[
        df_filtrado["numero_po"].astype(str).str.contains(numero_po_busqueda, case=False, na=False)
    ]
if item_busqueda:
    df_filtrado = df_filtrado[
        df_filtrado["descripcion_item"].str.contains(item_busqueda, case=False, na=False)
    ]

# ==========================================
# ENCABEZADO Y TARJETAS (KPIs)
# ==========================================

st.title("Seguimiento de Requisiciones (RQ)")
st.caption(
    "Desde la requisición (RQ), pasando por la orden de compra (PO), "
    "la entrada al almacén (EA), hasta la factura."
)

if ultima_actualizacion:
    st.info(
        f"🕒 Última actualización de datos: "
        f"{ultima_actualizacion.strftime('%d/%m/%Y %I:%M %p')}"
    )
else:
    st.warning("🕒 Aún no hay registro de la última actualización de datos.")

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total de RQ (filtradas)", f"{df_filtrado['numero_rq'].nunique():,}")
col2.metric(
    "RQ sin PO todavía",
    f"{df_filtrado[df_filtrado['estado_proceso'] == 'RQ sin PO']['numero_rq'].nunique():,}",
)
col3.metric(
    "PO sin recibir (EA)",
    f"{df_filtrado[df_filtrado['estado_proceso'] == 'PO sin EA']['numero_po'].nunique():,}",
)
col4.metric(
    "EA sin facturar",
    f"{df_filtrado[df_filtrado['estado_proceso'] == 'EA sin Factura']['numero_ea'].nunique():,}",
)
col5.metric(
    "Urgentes (Alerta RQ→PO)",
    f"{(df_filtrado['alerta_rq_po'] == '🔴 URGENTE - Generar PO').sum():,}",
)

st.divider()

# ==========================================
# GRÁFICO DE DONA: Estado del proceso
# ==========================================

col_izq, col_der = st.columns([1, 1.4])

with col_izq:
    st.subheader("Estado del proceso")
    conteo_estado = (
        df_filtrado.drop_duplicates(subset=["numero_rq", "numero_po", "numero_ea", "numero_factura"])
        ["estado_proceso"]
        .value_counts()
        .reset_index()
    )
    conteo_estado.columns = ["Estado", "Cantidad"]

    fig = px.pie(
        conteo_estado,
        names="Estado",
        values="Cantidad",
        hole=0.5,
        color="Estado",
        color_discrete_map={
            "Factura recibida": "#1a7a3a",
            "RQ sin PO": "#e63946",
            "PO sin EA": "#f4a300",
            "EA sin Factura": "#3b82c4",
        },
    )
    fig.update_traces(textinfo="percent+value")
    st.plotly_chart(fig, use_container_width=True)

with col_der:
    st.subheader("Alertas RQ → PO")
    conteo_alerta = (
        df_filtrado.drop_duplicates(subset=["numero_rq"])
        ["alerta_rq_po"]
        .value_counts()
        .reset_index()
    )
    conteo_alerta.columns = ["Alerta", "Cantidad"]
    st.dataframe(conteo_alerta, use_container_width=True, hide_index=True)

st.divider()

# ==========================================
# TABLA: Alertas de tiempo
# ==========================================

st.subheader("⏱️ Alertas de tiempo por orden")

tabla_alertas = df_filtrado[
    [
        "numero_rq", "numero_po", "numero_ea", "numero_factura",
        "dias_rq_po", "alerta_rq_po",
        "dias_po_ea", "alerta_po_ea",
        "dias_ea_factura", "alerta_ea_factura",
    ]
].drop_duplicates(subset=["numero_rq", "numero_po", "numero_ea", "numero_factura"])

st.dataframe(
    tabla_alertas,
    use_container_width=True,
    hide_index=True,
    column_config={
        "numero_rq": "N° RQ",
        "numero_po": "N° PO",
        "numero_ea": "N° EA",
        "numero_factura": "N° Factura",
        "dias_rq_po": "Días RQ→PO",
        "alerta_rq_po": "Alerta RQ→PO",
        "dias_po_ea": "Días PO→EA",
        "alerta_po_ea": "Alerta PO→EA",
        "dias_ea_factura": "Días EA→Factura",
        "alerta_ea_factura": "Alerta EA→Factura",
    },
)

st.divider()

# ==========================================
# TABLA: Detalle completo
# ==========================================

st.subheader("📋 Detalle completo")

tabla_detalle = df_filtrado[
    [
        "numero_rq", "fecha_rq", "descripcion_item", "cantidad_rq",
        "requisitor", "bodega",
        "numero_po", "fecha_po", "cantidad_po", "proveedor",
        "numero_ea", "fecha_ea", "cantidad_ea",
        "numero_factura", "fecha_factura", "factura_proveedor",
        "alerta_diferencia_cantidad",
    ]
]

st.dataframe(
    tabla_detalle,
    use_container_width=True,
    hide_index=True,
    column_config={
        "numero_rq": "N° RQ",
        "fecha_rq": st.column_config.DateColumn("Fecha RQ", format="DD/MM/YYYY"),
        "descripcion_item": "Ítem",
        "cantidad_rq": "Cant. RQ",
        "requisitor": "Requisitor",
        "bodega": "Bodega",
        "numero_po": "N° PO",
        "fecha_po": st.column_config.DateColumn("Fecha PO", format="DD/MM/YYYY"),
        "cantidad_po": "Cant. PO",
        "proveedor": "Proveedor",
        "numero_ea": "N° EA",
        "fecha_ea": st.column_config.DateColumn("Fecha EA", format="DD/MM/YYYY"),
        "cantidad_ea": "Cant. EA",
        "numero_factura": "N° Factura",
        "fecha_factura": st.column_config.DateColumn("Fecha Factura", format="DD/MM/YYYY"),
        "factura_proveedor": "Factura proveedor",
        "alerta_diferencia_cantidad": "Alerta cantidad",
    },
)

st.caption(f"{len(tabla_detalle):,} filas mostradas de {len(df):,} totales.")

# ==========================================
# EXPORTAR A EXCEL
# ==========================================

@st.cache_data
def convertir_a_excel(dataframe):
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        dataframe.to_excel(writer, index=False, sheet_name="Seguimiento_RQ")
    return buffer.getvalue()

st.download_button(
    "📊 Exportar esta vista a Excel",
    data=convertir_a_excel(tabla_detalle),
    file_name="seguimiento_rq_filtrado.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
