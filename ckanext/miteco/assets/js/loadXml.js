/**
 * [RESERVADO] Función para habilitar edición desde el modal de advertencia #xmlWarn.
 * Se conserva por si se requiere reactivar la modal de confirmación en futuras implementaciones.
 */
function enableXmlEdit() {
    // Manual editing is disabled — XML can only be updated via file import.
    // The highlighted preview stays visible; only the upload section is toggled.

    // Toggle all .multi-collapse elements using Bootstrap API
    document.querySelectorAll('.multi-collapse').forEach(function(el) {
        var instance = bootstrap.Collapse.getOrCreateInstance(el, { toggle: false });
        if (el.classList.contains('show')) {
            instance.hide();
        } else {
            instance.show();
        }
    });

    // Close the warning modal
    var modalEl = document.getElementById('xmlWarn');
    if (modalEl) {
        var modal = bootstrap.Modal.getInstance(modalEl);
        if (modal) modal.hide();
    }
}

/**
 * Extrae el prefijo del sitio (/catalog o similar) según la URL actual de forma robusta.
 */
function getSitePrefix() {
    var path = window.location.pathname;
    var inspirePos = path.indexOf('/inspire/');
    if (inspirePos >= 0) {
        path = path.substring(0, inspirePos);
    } else {
        var datasetPos = path.indexOf('/dataset/');
        if (datasetPos >= 0) {
            path = path.substring(0, datasetPos);
        }
    }
    return path.replace(/\/[a-z]{2}$/, '').replace(/\/$/, '');
}

/**
 * Importa el fichero XML seleccionado ejecutando el mismo flujo que upload_inspire.py:
 *  - Envía el XML al endpoint interno /inspire/dataset/<id>/upload-xml
 *  - En backend: valida INSPIRE, guarda en inspire_xml, ejecuta xsl_fill() y actualiza el dataset.
 *  - Al terminar: refresca el preview y recarga la página para mostrar los metadatos actualizados.
 */
async function loadXml() {
    var fileInput = document.getElementById('field-xml-upload');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        alert('Por favor, selecciona primero un archivo XML.');
        return;
    }

    var file = fileInput.files[0];
    var loadBtn = document.getElementById('loadButton');
    var statusEl = document.getElementById('xml-upload-status');
    var textarea = document.getElementById('xml-text');

    var datasetId = textarea ? textarea.getAttribute('data-dataset-id') : '';
    var datasetName = textarea ? textarea.getAttribute('data-dataset-name') : '';
    var datasetOrg = textarea ? textarea.getAttribute('data-dataset-org') : '';
    var targetId = datasetName || datasetId || '';
    if (targetId === 'new') {
        targetId = '';
    }

    // Feedback visual de inicio
    if (loadBtn) {
        loadBtn.disabled = true;
        loadBtn.innerHTML = '<i class="fa fa-spinner fa-spin" aria-hidden="true"></i> ' + (window._ ? _('Importing...') : 'Importando...');
    }
    if (statusEl) {
        statusEl.style.display = 'inline';
        statusEl.className = 'small ms-2 text-primary';
        statusEl.textContent = window._ ? _('Validating and processing INSPIRE XML...') : 'Validando y procesando XML INSPIRE...';
    }

    var formData = new FormData();
    formData.append('file', file);
    if (targetId) {
        formData.append('id', targetId);
    }
    if (datasetOrg) {
        formData.append('org', datasetOrg);
    }

    var uploadSection = document.getElementById('xmlUploadSection');
    var uploadUrl = uploadSection ? uploadSection.getAttribute('data-upload-url') : '';
    if (!uploadUrl) {
        var prefix = getSitePrefix();
        uploadUrl = window.location.origin + prefix + (targetId ? ('/inspire/dataset/' + encodeURIComponent(targetId) + '/upload-xml') : '/inspire/dataset/upload-xml');
    }

    try {
        var response = await fetch(uploadUrl, {
            method: 'POST',
            body: formData,
            credentials: 'same-origin'
        });

        var textResponse = await response.text();
        var result;
        try {
            result = JSON.parse(textResponse);
        } catch (jsonErr) {
            if (!response.ok) {
                throw new Error('El servidor devolvió un error HTTP ' + response.status + ' (' + response.statusText + '). Comprueba los permisos y que el contenedor esté reiniciado.');
            }
            throw new Error('Respuesta no válida del servidor (no es JSON válido).');
        }

        if (result.success) {
            if (statusEl) {
                statusEl.className = 'small ms-2 text-success fw-bold';
                statusEl.textContent = '¡Importación completada con éxito!';
            }

            // Actualizar vista previa local
            var reader = new FileReader();
            reader.onload = function() {
                if (textarea) textarea.value = reader.result;
                var preview = document.getElementById('xml-preview');
                if (preview) {
                    preview.textContent = reader.result;
                    if (typeof hljs !== 'undefined') {
                        delete preview.dataset.highlighted;
                        hljs.highlightElement(preview);
                    }
                }
            };
            reader.readAsText(file);

            // Salir del formulario y redirigir a la vista del dataset
            setTimeout(function() {
                var pkgIdentifier = result.package || targetId;
                var prefix = getSitePrefix();
                if (pkgIdentifier) {
                    window.location.href = window.location.origin + prefix + '/dataset/' + encodeURIComponent(pkgIdentifier);
                } else {
                    window.location.href = window.location.origin + prefix + '/dataset';
                }
            }, 500);

        } else {
            var msg = result.msg || 'No se pudo validar o procesar el XML.';
            if (statusEl) {
                statusEl.className = 'small ms-2 text-danger fw-bold';
                statusEl.textContent = 'Error al importar: ' + msg;
            }
            alert('Error al importar el XML INSPIRE:\n' + msg);
        }
    } catch (err) {
        if (statusEl) {
            statusEl.className = 'small ms-2 text-danger fw-bold';
            statusEl.textContent = 'Error de conexión: ' + err.message;
        }
        alert('Error de conexión al importar el XML: ' + err.message);
    } finally {
        if (loadBtn) {
            loadBtn.disabled = false;
            loadBtn.innerHTML = '<i class="fa fa-upload" aria-hidden="true"></i> ' + (window._ ? _('import xml') : 'Importar XML');
        }
    }
}