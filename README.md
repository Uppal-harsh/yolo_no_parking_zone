# Indian License Plate Detection & No-Parking Enforcement AI

This is a comprehensive AI solution for automated license plate detection and no-parking violation enforcement, optimized for edge deployment on Raspberry Pi 4.

## 🚀 Features
- **Accurate Detection**: YOLOv8-nano model trained specifically on Indian license plates.
- **Embedded OCR**: Automatic plate number extraction using EasyOCR.
- **Admin Portal**: A world-class, Glassmorphism-themed web dashboard for real-time monitoring.
- **Violation Logic**: 
  - **Warning**: Issued after 3 minutes.
  - **Challan & SMS**: Issued after 5 minutes of parking.
- **Edge Deployment**: Pre-exported ONNX models for high-performance inference on CPU-only devices like Raspberry Pi 4.

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd JOE
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Admin Portal
```bash
python app.py
```

## 📋 Dashboard Usage
1. Open your browser to `http://localhost:8000`.
2. **Access from Raspberry Pi**: Ensure the Pi is on the same network and navigate to `http://<your-laptop-ip>:8000`.
3. **Upload**: Use the drag-and-drop zone to process images or videos.
4. **Monitor**: Watch the violation log for real-time status updates and timers.

## 📦 Deployment Options

### Option A: Local Deployment (Standalone Pi)
- Run the full AI and Web Portal directly on the Pi 4.
- Best for offline use.
- Use `best.onnx` for speed.

### Option B: Distributed Deployment (Recommended)
- **Laptop (Server)**: Runs `app.py`. Performs heavy AI & OCR.
- **Raspberry Pi (Node)**: Runs `pi_camera_node.py`. Captures images from Camera v3 and sends them to the laptop.
- **Why?**: Zero throttling on Pi and lightning-fast AI on Laptop.

## 🔌 Pi Camera v3 Node Setup
1. Connect Pi Camera v3 to the Raspberry Pi.
2. Ensure `Picamera2` is installed: `sudo apt install python3-picamera2`.
3. Update `LAPTOP_IP` in `pi_camera_node.py`.
4. Run: `python3 pi_camera_node.py`.

## ⚖️ License
MIT License
