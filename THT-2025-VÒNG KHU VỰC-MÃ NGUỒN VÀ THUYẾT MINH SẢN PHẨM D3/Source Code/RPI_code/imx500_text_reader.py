import tempfile
import pytesseract
import cv2
from picamera2 import Picamera2
from picamera2.devices import IMX500
import time
import os
import argparse
import pygame
import gtts
from gtts.tts import gTTS

# Initialize IMX500 camera
def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, help="Path of the model",
                        default="/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")
    parser.add_argument("--fps", type=int, help="Frames per second")
    parser.add_argument("--bbox-normalization", action=argparse.BooleanOptionalAction, help="Normalize bbox")
    parser.add_argument("--bbox-order", choices=["yx", "xy"], default="yx",
                        help="Set bbox order yx -> (y0, x0, y1, x1) xy -> (x0, y0, x1, y1)")
    parser.add_argument("--threshold", type=float, default=0.55, help="Detection threshold")
    parser.add_argument("--iou", type=float, default=0.65, help="Set iou threshold")
    parser.add_argument("--max-detections", type=int, default=10, help="Set max detections")
    parser.add_argument("--ignore-dash-labels", action=argparse.BooleanOptionalAction, help="Remove '-' labels ")
    parser.add_argument("--postprocess", choices=["", "nanodet"], default=None, help="Run post process of type")
    parser.add_argument("-r", "--preserve-aspect-ratio", action=argparse.BooleanOptionalAction,
                        help="preserve the pixel aspect ratio of the input tensor")
    parser.add_argument("--labels", type=str, help="Path to the labels file")
    parser.add_argument("--print-intrinsics", action="store_true", help="Print JSON network_intrinsics then exit")
    return parser.parse_args()

args = get_args()
    # Initialize the camera and model
imx500 = IMX500(args.model)
intrinsics = imx500.network_intrinsics
#imx500 = IMX500("/path/to/your/model/file")  # Provide the correct model file path
picam2 = Picamera2(imx500.camera_num)
config = picam2.create_preview_configuration(controls={"FrameRate": intrinsics.inference_rate}, buffer_count=12)
picam2.start(config)

def capture_and_read_text():
    # Capture an image frame from the camera
    frame = picam2.capture_array()

    # Save the frame to a temporary file
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        image_path = tmp_file.name
        cv2.imwrite(image_path, frame)  # Save the image to the temp file
        print(f"Image saved to temporary file: {image_path}")

    # Use pytesseract to read text from the saved image
    text = pytesseract.image_to_string(image_path)
    print("Detected Text:", text)

    # Optionally, clean up the temp file after processing
    os.remove(image_path)
    pygame.mixer.init()
                    #print(text)
    if text.strip():
        
        tts = gTTS(text=text, lang='en', slow=False)

    # Use a temporary file to store the MP3
        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as tmp_mp3_file:
            tts.save(tmp_mp3_file.name)

        # Load and play the MP3 using pygame
            pygame.mixer.music.load(tmp_mp3_file.name)
            pygame.mixer.music.play()


def main():
    print("Press 'k' to capture an image and read text from it.")
    try:
        while True:
            # Capture image frame from the camera
            frame = picam2.capture_array()

            # Display the live camera feed
            cv2.imshow("Camera Feed - Press 'k' to Capture", frame)

            # Capture keypresses
            key = cv2.waitKey(1) & 0xFF

            if key == ord('k'):  # If 'k' is pressed
                capture_and_read_text()

            if key == ord('q'):  # Press 'q' to quit the program
                break

            time.sleep(0.1)  # Small delay to prevent high CPU usage

    except KeyboardInterrupt:
        print("Stopped by user.")
    finally:
        picam2.stop()
        cv2.destroyAllWindows()  # Close all OpenCV windows

if __name__ == "__main__":
    main()
