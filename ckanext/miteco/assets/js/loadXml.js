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

async function loadXml() {
    var fileInput = document.getElementById('field-xml-upload');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        alert('Please select an XML file first.');
        return;
    }
    var file = fileInput.files[0];
    var reader = new FileReader();
    reader.addEventListener('load', function() {
        var textarea = document.getElementById('xml-text');
        if (textarea) {
            textarea.value = reader.result;
        }
        // Refresh the syntax-highlighted preview
        var preview = document.getElementById('xml-preview');
        if (preview) {
            preview.textContent = reader.result;
            if (typeof hljs !== 'undefined') {
                delete preview.dataset.highlighted;
                hljs.highlightElement(preview);
            }
        }
    });
    reader.readAsText(file);
}