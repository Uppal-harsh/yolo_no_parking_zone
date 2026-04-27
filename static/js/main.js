document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const previewArea = document.getElementById('preview-area');
    const imagePreview = document.getElementById('image-preview');
    const loader = document.getElementById('loader');
    const violationBody = document.getElementById('violation-body');
    const btnRun = document.getElementById('btn-run');

    let activeViolations = [];

const API_BASE = "http://localhost:8080";

    // Fetch initial status from server
    async function fetchLogs() {
        console.log("Checking for new logs...");
        try {
            const response = await fetch(`${API_BASE}/logs`);
            const data = await response.json();
            console.log("Logs received:", data.logs);
            data.logs.forEach(log => {
                // If already in activeViolations, skip
                if (activeViolations.find(v => v.plate === log.plate)) return;

                console.log("Adding new violation to UI:", log.plate);
                const violation = {
                    id: Math.random().toString(36).substr(2, 9),
                    plate: log.plate,
                    phone: log.phone,
                    startTime: Date.now() - (log.elapsed * 1000),
                    status: log.status,
                    smsSent: log.status === 'CHALLANED'
                };
                activeViolations.push(violation);
                addViolationRow(violation);
            });
        } catch (e) { console.error("Fetch error:", e); }
    }
    fetchLogs();
    setInterval(fetchLogs, 2000); // Check every 2 seconds

    // Helper to add row
    function addViolationRow(v) {
        const row = document.createElement('tr');
        row.id = `row-${v.id}`;
        row.innerHTML = `
            <td class="plate-code">${v.plate}</td>
            <td class="phone-num">${v.phone}</td>
            <td><span id="timer-${v.id}">0:00</span> elapsed</td>
            <td><span id="status-${v.id}" class="badge">${v.status}</span></td>
            <td><button class="btn-view" onclick="removeViolation('${v.id}')">Clear</button></td>
        `;
        violationBody.prepend(row);
    }

    // Run Button Logic (Loop Mode)
    let detectionInterval = null;

    btnRun.addEventListener('click', async () => {
        if (detectionInterval) {
            // Stop Loop
            clearInterval(detectionInterval);
            detectionInterval = null;
            btnRun.innerText = "Run Detection Loop";
            btnRun.style.background = "#06b6d4";
            console.log("Detection loop stopped.");
        } else {
            // Start Loop
            btnRun.innerText = "Stop Detection Loop (Every 10s)";
            btnRun.style.background = "#ef4444";
            
            console.log("Detection loop started.");
            
            // Run once immediately
            runSingleDetection();
            
            // Set interval
            detectionInterval = setInterval(runSingleDetection, 10000); // 10 seconds
        }
    });

    async function runSingleDetection() {
        console.log("Triggering 10s capture...");
        try {
            const response = await fetch(`${API_BASE}/api/run-simulation`);
            const data = await response.json();
            
            if (response.ok && data.detections) {
                displayResults(data.detections);
                if (data.image_url) {
                    imagePreview.src = `${API_BASE}${data.image_url}`;
                    dropZone.style.display = 'none';
                    previewArea.style.display = 'block';
                }
            } else {
                console.error(`Loop Error: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Loop Request failed:', error);
        }
    }

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
            const response = await fetch(`${API_BASE}/upload`, {
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
            console.log('No license plates detected.');
            return;
        }

        detections.forEach(det => {
            // Check if already tracking this plate
            if (activeViolations.find(v => v.plate === det.plate)) return;

            const id = Math.random().toString(36).substr(2, 9);
            const violation = {
                id: id,
                plate: det.plate,
                phone: det.phone,
                startTime: Date.now(),
                status: 'Checking',
                smsSent: false
            };
            
            activeViolations.push(violation);
            addViolationRow(violation);
        });
    }

    // Tick function to update status every second
    setInterval(() => {
        activeViolations.forEach(async v => {
            const elapsed = Math.floor((Date.now() - v.startTime) / 1000);
            const timerElement = document.getElementById(`timer-${v.id}`);
            const statusElement = document.getElementById(`status-${v.id}`);

            if (timerElement) timerElement.innerText = formatTime(elapsed);
            
            if (elapsed >= 300 && !v.smsSent) { // 5 minutes
                v.smsSent = true;
                v.status = 'CHALLANED';
                if (statusElement) {
                    statusElement.innerText = 'Challan Sent';
                    statusElement.className = 'badge badge-danger';
                }
                
                // Trigger Backend SMS
                try {
                    await fetch(`${API_BASE}/api/send-sms`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({
                            plate: v.plate,
                            phone: v.phone,
                            message: `E-Challan: Vehicle ${v.plate} has been parked in a No-Parking zone for over 5 minutes.`
                        })
                    });
                } catch (e) { console.error("Failed to send SMS trigger"); }
            } else if (elapsed >= 180 && v.status === 'Checking') { // 3 minutes warning
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
