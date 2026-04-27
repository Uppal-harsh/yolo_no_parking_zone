import time
import requests
import os

# --- PI CAMERA CONFIGURATION ---
# Note: This script requires 'Picamera2' installed on the Raspberry Pi
# sudo apt install python3-picamera2

LAPTOP_IP = "192.168.1.5" # UPDATE THIS TO YOUR LAPTOP'S IP
SERVER_URL = f"http://{LAPTOP_IP}:8000/upload"
CAPTURE_INTERVAL = 5 # Seconds between checks

def run_camera_node():
    from picamera2 import Picamera2
    
    picam2 = Picamera2()
    config = picam2.create_still_configuration()
    picam2.configure(config)
    picam2.start()
    
    print(f"--- AI No-Parking System: Remote Node ---")
    print(f"Monitoring via Camera v3 -> Sending to {SERVER_URL}")
    
    try:
        while True:
            temp_img = "current_capture.jpg"
            picam2.capture_file(temp_img)
            
            print(f"[{time.strftime('%H:%M:%S')}] Frame captured. Analyzing...")
            
            with open(temp_img, 'rb') as f:
                files = {'file': f}
                try:
                    r = requests.post(SERVER_URL, files=files, timeout=5)
                    results = r.json()
                    
                    if results['detections']:
                        for d in results['detections']:
                            print(f" >> DETECTED: {d['plate']} (Conf: {d['confidence']:.2f})")
                    else:
                        print(" >> Status: No vehicles detected.")
                except Exception as e:
                    print(f" !! Communication Error: {e}")
            
            time.sleep(CAPTURE_INTERVAL)
            
    except KeyboardInterrupt:
        picam2.stop()
        print("Node stopped.")

if __name__ == "__main__":
    try:
        run_camera_node()
    except ImportError:
        print("Error: Picamera2 not found. This script must be run on a Raspberry Pi with a Camera Module v3.")
