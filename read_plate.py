import cv2
from ultralytics import YOLO
import easyocr
import os

def process_plate(image_path, output_file):
    # Load YOLO model
    model = YOLO('best.pt')
    
    # Initialize EasyOCR
    reader = easyocr.Reader(['en'])
    
    # Run YOLO detection
    results = model.predict(image_path, imgsz=640, conf=0.4)
    
    img = cv2.imread(image_path)
    
    with open(output_file, 'w') as f:
        f.write(f"Inference and OCR Results for {image_path}:\n")
        
        for r in results:
            for box in r.boxes:
                # Get coordinates
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])
                
                # Crop the plate
                plate_crop = img[y1:y2, x1:x2]
                
                if plate_crop.size == 0:
                    continue
                
                # OCR the crop
                # EasyOCR returns a list of results: (bbox, text, prob)
                ocr_results = reader.readtext(plate_crop)
                
                plate_text = ""
                if ocr_results:
                    # Sort by confidence or just concat
                    plate_text = " ".join([res[1] for res in ocr_results])
                
                # Filter text (optional: remove special chars)
                plate_text = "".join(e for e in plate_text if e.isalnum() or e == " ")
                
                print(f"Detected Plate: {plate_text} (Conf: {conf:.2f})")
                f.write(f"Plate Box: [{x1}, {y1}, {x2}, {y2}]\n")
                f.write(f"Confidence: {conf:.2f}\n")
                f.write(f"Plate Number: {plate_text}\n")
                f.write("-" * 20 + "\n")

if __name__ == "__main__":
    img_path = 'check/500_4143.webp'
    out_file = 'detection_results.txt'
    process_plate(img_path, out_file)
    print(f"Results saved to {out_file}")
