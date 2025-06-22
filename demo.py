import time
import os
import whisper
from wake_picovoice import listen_for_wake_word
from audio_interface import get_audio_handler

model = whisper.load_model("small")
audio = get_audio_handler()

def process_voice_command():
    audio_file = audio.record_audio("recorded_audio.wav")
    
    if audio_file:
        try:
            result = model.transcribe(audio_file)
            transcribed_text = result["text"]
            
            if os.path.exists(audio_file):
                os.remove(audio_file)
                
            return transcribed_text if transcribed_text else None
        except:
            return None
    return None

def speak_text(text, lang='th'):
    temp_file = audio.text_to_speech(text, lang)
    if temp_file:
        audio.play_audio(temp_file)
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main():
    detected = listen_for_wake_word(detect_and_exit=True)
    if detected:
        speak_text("สวัสดีครับ")
        time.sleep(1)
        
        command_text = None
        while not command_text:
            command_text = process_voice_command()
        
        speak_text(command_text)

if __name__ == "__main__":
    main()