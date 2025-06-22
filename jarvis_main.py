import time

from wake_picovoice import listen_for_wake_word
from text_to_speech_gtts import text_to_speech_gtts
from local_whisper_app import process_voice_command

def main():
    # 1. รอฟัง Wake Word
    detected = listen_for_wake_word(detect_and_exit=True)
    if detected:
        # 2. พูดทักทาย
        text_to_speech_gtts("สวัสดีครับ", lang='th', play_audio=True)
        time.sleep(1)
        # 3. ฟังคำสั่งเสียง
        command_text = None
        while not command_text:
            command_text = process_voice_command()
        # 4. ตอบกลับด้วยเสียงที่ได้ยิน
        text_to_speech_gtts(command_text, lang='th', play_audio=True)

if __name__ == "__main__":
    main()