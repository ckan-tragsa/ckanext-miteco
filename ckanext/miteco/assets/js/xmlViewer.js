/**
 * xmlViewer.js
 * Handles the Inspire XML viewer in the "Espacial Avanzado" form tab:
 *   - Syntax highlighting of the read-only XML preview
 *   - Version history panel (fetched from inspire_list_documents API)
 *   - "Load version" action with Bootstrap 5 confirmation modal
 *   - Download button for the current XML
 */

(function () {
    'use strict';

    // ── Helpers ──────────────────────────────────────────────────────────────

    function getDatasetId() {
        var el = document.getElementById('xml-text');
        return el ? el.getAttribute('data-dataset-id') : null;
    }

    function getDatasetName() {
        var el = document.getElementById('xml-text');
        return el ? el.getAttribute('data-dataset-name') : null;
    }

    /**
     * Extracts the site prefix (/catalog) from the current URL.
     * Works for both /catalog/dataset/name/edit and /catalog/es/dataset/name/edit
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

    function showDialog(title, message, type, onOk) {
        if (typeof window.showXmlDialog === 'function') {
            window.showXmlDialog(title, message, type, onOk);
        } else {
            if (message) alert(message);
            if (typeof onOk === 'function') onOk();
        }
    }

    // ── Syntax highlighting ──────────────────────────────────────────────────

    function initHighlight() {
        var preview = document.getElementById('xml-preview');
        if (!preview) return;

        var textarea = document.getElementById('xml-text');
        // The server renders the saved CKAN template; the hidden field holds
        // the original XML and must not replace that preview on page load.
        if (!preview.textContent.trim() && textarea && textarea.value) {
            preview.textContent = textarea.value;
        }
        if (preview.textContent.trim() && typeof hljs !== 'undefined') {
            hljs.highlightElement(preview);
        }

        // Keep preview in sync when the textarea value changes (after file import)
        if (textarea) {
            textarea.addEventListener('input', function () {
                preview.textContent = textarea.value;
                delete preview.dataset.highlighted;
                if (typeof hljs !== 'undefined') hljs.highlightElement(preview);
            });
        }

        // Keep preview in sync when the user selects a file to upload
        var fileInput = document.getElementById('field-xml-upload');
        if (fileInput) {
            fileInput.addEventListener('change', function () {
                if (fileInput.files && fileInput.files.length > 0) {
                    var reader = new FileReader();
                    reader.onload = function () {
                        preview.textContent = reader.result;
                        if (textarea) textarea.value = reader.result;
                        delete preview.dataset.highlighted;
                        if (typeof hljs !== 'undefined') hljs.highlightElement(preview);
                    };
                    reader.readAsText(fileInput.files[0]);
                }
            });
        }
    }

    // ── Download button ──────────────────────────────────────────────────────

    function initDownloadButton() {
        var btn = document.getElementById('xml-download-btn');
        if (!btn) return;

        btn.addEventListener('click', function () {
            var textarea = document.getElementById('xml-text');
            var preview = document.getElementById('xml-preview');
            var content = (preview && preview.textContent) || (textarea && textarea.value);
            if (!content || !content.trim()) return;

            var blob = new Blob([content], { type: 'application/xml' });
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = (getDatasetName() || 'metadata') + '.xml';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        });
    }

    // ── Version history ──────────────────────────────────────────────────────

    /**
     * Formatea fecha ISO normalizando timestamps UTC a la hora local del navegador.
     */
    function formatDate(isoString) {
        if (!isoString) return '—';
        var s = String(isoString).trim();
        // Si no tiene zona horaria ('Z' o offset ±HH:mm), se asume UTC para coincidir con la BD
        if (s && !s.endsWith('Z') && !/[+-]\d{2}:?\d{2}$/.test(s)) {
            s += 'Z';
        }
        var d = new Date(s);
        if (isNaN(d.getTime())) return isoString;
        return d.toLocaleString(undefined, {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    }

    function loadVersion(datasetName, hash) {
        var prefix = getSitePrefix();
        var url = window.location.origin +
            prefix +
            '/dataset/' + encodeURIComponent(datasetName) + '/xml/' + hash;

        fetch(url)
            .then(function (r) {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.text();
            })
            .then(function (xml) {
                var textarea = document.getElementById('xml-text');
                if (!textarea) return;
                textarea.removeAttribute('readonly');
                textarea.value = xml;

                // Refresh preview
                var preview = document.getElementById('xml-preview');
                if (preview) {
                    preview.textContent = xml;
                    delete preview.dataset.highlighted;
                    if (typeof hljs !== 'undefined') hljs.highlightElement(preview);
                }

                showDialog(
                    'Versión cargada',
                    'Se ha cargado la versión histórica seleccionada en el editor y en la previsualización.',
                    'success'
                );
            })
            .catch(function (err) {
                showDialog('Error al cargar la versión', err.message, 'error');
            });
    }

    function renderHistory(versions, datasetName) {
        var panel = document.getElementById('xml-history-panel');
        var currentHash = panel ? panel.getAttribute('data-current-hash') : null;
        var tbody = document.getElementById('xml-history-tbody');
        var empty = document.getElementById('xml-history-empty');
        if (!tbody) return;

        if (!versions || versions.length === 0) {
            if (empty) empty.style.display = '';
            tbody.innerHTML = '';
            return;
        }

        if (empty) empty.style.display = 'none';
        tbody.innerHTML = '';

        versions.forEach(function (v, index) {
            var tr = document.createElement('tr');
            var isCurrent = (currentHash && v.md5 === currentHash) || (!currentHash && index === 0);
            var label = isCurrent ?
                ' <span class="badge rounded-pill text-bg-light border ms-1" style="color:var(--sct-primary-color)!important">actual</span>' :
                ' <span class="badge rounded-pill text-bg-light border text-muted ms-1">versión</span>';
            var hashStr = v.md5 ? v.md5.substring(0, 12) + '…' : '—';
            tr.innerHTML =
                '<td>' + formatDate(v.time) + label + '</td>' +
                '<td><code style="font-size:0.75em">' + hashStr + '</code></td>' +
                '<td>' +
                    '<button type="button" class="btn btn-sm btn-outline-secondary btn-load-version" ' +
                    'data-hash="' + v.md5 + '">' +
                    '<i class="fa fa-history me-1"></i> Cargar' +
                    '</button>' +
                '</td>';

            tr.querySelector('.btn-load-version').addEventListener('click', function () {
                var hashToLoad = this.getAttribute('data-hash');
                var confirmModalEl = document.getElementById('modal-xml-version-confirm');

                if (confirmModalEl && typeof bootstrap !== 'undefined') {
                    var confirmModal = bootstrap.Modal.getOrCreateInstance(confirmModalEl);
                    var confirmBtn = document.getElementById('btn-confirm-load-version');
                    if (confirmBtn) {
                        var newConfirmBtn = confirmBtn.cloneNode(true);
                        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
                        newConfirmBtn.addEventListener('click', function() {
                            confirmModal.hide();
                            loadVersion(datasetName, hashToLoad);
                        });
                    }
                    confirmModal.show();
                } else {
                    loadVersion(datasetName, hashToLoad);
                }
            });

            tbody.appendChild(tr);
        });
    }

    function initVersionHistory() {
        var panel = document.getElementById('xml-history-panel');
        if (!panel) return;

        var datasetId   = panel.getAttribute('data-dataset-id');
        var datasetName = panel.getAttribute('data-dataset-name');
        var targetId    = datasetId || datasetName;
        if (!targetId || targetId === 'new' || targetId === 'None') {
            panel.style.display = 'none';
            return;
        }

        var prefix = getSitePrefix();
        var apiUrl = prefix + '/api/3/action/inspire_list_documents?id=' + encodeURIComponent(targetId);

        fetch(apiUrl)
            .then(function (r) {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(function (data) {
                if (data.success && data.result) {
                    renderHistory(data.result, datasetName || datasetId);
                    panel.style.display = '';
                } else {
                    renderHistory([], datasetName || datasetId);
                }
            })
            .catch(function (err) {
                console.warn('Could not load inspire XML version history:', err);
                renderHistory([], datasetName || datasetId);
            });
    }

    // ── Init ─────────────────────────────────────────────────────────────────

    document.addEventListener('DOMContentLoaded', function () {
        initHighlight();
        initDownloadButton();
        initVersionHistory();
    });

}());
