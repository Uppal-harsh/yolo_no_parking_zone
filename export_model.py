from ultralytics import YOLO
import os

def export_model():
    model_path = "runs/detect/train/weights/best.pt"
    if not os.path.exists(model_path):
        print(f"Error: {model_path} not found.")
        return
        
    print(f"Loading {model_path}...")
    model = YOLO(model_path)
    
    # print("Validating model...")
    # results = model.val(data='data.yaml', device='cpu')
    # print(f"mAP50: {results.box.map50}")
    # print(f"Precision: {results.box.mp}")
    # print(f"Recall: {results.box.mr}")
    
    if not os.path.exists("runs/detect/train/weights/best.onnx"):
        print("Exporting to ONNX...")
        onnx_path = model.export(format='onnx', imgsz=416)
        print(f"ONNX exported to: {onnx_path}")
    else:
        print("ONNX already exists, skipping.")
    
    print("Exporting to TFLite...")
    try:
        tflite_path = model.export(format='tflite', imgsz=416)
        print(f"TFLite exported to: {tflite_path}")
    except Exception as e:
        print(f"TFLite export failed: {e}")

if __name__ == "__main__":
    export_model()
