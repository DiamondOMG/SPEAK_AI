import time
import asyncio
from wake_picovoice import listen_for_wake_word
from text_to_speech_gtts import text_to_speech_gtts
from local_whisper_app import process_voice_command
from post_api import post_to_jarvis_api

async def main():
    while True:
        detected = listen_for_wake_word(detect_and_exit=True)
        if detected:
            text_to_speech_gtts("สวัสดีครับ", lang='th', play_audio=True)
            time.sleep(0.2)

            command_text = None
            while not command_text:
                command_text = process_voice_command()

            post_response = await post_to_jarvis_api(command_text)
            print(f"Received response: {post_response}")
            if post_response and isinstance(post_response, dict):
                response_text = post_response.get("output", "ขออภัย ฉันไม่ได้รับข้อมูล")
            else:
                response_text = "ขออภัย ฉันไม่ได้รับข้อมูล"

            text_to_speech_gtts(response_text, lang='th', play_audio=True)

if __name__ == "__main__":
    asyncio.run(main())
