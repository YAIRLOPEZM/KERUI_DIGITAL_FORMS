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