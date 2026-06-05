import cv2 
import numpy as np 
import subprocess 
from ultralytics import YOLO 
# Load YOLOv8 model 
model = YOLO("best.pt") 
# Frame size 
WIDTH = 640 
HEIGHT = 480 
# Start libcamera-vid stream (raw YUV420 output to stdout) 
cmd = [ 
    "libcamera-vid", 
    "-t", "0", # unlimited time 
    "--width", str(WIDTH), 
    "--height", str(HEIGHT), 
    "-o", "-", # output to stdout 
    "--codec", "yuv420"] 

# Start subprocess

p = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                     bufsize=WIDTH * HEIGHT * 3) 
while True: 
    # Read one YUV420 frame (1.5 bytes per pixel) 
    raw_frame = p.stdout.read(int(WIDTH * HEIGHT * 1.5)) 
    if not raw_frame: 
        print("Failed to grab frame") 
        break 
    # Decode YUV420 to BGR (for OpenCV) 
    yuv = np.frombuffer(raw_frame, 
                        dtype=np.uint8).reshape((int(HEIGHT * 1.5), WIDTH)) 
    frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420) 
    # Convert to RGB (YOLO expects RGB input) 
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB) 
    # Run YOLO detection 
    results = model(rgb_frame) 
    # Draw results on the original frame 
    for r in results: 
        for box in r.boxes: 
            x1, y1, x2, y2 = map(int, box.xyxy[0]) 
            cls = int(box.cls[0]) 
            conf = float(box.conf[0]) 
            label = model.names[cls] 
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2) 
            cv2.putText(frame, f"{label} {conf:.2f}", (x1, y1 - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2) 
            # Display the frame 
            cv2.imshow("YOLOv8 Detection", frame) 
            # Exit when pressing 'q' 
            if cv2.waitKey(1) & 0xFF == ord('q'): 
                break 
            # Terminate subprocess and close window 
            p.terminate() 
            cv2.destroyAllWindows()