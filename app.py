import cv2
import numpy as np
import os
import time
import shutil
from fastapi import FastAPI, UploadFile, File, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from ultralytics import YOLO
import easyocr

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for Live Server (port 5500)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allows all origins for debugging
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("check", exist_ok=True) # Ensure check folder exists
os.makedirs("templates", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/check", StaticFiles(directory="check"), name="check") # Mount check folder
templates = Jinja2Templates(directory="templates")

# Initialize Models
print("Loading YOLOv8 model...")
model = YOLO('best.pt')
print("Initializing EasyOCR...")
reader = easyocr.Reader(['en'])

# Database to store plate to phone number mapping
# In a real app, this would be a SQL database
PLATE_DB = {
    "MH14TCM288": "9876543210",
    "KA01HH1234": "9988776655",
    "DL3CAQ1234": "8877665544",
    "HR26DQ5555": "7766554433"
}

# Database to store tracked plates
# Format: {plate_text: {"plate": str, "phone": str, "first_seen": timestamp, "status": str, "sms_sent": bool}}
tracked_plates = {}

MY_NUMBER = "8905905953"

@app.get("/")
async def index(request: Request):
    try:
        return templates.TemplateResponse(request=request, name="index.html")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JSONResponse(content={"error": f"Template error: {str(e)}"}, status_code=500)

@app.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    # Save file
    file_path = f"static/uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return await process_image(file_path)

async def process_image(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return JSONResponse(content={"error": "Invalid image"}, status_code=400)
        
    results = model.predict(img, imgsz=640, conf=0.3)
    
    detections = []
    for r in results:
        for box in r.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])
            
            # OCR
            plate_crop = img[y1:y2, x1:x2]
            if plate_crop.size > 0:
                ocr_res = reader.readtext(plate_crop)
                plate_text = "".join([res[1] for res in ocr_res]).upper().replace(" ", "")
                
                # Filter noise
                if len(plate_text) > 3:
                    phone = PLATE_DB.get(plate_text, "Unknown")
                    
                    # Update tracking
                    if plate_text not in tracked_plates:
                        tracked_plates[plate_text] = {
                            "plate": plate_text,
                            "phone": phone,
                            "detection_time": time.time(), # Use float timestamp for easier math
                            "status": "Checking",
                            "sms_sent": False
                        }
                    
                    detections.append({
                        "plate": plate_text,
                        "phone": phone,
                        "confidence": conf,
                        "box": [x1, y1, x2, y2],
                        "timestamp": tracked_plates[plate_text]["detection_time"]
                    })
    
    return JSONResponse(content={"detections": detections, "image_url": f"/{img_path}"})

@app.post("/api/send-sms")
async def send_sms(data: dict):
    plate = data.get("plate")
    phone = data.get("phone")
    message = data.get("message", "E-Challan issued for No-Parking violation.")
    
    if plate in tracked_plates:
        tracked_plates[plate]["status"] = "CHALLANED"
        tracked_plates[plate]["sms_sent"] = True
        
        # Simulate SMS sending
        print(f"\n[SMS GATEWAY] Sending from {MY_NUMBER} to {phone}")
        print(f"[SMS MESSAGE] Plate: {plate} | {message}")
        print(f"[SMS STATUS] Sent successfully.\n")
        
        return {"status": "success", "plate": plate}
    return {"status": "error", "message": "Plate not found in active tracking"}

@app.post("/api/manual-entry")
async def manual_entry(data: dict):
    """Allows external scripts to send plate detections to the portal."""
    plate = data.get("plate", "").upper()
    phone = data.get("phone", "Unknown")
    
    if not plate:
        return {"status": "error", "message": "No plate provided"}

    # Use existing PLATE_DB to find phone if not provided
    if phone == "Unknown":
        phone = PLATE_DB.get(plate, "+91 00000 00000")

    if plate not in tracked_plates:
        tracked_plates[plate] = {
            "plate": plate,
            "phone": phone,
            "detection_time": time.time(),
            "status": "Checking",
            "sms_sent": False
        }
        print(f"[REMOTE] New plate added: {plate}")
        return {"status": "success", "plate": plate}
    
    return {"status": "already_tracked", "plate": plate}

# Raspi Configuration
RASPI_IP = "10.87.142.222" # Updated Pi IP
RASPI_USER = "pi"        # Update this to your Pi's username
RASPI_IMAGE_PATH = "/home/pi/capture.jpg"
# Set the command here (rpicam-still is for the latest Raspberry Pi OS)
RASPI_CAPTURE_COMMAND = "rpicam-still -o" 

@app.get("/api/run-simulation")
async def run_simulation():
    """Triggers Raspberry Pi to take a photo, pulls it via SCP, and processes it."""
    import subprocess
    
    timestamp = int(time.time())
    local_path = f"check/raspi_{timestamp}.jpg"
    
    # Check if we should skip Raspi for testing
    FORCE_FALLBACK = False # Set to True to bypass Raspi connection
    
    if not FORCE_FALLBACK:
        print(f"[REMOTE] Triggering capture on Raspi ({RASPI_IP})...")
        
        # Using the configurable command
        capture_cmd = f"ssh {RASPI_USER}@{RASPI_IP} \"{RASPI_CAPTURE_COMMAND} {RASPI_IMAGE_PATH}\""
        
        # Command to pull photo via SCP
        scp_cmd = f"scp {RASPI_USER}@{RASPI_IP}:{RASPI_IMAGE_PATH} {local_path}"
        
        try:
            # 1. Take photo
            process = subprocess.run(capture_cmd, shell=True, capture_output=True, text=True, timeout=10)
            if process.returncode != 0:
                print(f"[WARN] SSH Capture failed: {process.stderr}. Using fallback.")
                if os.path.exists("test.jpg"):
                    shutil.copy("test.jpg", local_path)
                else:
                    return JSONResponse(content={"error": f"Raspi unreachable and test.jpg missing. SSH Error: {process.stderr}"}, status_code=500)
            else:
                # 2. Pull photo
                scp_process = subprocess.run(scp_cmd, shell=True, capture_output=True, text=True, timeout=10)
                if scp_process.returncode != 0:
                    print(f"[WARN] SCP Transfer failed: {scp_process.stderr}. Using fallback.")
                    shutil.copy("test.jpg", local_path)
        except Exception as e:
            print(f"[WARN] Connection error: {e}. Using fallback.")
            if os.path.exists("test.jpg"):
                shutil.copy("test.jpg", local_path)
            else:
                return JSONResponse(content={"error": f"Connection failed: {str(e)}"}, status_code=500)
    else:
        # Direct fallback for pure simulation
        shutil.copy("test.jpg", local_path)
        
    # 3. Process the image (either from Raspi or Fallback)
    print(f"[INFO] Processing image: {local_path}")
    return await process_image(local_path)

@app.get("/logs")
async def get_logs():
    """Returns the current state of all tracked plates for the dashboard."""
    # Convert timestamps back to ISO for JS if needed, or just send floats
    logs = []
    for p, data in tracked_plates.items():
        logs.append({
            "plate": data["plate"],
            "phone": data["phone"],
            "detection_time": time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(data["detection_time"])),
            "status": data["status"],
            "elapsed": int(time.time() - data["detection_time"])
        })
    return {"logs": logs}

if __name__ == "__main__":
    import uvicorn
    # Changed to 8080 to avoid conflicts
    uvicorn.run(app, host="0.0.0.0", port=8080)
