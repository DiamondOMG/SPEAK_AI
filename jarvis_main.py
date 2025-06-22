import time
from wake_picovoice import listen_for_wake_word
from text_to_speech_gtts import text_to_speech_gtts
from local_whisper_app import process_voice_command

def main():
    detected = listen_for_wake_word(detect_and_exit=True)
    if detected:
        text_to_speech_gtts("สวัสดีครับ", lang='th', play_audio=True)
        time.sleep(0.2)
        command_text = None
        while not command_text:
            command_text = process_voice_command()
        text_to_speech_gtts(command_text, lang='th', play_audio=True)

if __name__ == "__main__":
    main()