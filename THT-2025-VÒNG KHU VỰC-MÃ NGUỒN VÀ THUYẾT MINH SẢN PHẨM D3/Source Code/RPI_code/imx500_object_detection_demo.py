import argparse
import sys
import time
from functools import lru_cache
import cv2
import tempfile
import io
import os
import pytesseract
import gtts
from gtts.tts import gTTS
import pygame
from datetime import datetime, timedelta
from googletrans import Translator
import numpy as np
import speech_recognition as sr
import pyttsx3
import threading
from picamera2 import MappedArray, Picamera2
from picamera2.devices import IMX500
from picamera2.devices.imx500 import (NetworkIntrinsics, postprocess_nanodet_detection)

last_detections = []
translator = Translator()
recognizer = sr.Recognizer()
engine = pyttsx3.init()

frame_start_time = time.time()
frame_count = 0

def send_email():
    with open("email.txt", "w") as f:
        f.write("""To: cudemlmao@gmail.com
From: yourgmail@gmail.com
Subject:

Nguoi than khiem thi cua ban dang gap nguy hiem hay kiem tra ngay !!!
""")
    os.system("ssmtp cudemlmao@gmail.com < email.txt")

class Detection:
    def __init__(self, coords, category, conf, metadata):
        self.category = category
        self.conf = conf
        self.box = imx500.convert_inference_coords(coords, metadata, picam2)

def speak(text):
    engine.say(text)
    engine.runAndWait()

def capture_and_read_text():
    frame = picam2.capture_array()
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        image_path = tmp_file.name
        cv2.imwrite(image_path, frame)
        print(f"Image saved to temporary file: {image_path}")
    text = pytesseract.image_to_string(image_path)
    print("Detected Text:", text)
    os.remove(image_path)
    pygame.mixer.init()
    if text.strip():
        tts = gTTS(text=text, lang='vi', slow=False)
        with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as tmp_mp3_file:
            tts.save(tmp_mp3_file.name)
            pygame.mixer.music.load(tmp_mp3_file.name)
            pygame.mixer.music.play()

pre_speech=""
def voice_listener():
    global pre_speech
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        print("Voice listener activated. Say something!")
        while True:
            try:
                audio = recognizer.listen(source, timeout=5)
                text = recognizer.recognize_google(audio, language='vi-VN')
                if(text==pre_speech):
                    continue
                if "giờ" in text or "ngày" in text:
                    now = datetime.now()
                    text_ap = f"Bây giờ là {now.hour} giờ {now.minute} phút, ngày {now.day} tháng {now.month} năm {now.year}"
                    tts = gTTS(text=text_ap, lang='vi', slow=False)
                    pygame.mixer.init()
                    with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as tmp_mp3_file:
                        tts.save(tmp_mp3_file.name)
                        pygame.mixer.music.load(tmp_mp3_file.name)
                        pygame.mixer.music.play()
                elif "chụp ảnh" in text:
                    capture_and_read_text()
                elif "cứu" in text:
                    send_email()
                    print("Gui Thanh Cong")
                pre_speech = text
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                print("Could not understand audio.")
            except sr.RequestError as e:
                print(f"Speech Recognition Error: {e}")

def parse_detections(metadata: dict):
    global last_detections
    bbox_normalization = intrinsics.bbox_normalization
    bbox_order = intrinsics.bbox_order
    threshold = args.threshold
    iou = args.iou
    max_detections = args.max_detections
    np_outputs = imx500.get_outputs(metadata, add_batch=True)
    input_w, input_h = imx500.get_input_size()
    if np_outputs is None:
        return last_detections
    if intrinsics.postprocess == "nanodet":
        boxes, scores, classes = postprocess_nanodet_detection(
            outputs=np_outputs[0], conf=threshold, iou_thres=iou, max_out_dets=max_detections
        )[0]
        from picamera2.devices.imx500.postprocess import scale_boxes
        boxes = scale_boxes(boxes, 1, 1, input_h, input_w, False, False)
    else:
        boxes, scores, classes = np_outputs[0][0], np_outputs[1][0], np_outputs[2][0]
        if bbox_normalization:
            boxes = boxes / input_h
        if bbox_order == "xy":
            boxes = boxes[:, [1, 0, 3, 2]]
        boxes = np.array_split(boxes, 4, axis=1)
        boxes = zip(*boxes)

    last_detections = [
        Detection(box, category, score, metadata)
        for box, score, category in zip(boxes, scores, classes)
        if score > threshold
    ]
    return last_detections

@lru_cache
def get_labels():
    labels = intrinsics.labels
    if intrinsics.ignore_dash_labels:
        labels = [label for label in labels if label and label != "-"]
    return labels

def estimate_distance(object_width_px: float, real_width: float, focal_length: float) -> float:
    if object_width_px == 0:
        return float('inf')
    return (real_width * focal_length) / object_width_px

