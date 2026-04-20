from ultralytics import YOLO
import os

def check():
    onnx_path = "runs/detect/train/weights/best.onnx"
    if os.path.exists(onnx_path):
        print("Loading ONNX model for check...")
        model = YOLO(onnx_path, task='detect')
        print("Model loaded successfully.")
        # Inference on a sample image from validation set
        sample_img = os.listdir("dataset/valid/images")[0]
        results = model.predict(os.path.join("dataset/valid/images", sample_img))
        print(f"Results: {results}")
        print("Inference successful.")
    else:
        print("ONNX not found.")

if __name__ == "__main__":
    check()
