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

app = FastAPI()

# Setup directories
os.makedirs("static/uploads", exist_ok=True)
os.makedirs("templates", exist_ok=True)
os.makedirs("static/css", exist_ok=True)
os.makedirs("static/js", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Initialize Models
print("Loading YOLOv8 model...")
model = YOLO('best.pt')
print("Initializing EasyOCR...")
reader = easyocr.Reader(['en'])

# Database to store tracked plates (In-memory for demo)
# Format: {plate_text: {"first_seen": timestamp, "last_seen": timestamp, "status": "OK"}}
tracked_plates = {}

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    # Save file
    file_path = f"static/uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process
    img = cv2.imread(file_path)
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
                    detections.append({
                        "plate": plate_text,
                        "confidence": conf,
                        "box": [x1, y1, x2, y2]
                    })
    
    return JSONResponse(content={"detections": detections, "image_url": f"/{file_path}"})

@app.get("/api/violations")
async def get_violations():
    # Placeholder for violation logic
    # In a real video stream, this would be updated continuously
    return JSONResponse(content={"violations": list(tracked_plates.values())})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
