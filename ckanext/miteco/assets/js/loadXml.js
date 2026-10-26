/**
 * loadXml.js
 * Gestiona la carga e importación de archivos XML INSPIRE en el portal:
 *  - Muestra modales estilizados con la identidad corporativa de MITECO.
 *  - Valida la selección del archivo.
 *  - Envía la solicitud al endpoint de subida.
 *  - Notifica el resultado mediante modales accesibles y coherentes con CKAN.
 */

/**
 * Modal genérico de aviso / diálogo estilizado con la identidad de MITECO.
 * @param {string} title Título del modal.
 * @param {string} message Contenido del mensaje explicativo.
 * @param {'info'|'success'|'warning'|'error'} [type='info'] Tipo de mensaje para icono y colores.
 * @param {function} [onOk] Callback a ejecutar al presionar 'Aceptar' o cerrar.
 */
window.showXmlDialog = function(title, message, type, onOk) {
    var modalEl = document.getElementById('modal-xml-dialog');
    if (!modalEl || typeof bootstrap === 'undefined') {
        if (message) alert(message);
        if (typeof onOk === 'function') onOk();
        return;
    }

    var titleEl = document.getElementById('modal-xml-dialog-title');
    var msgEl = document.getElementById('modal-xml-dialog-message');
    var iconEl = document.getElementById('modal-xml-dialog-icon');
    var okBtn = document.getElementById('modal-xml-dialog-ok-btn');

    if (titleEl) titleEl.textContent = title || 'Aviso';
    if (msgEl) msgEl.textContent = message || '';

    if (iconEl) {
        iconEl.className = 'me-2 fa ';
        if (type === 'success') {
            iconEl.className += 'fa-check-circle text-success';
        } else if (type === 'error') {
            iconEl.className += 'fa-times-circle text-danger';
        } else if (type === 'warning') {
            iconEl.className += 'fa-exclamation-triangle text-warning';
        } else {
            iconEl.className += 'fa-info-circle text-primary';
        }
    }

    var modal = bootstrap.Modal.getOrCreateInstance(modalEl);

    if (okBtn) {
        var newOkBtn = okBtn.cloneNode(true);
        okBtn.parentNode.replaceChild(newOkBtn, okBtn);
        newOkBtn.addEventListener('click', function() {
            modal.hide();
            if (typeof onOk === 'function') {
                onOk();
            }
        });
    }

    modal.show();
};

/**
 * [RESERVADO] Función para habilitar edición desde el modal de advertencia #xmlWarn.
 * Se conserva por si se requiere reactivar la modal de confirmación en futuras implementaciones.
 */
function enableXmlEdit() {
    document.querySelectorAll('.multi-collapse').forEach(function(el) {
        var instance = bootstrap.Collapse.getOrCreateInstance(el, { toggle: false });
        if (el.classList.contains('show')) {
            instance.hide();
        } else {
            instance.show();
        }
    });

    var modalEl = document.getElementById('xmlWarn');
    if (modalEl && typeof bootstrap !== 'undefined') {
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
 * Punto de entrada al hacer clic en el botón de importación ("import xml" / #loadButton).
 * Valida la selección del archivo y solicita confirmación mediante modal corporativo.
 */
function loadXml() {
    var fileInput = document.getElementById('field-xml-upload');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        window.showXmlDialog(
            'Archivo no seleccionado',
            'Por favor, seleccione primero un archivo XML desde su equipo antes de iniciar la importación.',
            'warning'
        );
        return;
    }

    // Modal corporativo de confirmación de importación
    var confirmModalEl = document.getElementById('modal-xml-import-confirm');
    if (confirmModalEl && typeof bootstrap !== 'undefined') {
        var confirmModal = bootstrap.Modal.getOrCreateInstance(confirmModalEl);
        var confirmBtn = document.getElementById('btn-confirm-import-action');
        if (confirmBtn) {
            var newConfirmBtn = confirmBtn.cloneNode(true);
            confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
            newConfirmBtn.addEventListener('click', function() {
                confirmModal.hide();
                executeXmlImport();
            });
        }
        confirmModal.show();
    } else {
        executeXmlImport();
    }
}

/**
 * Ejecuta la llamada asíncrona de subida e importación del XML.
 */
async function executeXmlImport() {
    var fileInput = document.getElementById('field-xml-upload');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) return;

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

    // Feedback visual en el botón de acción
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
    var complementCheckbox = document.getElementById('field-xml-complement');
    if (complementCheckbox) {
        formData.append('overwrite', complementCheckbox.checked ? 'false' : 'true');
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
                throw new Error('El servidor devolvió un error HTTP ' + response.status + ' (' + response.statusText + '). Compruebe los permisos y la configuración.');
            }
            throw new Error('Respuesta no válida del servidor.');
        }

        if (result.success) {
            var warnings = Array.isArray(result.warnings) ? result.warnings : [];
            var warningText = warnings.map(function (warning) {
                return warning.field + ': ' + warning.message + (warning.value ? ' (' + warning.value + ')' : '');
            }).join('\n');
            if (statusEl) {
                statusEl.className = 'small ms-2 fw-bold ' + (warnings.length ? 'text-warning' : 'text-success');
                statusEl.textContent = warnings.length ? 'Importación completada con avisos: ' + warningText : '¡Importación completada con éxito!';
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

            // Modal de éxito y redirección
            var pkgIdentifier = result.package || targetId;
            var prefix = getSitePrefix();
            var targetRedirect = pkgIdentifier ?
                (window.location.origin + prefix + '/dataset/' + encodeURIComponent(pkgIdentifier)) :
                (window.location.origin + prefix + '/dataset');

            window.showXmlDialog(
                warnings.length ? 'Importación completada con avisos' : 'Importación completada con éxito',
                warnings.length ? warningText : 'El archivo XML INSPIRE ha sido validado e importado correctamente en el conjunto de datos.',
                warnings.length ? 'warning' : 'success',
                function() {
                    window.location.href = targetRedirect;
                }
            );

        } else {
            var msg = result.msg || 'No se pudo validar o procesar el archivo XML.';
            if (statusEl) {
                statusEl.className = 'small ms-2 text-danger fw-bold';
                statusEl.textContent = 'Error al importar: ' + msg;
            }
            window.showXmlDialog('Error en validación INSPIRE', msg, 'error');
        }
    } catch (err) {
        if (statusEl) {
            statusEl.className = 'small ms-2 text-danger fw-bold';
            statusEl.textContent = 'Error: ' + err.message;
        }
        window.showXmlDialog('Error de conexión', 'No se pudo completar la importación: ' + err.message, 'error');
    } finally {
        if (loadBtn) {
            loadBtn.disabled = false;
            loadBtn.innerHTML = '<i class="fa fa-upload" aria-hidden="true"></i> ' + (window._ ? _('import xml') : 'Importar XML');
        }
    }
}
