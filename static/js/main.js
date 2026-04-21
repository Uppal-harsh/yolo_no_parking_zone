document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const previewArea = document.getElementById('preview-area');
    const imagePreview = document.getElementById('image-preview');
    const loader = document.getElementById('loader');
    const violationBody = document.getElementById('violation-body');

    let activeViolations = [];

    // Drag and Drop handlers
    dropZone.addEventListener('click', () => fileInput.click());

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.style.borderColor = '#06b6d4';
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.style.borderColor = 'rgba(255, 255, 255, 0.08)';
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        const files = e.dataTransfer.files;
        if (files.length > 0) handleFile(files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) handleFile(e.target.files[0]);
    });

    async function handleFile(file) {
        // Show Preview
        const reader = new FileReader();
        reader.onload = (e) => {
            imagePreview.src = e.target.result;
            dropZone.style.display = 'none';
            previewArea.style.display = 'block';
            loader.style.display = 'block';
        };
        reader.readAsDataURL(file);

        // Upload to server
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            loader.style.display = 'none';
            displayResults(data.detections);
        } catch (error) {
            console.error('Upload failed:', error);
            loader.style.display = 'none';
            alert('Processing failed. Please check server logs.');
        }
    }

    function displayResults(detections) {
        if (detections.length === 0) {
            alert('No license plates detected.');
            return;
        }

        detections.forEach(det => {
            const id = Math.random().toString(36).substr(2, 9);
            const violation = {
                id: id,
                plate: det.plate,
                startTime: Date.now(),
                status: 'SAFE'
            };
            
            activeViolations.push(violation);
            
            const row = document.createElement('tr');
            row.id = `row-${id}`;
            row.innerHTML = `
                <td class="plate-code">${det.plate}</td>
                <td><span id="timer-${id}">0:00</span> elapsed</td>
                <td><span id="status-${id}" class="badge" style="background: rgba(16, 185, 129, 0.1); color: #10b981;">Checking</span></td>
                <td><button class="btn-view" onclick="removeViolation('${id}')">Clear</button></td>
            `;
            violationBody.prepend(row);
        });
    }

    // Tick function to update status every second
    setInterval(() => {
        activeViolations.forEach(v => {
            const elapsed = Math.floor((Date.now() - v.startTime) / 1000);
            const timerElement = document.getElementById(`timer-${v.id}`);
            const statusElement = document.getElementById(`status-${v.id}`);

            if (timerElement) timerElement.innerText = formatTime(elapsed);
            
            if (elapsed >= 420) { // 7 minutes
                v.status = 'CHALLANED';
                if (statusElement) {
                    statusElement.innerText = 'Challan';
                    statusElement.className = 'badge badge-danger';
                }
            } else if (elapsed >= 300) { // 5 minutes
                v.status = 'WARNING';
                if (statusElement) {
                    statusElement.innerText = 'Warning';
                    statusElement.className = 'badge badge-warning';
                }
            }
        });
    }, 1000);

    function formatTime(sec) {
        const m = Math.floor(sec / 60);
        const s = sec % 60;
        return `${m}:${s.toString().padStart(2, '0')}`;
    }

    window.removeViolation = (id) => {
        activeViolations = activeViolations.filter(v => v.id !== id);
        const row = document.getElementById(`row-${id}`);
        if (row) row.remove();
    };
});
