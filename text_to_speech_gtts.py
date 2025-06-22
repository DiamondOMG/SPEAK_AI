from gtts import gTTS
import os
import pygame
import time

AUDIO_OUTPUT_FILENAME = "response_audio.mp3"

def text_to_speech_gtts(text, lang='th', play_audio=True):
    try:
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(AUDIO_OUTPUT_FILENAME)
        
        if play_audio:
            pygame.mixer.quit()
            pygame.mixer.init()
            pygame.mixer.music.load(AUDIO_OUTPUT_FILENAME)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()

        if os.path.exists(AUDIO_OUTPUT_FILENAME):
            os.remove(AUDIO_OUTPUT_FILENAME)

        return True
    
    except Exception as e:
        return None

if __name__ == "__main__":
    thai_text = "สวัสดีครับ ผมคือระบบผู้ช่วยเสียงของคุณ ยินดีที่ได้รู้จักครับ"
    text_to_speech_gtts(thai_text, lang='th')