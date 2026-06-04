import cv2
import numpy as np
import subprocess
from ultralytics import YOLOv8

# Load your YOLOv10 model
model = YOLOv8("weights (6).pt")  # Replace with the correct path to your model

# Video resolution
WIDTH = 640
HEIGHT = 480

# Start libcamera-vid to stream YUV420 video
cmd = [
    "libcamera-vid",
    "-t", "0",               # Run indefinitely
    "--width", str(WIDTH),
    "--height", str(HEIGHT),
    "-o", "-",               # Output to stdout
    "--codec", "yuv420"
]

# Launch the subprocess to capture frames
p = subprocess.Popen(cmd, stdout=subprocess.PIPE, bufsize=WIDTH * HEIGHT * 3)

def predict_and_detect(chosen_model, img, conf=0.4):
    # Run YOLOv10 inference
    results = chosen_model.predict(img, conf=conf)

    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            class_id = int(box.cls.item())
            confidence = float(box.conf.item())
            class_name = result.names[class_id]

            class_label = f"{class_name}: "
            conf_label = f"{confidence * 100:.1f}%"

            (class_width, class_height), _ = cv2.getTextSize(
                class_label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            (conf_width, _), _ = cv2.getTextSize(
                conf_label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)

            text_y = max(25, y1 - 5)

            # Draw bounding box
            cv2.rectangle(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
            # Draw label background
            cv2.rectangle(img, (x1, text_y - class_height - 5),
                          (x1 + class_width + conf_width + 10, text_y + 5),
                          (255, 0, 0), -1)

            # Draw class label (white)
            cv2.putText(img, class_label, (x1 + 3, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            # Draw confidence (red)
            cv2.putText(img, conf_label, (x1 + class_width + 5, text_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

            print(f"Detected: {class_name} {confidence * 100:.1f}% at [{x1},{y1},{x2},{y2}]")

    return img

try:
    while True:
        # Read a single frame from the subprocess
        raw_frame = p.stdout.read(int(WIDTH * HEIGHT * 1.5))
        if not raw_frame:
            print("Failed to grab frame")
            break

        # Convert YUV420 frame to OpenCV-compatible BGR format
        yuv = np.frombuffer(raw_frame, dtype=np.uint8).reshape((int(HEIGHT * 1.5), WIDTH))
        frame = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)

        # Convert BGR to RGB for YOLO
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Run detection and draw results
        result_img = predict_and_detect(model, rgb_frame, conf=0.4)

        # Display the result
        cv2.imshow("YOLOv8 Live Detection", result_img)
        if cv2.waitKey(1) == 27:  # Press ESC to exit
            break

except KeyboardInterrupt:
    print("Interrupted by user")

finally:
    # Cleanup
    p.terminate()
    p.wait()
    cv2.destroyAllWindows()
    print("Process terminated.")