last_time = datetime.now()
cur_time = datetime.now()
def draw_detections(request, stream="main"):
    global last_time, cur_time
    detections = last_detections
    if detections is None:
        return
    labels = get_labels()
    with MappedArray(request, stream) as m:
        for detection in detections:
            x, y, w, h = detection.box
            class_detect = labels[int(detection.category)]
            label = f"{class_detect} ({detection.conf:.2f})"
            real_object_width = 0.2
            focal_length_px = 800
            distance = estimate_distance(w, real_object_width, focal_length_px)
            distance_text = f"Distance: {distance:.2f}m"

            if (cur_time - last_time).total_seconds() >= 12:
                pygame.mixer.init()
                text_ap = class_detect
                if distance < 1.0:
                    text_ap = "Alert " + class_detect + " is near"
                translation = translator.translate(text_ap, src='en', dest='vi')
                tts = gTTS(text=translation.text, lang='vi', slow=False)
                with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as tmp_mp3_file:
                    tts.save(tmp_mp3_file.name)
                    pygame.mixer.music.load(tmp_mp3_file.name)
                    pygame.mixer.music.play()
                last_time = datetime.now()

            (text_width, text_height), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            text_x = x + 5
            text_y = y + 15
            overlay = m.array.copy()
            cv2.rectangle(overlay, (text_x, text_y - text_height), (text_x + text_width, text_y + baseline), (255, 255, 255), cv2.FILLED)
            alpha = 0.30
            cv2.addWeighted(overlay, alpha, m.array, 1 - alpha, 0, m.array)
            cv2.putText(m.array, label, (text_x, text_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            cv2.putText(m.array, distance_text, (text_x, text_y + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            cv2.rectangle(m.array, (x, y), (x + w, y + h), (0, 255, 0), thickness=2)

        if intrinsics.preserve_aspect_ratio:
            b_x, b_y, b_w, b_h = imx500.get_roi_scaled(request)
            color = (255, 0, 0)
            cv2.putText(m.array, "ROI", (b_x + 5, b_y + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            cv2.rectangle(m.array, (b_x, b_y), (b_x + b_w, b_y + b_h), (255, 0, 0, 0))

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="/usr/share/imx500-models/imx500_network_ssd_mobilenetv2_fpnlite_320x320_pp.rpk")
    parser.add_argument("--fps", type=int)
    parser.add_argument("--bbox-normalization", action=argparse.BooleanOptionalAction)
    parser.add_argument("--bbox-order", choices=["yx", "xy"], default="yx")
    parser.add_argument("--threshold", type=float, default=0.55)
    parser.add_argument("--iou", type=float, default=0.65)
    parser.add_argument("--max-detections", type=int, default=10)
    parser.add_argument("--ignore-dash-labels", action=argparse.BooleanOptionalAction)
    parser.add_argument("--postprocess", choices=["", "nanodet"], default=None)
    parser.add_argument("-r", "--preserve-aspect-ratio", action=argparse.BooleanOptionalAction)
    parser.add_argument("--labels", type=str)
    parser.add_argument("--print-intrinsics", action="store_true")
    return parser.parse_args()

if __name__ == "__main__":
    args = get_args()
    imx500 = IMX500(args.model)
    intrinsics = imx500.network_intrinsics
    print("Supported labels by this model:")
    for i, label in enumerate(intrinsics.labels):
        print(f"{i}: {label}")

    if not intrinsics:
        intrinsics = NetworkIntrinsics()
        intrinsics.task = "object detection"
    elif intrinsics.task != "object detection":
        print("Network is not an object detection task", file=sys.stderr)
        exit()

    for key, value in vars(args).items():
        if key == 'labels' and value is not None:
            with open(value, 'r') as f:
                intrinsics.labels = f.read().splitlines()
        elif hasattr(intrinsics, key) and value is not None:
            setattr(intrinsics, key, value)

    if intrinsics.labels is None:
        with open("assets/coco_labels.txt", "r") as f:
            intrinsics.labels = f.read().splitlines()
    intrinsics.update_with_defaults()

    if args.print_intrinsics:
        print(intrinsics)
        exit()
    picam2 = Picamera2(imx500.camera_num)
    config = picam2.create_preview_configuration(controls={"FrameRate": intrinsics.inference_rate}, buffer_count=12)
    imx500.show_network_fw_progress_bar()
    picam2.start(config)
    if intrinsics.preserve_aspect_ratio:
        imx500.set_auto_aspect_ratio()

    picam2.pre_callback = draw_detections
    listener_thread = threading.Thread(target=voice_listener, daemon=True)
    listener_thread.start()
    while True:
        cur_time = datetime.now()
        frame = picam2.capture_array()
        frame_bgr = cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)
        cv2.imshow("Camera Feed", frame_bgr)
        last_results = parse_detections(picam2.capture_metadata())
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
    cv2.destroyAllWindows()
    picam2.stop()
