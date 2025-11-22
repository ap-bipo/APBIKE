import speech_recognition as sr
import pyttsx3
from datetime import datetime
import pygame
import argparse
import sys
import time  # Import time module to track FPS
from functools import lru_cache
import cv2
import tempfile
import io
import gtts
from gtts.tts import gTTS
import pygame
from datetime import datetime, timedelta
import numpy as np

recognizer = sr.Recognizer()
engine = pyttsx3.init()

def speak(text):
    engine.say(text)
    engine.runAndWait()

while True:
    try:
        with sr.Microphone() as mic:
            recognizer.adjust_for_ambient_noise(mic, duration=0.7)
            print(" Đang lắng nghe...")
            audio = recognizer.listen(mic)
            text = recognizer.recognize_google(audio, language='vi-VN')
            if "giờ" in text or "ngày" in text:
                now = datetime.now()
                pygame.mixer.init()
                text_ap = f"Bây giờ là {now.hour} giờ {now.minute} phút, ngày {now.day} tháng {now.month} năm {now.year}"
                tts = gTTS(text=text_ap, lang='vi', slow=False)

                with tempfile.NamedTemporaryFile(delete=True, suffix=".mp3") as tmp_mp3_file:
                    tts.save(tmp_mp3_file.name)
                    pygame.mixer.music.load(tmp_mp3_file.name)
                    pygame.mixer.music.play()
                    
            print(f"️ Bạn nói: {text}")

            # Kiểm tra nội dung
            


    except sr.UnknownValueError:
        print(" Không nhận diện được. Hãy thử lại.")
        continue

    except sr.RequestError as e:
        print(f" Lỗi dịch vụ Google: {e}")
        continue


