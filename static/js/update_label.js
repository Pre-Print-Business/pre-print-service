
document.getElementById('fileInput').addEventListener('change', function() {
    var fileName = "";
    if (this.files && this.files.length > 1) {
        fileName = (this.getAttribute('data-multiple-caption') || '').replace('{count}', this.files.length);
    } else if (this.value) {
        fileName = this.value.split('\\').pop();
    }

    if (fileName) {
        document.getElementById('fileLabel').textContent = fileName;
    } else {
        document.getElementById('fileLabel').textContent = "파일 선택";
    }
});
