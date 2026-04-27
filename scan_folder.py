import os
import cv2
import requests
from ultralytics import YOLO
import easyocr
import time

# API endpoint for the Admin Portal
API_URL = "http://localhost:8080/api/manual-entry"

def scan_check_folder(folder_path):
    print(f"🚀 Initializing AI Scanner...")
    
    if not os.path.exists('best.pt'):
        print("Error: best.pt model file not found in current directory.")
        return

    # Load models
    model = YOLO("best.pt") 
    reader = easyocr.Reader(['en'])
    
    if not os.path.exists(folder_path):
        print(f"Error: Folder {folder_path} not found.")
        return

    images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.png'))]
    print(f"🔍 Found {len(images)} images in {folder_path}")

    for img_name in images:
        path = os.path.join(folder_path, img_name)
        img = cv2.imread(path)
        if img is None: continue

        print(f"  --- Processing: {img_name} ---")
        results = model(img, conf=0.4, verbose=False)
        
        for r in results:
            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                
                # Padding for OCR
                h, w = img.shape[:2]
                pad = 5
                nx1, ny1 = max(0, x1-pad), max(0, y1-pad)
                nx2, ny2 = min(w, x2+pad), min(h, y2+pad)
                
                plate_crop = img[ny1:ny2, nx1:nx2]
                if plate_crop.size == 0: continue

                # OCR Processing
                ocr_res = reader.readtext(plate_crop)
                plate_text = "".join([res[1] for res in ocr_res]).upper()
                plate_text = "".join(e for e in plate_text if e.isalnum())
                
                if plate_text and len(plate_text) > 4:
                    print(f"    ✅ Detected: {plate_text} -> Sending to Portal...")
                    # Send to Portal
                    try:
                        resp = requests.post(API_URL, json={"plate": plate_text})
                        if resp.status_code == 200:
                            print(f"       [SUCCESS] {plate_text} is now live on Dashboard!")
                    except:
                        print(f"       [FAILED] Could not connect to Admin Portal (Is app.py running?)")

if __name__ == "__main__":
    # Scans the 'check' folder
    target = "check"
    scan_check_folder(target)
