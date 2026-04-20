from ultralytics import YOLO
import os

def train_and_export():
    # PATH to weights if we want to resume
    last_weights = "runs/detect/train/weights/last.pt"
    
    if os.path.exists(last_weights):
        print(f"Resuming training from {last_weights} using GPU...")
        model = YOLO(last_weights)
        # For resume=True, many arguments are loaded from the previous training
        model.train(resume=True)
    else:
        print("Starting training from scratch using GPU...")
        model = YOLO('yolov8n.pt')
        model.train(
            data='data.yaml',
            epochs=25,
            imgsz=416,
            batch=-1,
            device=0 # 0 for first NVIDIA GPU
        )
    
    print("Training finished. Evaluating...")
    # After training, load the best model for validation and export
    model = YOLO("runs/detect/train/weights/best.pt")
    metrics = model.val()
    print(f"mAP50: {metrics.box.map50}")
    
    # Export
    print("Exporting to ONNX...")
    model.export(format='onnx', imgsz=416)
    
    print("Exporting to TFLite...")
    model.export(format='tflite', imgsz=416)
    
    print("All tasks completed.")

if __name__ == "__main__":
    train_and_export()
