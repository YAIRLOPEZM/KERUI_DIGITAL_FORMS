import os

from playwright.sync_api import sync_playwright


def generar_pdf(numero_ot, html):

    # ==========================================
    # CREAR CARPETA PDF
    # ==========================================

    os.makedirs("pdf", exist_ok=True)

    # ==========================================
    # RUTA DEL PDF
    # ==========================================

    ruta_pdf = os.path.abspath(
        os.path.join(
            "pdf",
            f"{numero_ot}.pdf"
        )
    )

    # ==========================================
    # GENERAR PDF CON PLAYWRIGHT (CHROMIUM)
    # ==========================================
    # Playwright trae su propio Chromium instalado
    # (via "playwright install chromium"), así que
    # esto funciona igual en Windows y en Linux
    # (Render), sin depender de que exista Microsoft
    # Edge en el sistema.
    #
    # El HTML que llega aquí ya trae el CSS y las
    # imágenes (logo y firma) incrustados directamente
    # en el propio HTML, así que no depende de rutas de
    # archivos ni de un servidor web corriendo.

    with sync_playwright() as p:

        navegador = p.chromium.launch()

        pagina = navegador.new_page()

        pagina.set_content(html, wait_until="networkidle")

        pagina.pdf(
            path=ruta_pdf,
            format="A4",
            print_background=True,
            margin={
                "top": "0mm",
                "bottom": "0mm",
                "left": "0mm",
                "right": "0mm"
            }
        )

        navegador.close()

    print(
        f"✅ PDF generado correctamente: {ruta_pdf}"
    )

    return ruta_pdf
