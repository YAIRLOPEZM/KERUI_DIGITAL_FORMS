const canvas = document.getElementById("firmaTecnico");

const signaturePad = new SignaturePad(canvas);

document
.getElementById("limpiarFirma")
.addEventListener("click", function(){

    signaturePad.clear();

});

const firmaTecnico = new SignaturePad(
    document.getElementById("firmaTecnico")
);

const firmaSupervisor = new SignaturePad(
    document.getElementById("firmaSupervisor")
);

const firmaCoordinador = new SignaturePad(
    document.getElementById("firmaCoordinador")
);

document
.getElementById("limpiarSupervisor")
.onclick = () => firmaSupervisor.clear();

document
.getElementById("limpiarCoordinador")
.onclick = () => firmaCoordinador.clear();

// =============================
// NUEVO: SUBIR IMAGEN DE FIRMA
// =============================
// Función reutilizable: conecta un botón + un <input type="file">
// a un SignaturePad específico, para poder usar una imagen ya
// guardada en vez de dibujar con el dedo o el mouse.

function configurarSubidaImagen(pad, idBoton, idInputArchivo) {

    const boton = document.getElementById(idBoton);
    const inputArchivo = document.getElementById(idInputArchivo);

    if (!boton || !inputArchivo) {
        return;
    }

    boton.addEventListener("click", function () {
        inputArchivo.click();
    });

    inputArchivo.addEventListener("change", function (evento) {

        const archivo = evento.target.files[0];
        if (!archivo) return;

        if (!archivo.type.startsWith("image/")) {
            alert("Por favor selecciona un archivo de imagen (PNG o JPG).");
            return;
        }

        const lector = new FileReader();

        lector.onload = function (e) {

            const imagen = new Image();

            imagen.onload = function () {

                const canvasFirma = pad.canvas;
                const ratio = Math.max(window.devicePixelRatio || 1, 1);
                const anchoCanvas = canvasFirma.width / ratio;
                const altoCanvas = canvasFirma.height / ratio;

                // Mantiene la proporción de la imagen y la centra,
                // sin deformarla, dentro del recuadro de firma.
                const escala = Math.min(
                    anchoCanvas / imagen.width,
                    altoCanvas / imagen.height
                );
                const anchoDestino = imagen.width * escala;
                const altoDestino = imagen.height * escala;
                const x = (anchoCanvas - anchoDestino) / 2;
                const y = (altoCanvas - altoDestino) / 2;

                pad.clear();
                const ctx = canvasFirma.getContext("2d");
                ctx.drawImage(imagen, x, y, anchoDestino, altoDestino);

                // Le avisamos al SignaturePad que este es su nuevo
                // contenido, para que isEmpty() y toDataURL() lo
                // reconozcan igual que si se hubiera dibujado a mano.
                pad.fromDataURL(canvasFirma.toDataURL());
            };

            imagen.src = e.target.result;
        };

        lector.readAsDataURL(archivo);
    });
}

configurarSubidaImagen(firmaTecnico, "subirFirmaTecnico", "archivoFirmaTecnico");
configurarSubidaImagen(firmaSupervisor, "subirFirmaSupervisor", "archivoFirmaSupervisor");
configurarSubidaImagen(firmaCoordinador, "subirFirmaCoordinador", "archivoFirmaCoordinador");

// =============================
// GUARDAR FIRMAS ANTES DEL SUBMIT
// =============================

document.querySelector("form").addEventListener("submit", function(){

    document.getElementById("firma_tecnico").value =
        firmaTecnico.toDataURL();

    document.getElementById("firma_supervisor").value =
        firmaSupervisor.isEmpty()
            ? ""
            : firmaSupervisor.toDataURL();

    document.getElementById("firma_coordinador").value =
        firmaCoordinador.isEmpty()
            ? ""
            : firmaCoordinador.toDataURL();

});
