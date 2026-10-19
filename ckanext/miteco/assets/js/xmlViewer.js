/**
 * xmlViewer.js
 * Handles the Inspire XML viewer in the "Espacial Avanzado" form tab:
 *   - Syntax highlighting of the read-only XML preview
 *   - Version history panel (fetched from inspire_list_documents API)
 *   - "Load version" action (fetches XML from the blueprint endpoint)
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

    // ── Syntax highlighting ──────────────────────────────────────────────────

    function initHighlight() {
        var preview = document.getElementById('xml-preview');
        if (!preview || typeof hljs === 'undefined') return;

        var textarea = document.getElementById('xml-text');
        if (textarea && textarea.value) {
            preview.textContent = textarea.value;
            hljs.highlightElement(preview);
        }

        // Keep preview in sync when the textarea value changes (after file import)
        if (textarea) {
            textarea.addEventListener('input', function () {
                preview.textContent = textarea.value;
                delete preview.dataset.highlighted;
                hljs.highlightElement(preview);
            });
        }
    }

    // ── Download button ──────────────────────────────────────────────────────

    function initDownloadButton() {
        var btn = document.getElementById('xml-download-btn');
        if (!btn) return;

        btn.addEventListener('click', function () {
            var textarea = document.getElementById('xml-text');
            if (!textarea || !textarea.value.trim()) return;

            var blob = new Blob([textarea.value], { type: 'application/xml' });
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

    function formatDate(isoString) {
        if (!isoString) return '—';
        var d = new Date(isoString);
        return d.toLocaleString();
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
                if (preview && typeof hljs !== 'undefined') {
                    preview.textContent = xml;
                    delete preview.dataset.highlighted;
                    hljs.highlightElement(preview);
                }
            })
            .catch(function (err) {
                alert('Error al cargar la versión: ' + err.message);
            });
    }

    function renderHistory(versions, datasetName) {
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
            var label = index === 0 ? ' <span class="badge bg-success ms-1">actual</span>' : '';
            var hashStr = v.md5 ? v.md5.substring(0, 12) + '…' : '—';
            tr.innerHTML =
                '<td>' + formatDate(v.time) + label + '</td>' +
                '<td><code style="font-size:0.75em">' + hashStr + '</code></td>' +
                '<td>' +
                    '<button type="button" class="btn btn-sm btn-outline-secondary" ' +
                    'data-hash="' + v.md5 + '">' +
                    '<i class="fa fa-history"></i> Cargar' +
                    '</button>' +
                '</td>';

            tr.querySelector('button').addEventListener('click', function () {
                if (!confirm('¿Cargar esta versión? Se reemplazará el contenido actual del editor.')) return;
                loadVersion(datasetName, this.getAttribute('data-hash'));
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
        if (!targetId || targetId === 'new') return;  // new dataset, no versions yet

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
                }
            })
            .catch(function (err) {
                console.warn('Could not load inspire XML version history:', err);
            });
    }

    // ── Init ─────────────────────────────────────────────────────────────────

    document.addEventListener('DOMContentLoaded', function () {
        initHighlight();
        initDownloadButton();
        initVersionHistory();
    });

}());
