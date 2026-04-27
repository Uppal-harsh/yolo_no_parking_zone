import cv2
import os
import numpy as np
from ultralytics import YOLO
import easyocr

def process_plates_in_folder(folder_path, output_file):
    if not os.path.exists('best.pt'):
        print("Error: best.pt not found.")
        return
        
    model = YOLO('best.pt')
    reader = easyocr.Reader(['en'])
    
    valid_extensions = ('.jpg', '.jpeg', '.png', '.webp')
    image_files = [f for f in os.listdir(folder_path) if f.lower().endswith(valid_extensions)]
    
    with open(output_file, 'w') as f:
        f.write(f"Inference and OCR Results for folder: {folder_path}\n")
        f.write("=" * 40 + "\n")
        
        for img_name in image_files:
            img_path = os.path.join(folder_path, img_name)
            img = cv2.imread(img_path)
            if img is None: continue
                
            results = model.predict(img, imgsz=640, conf=0.3, verbose=False) # Increased conf to reduce noise
            
            f.write(f"\nImage: {img_name}\n")
            
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    
                    # 1. Padding
                    h, w = img.shape[:2]
                    pad = 5
                    nx1, ny1 = max(0, x1-pad), max(0, y1-pad)
                    nx2, ny2 = min(w, x2+pad), min(h, y2+pad)
                    
                    plate_crop = img[ny1:ny2, nx1:nx2]
                    
                    # 2. Pre-processing: Grayscale + Upscale
                    gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
                    upscaled = cv2.resize(gray, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
                    
                    ocr_res = reader.readtext(upscaled)
                    plate_text = "".join([res[1] for res in ocr_res]).upper()
                    plate_text = "".join(e for e in plate_text if e.isalnum())
                    
                    line = f"Plate: {plate_text} (Conf: {conf:.2f})"
                    print(f"Processing {img_name} -> {line}")
                    f.write(line + "\n")
            f.write("-" * 20 + "\n")

if __name__ == "__main__":
    process_plates_in_folder('check', 'detection_results.txt')
