from gtts import gTTS
import os
import simpleaudio as sa # สำหรับเล่นเสียง
from pydub import AudioSegment # สำหรับจัดการไฟล์เสียง
from pydub.playback import play # สำหรับเล่นเสียงด้วย pydub (อีกวิธี)
import time

# --- ตั้งค่า Output File ---
AUDIO_OUTPUT_FILENAME = "response_audio.mp3" # gTTS สร้างเป็น MP3
WAV_OUTPUT_FILENAME = "response_audio.wav" # สำหรับการเล่นด้วย simpleaudio

def text_to_speech_gtts(text, lang='th', play_audio=True):
    """
    แปลงข้อความเป็นเสียงโดยใช้ Google Text-to-Speech (gTTS).

    Parameters:
    - text (str): ข้อความที่ต้องการแปลงเป็นเสียง.
    - lang (str): รหัสภาษา (เช่น 'en' สำหรับอังกฤษ, 'th' สำหรับไทย).
    - play_audio (bool): True หากต้องการให้เล่นเสียงทันทีหลังจากสร้างไฟล์.

    Returns:
    - str: ชื่อไฟล์เสียงที่สร้างขึ้น (นามสกุล .mp3) หรือ None หากเกิดข้อผิดพลาด.
    """
    try:
        print(f"--- กำลังแปลงข้อความเป็นเสียง (ภาษา {lang.upper()})... ---")
        tts = gTTS(text=text, lang=lang, slow=False) # slow=False เพื่อให้พูดด้วยความเร็วปกติ
        
        # บันทึกเป็นไฟล์ MP3 ก่อน
        tts.save(AUDIO_OUTPUT_FILENAME)
        print(f"--- สร้างไฟล์เสียง: {AUDIO_OUTPUT_FILENAME} แล้ว ---")

        # gTTS จะบันทึกเป็น MP3 โดยตรง แต่ simpleaudio อาจเล่น MP3 ไม่ได้โดยตรง
        # เราจะใช้ pydub แปลงจาก MP3 เป็น WAV ก่อนเล่น (wav เล่นได้ชัวร์กว่า)
        audio = AudioSegment.from_mp3(AUDIO_OUTPUT_FILENAME)
        audio.export(WAV_OUTPUT_FILENAME, format="wav")
        print(f"--- แปลงเป็นไฟล์ WAV: {WAV_OUTPUT_FILENAME} แล้ว ---")
        
        if play_audio:
            print("--- กำลังเล่นเสียง... ---")
            wave_obj = sa.WaveObject.from_wave_file(WAV_OUTPUT_FILENAME)
            play_obj = wave_obj.play()
            play_obj.wait_done() # รอให้เสียงเล่นจบ
            print("--- เล่นเสียงเสร็จสิ้น ---")

        # ลบไฟล์ชั่วคราวออก (ถ้าไม่ต้องการเก็บไว้)
        if os.path.exists(AUDIO_OUTPUT_FILENAME):
            os.remove(AUDIO_OUTPUT_FILENAME)
        # if os.path.exists(WAV_OUTPUT_FILENAME):
        #     os.remove(WAV_OUTPUT_FILENAME)

        return WAV_OUTPUT_FILENAME # คืนชื่อไฟล์ WAV ที่เล่นได้
    
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการแปลงข้อความเป็นเสียง: {e}")
        # สำหรับ gTTS บางครั้งอาจเกิดข้อผิดพลาดถ้าไม่มี internet connection
        print("โปรดตรวจสอบ Internet connection ของคุณ")
        return None

# --- Main execution block ---
if __name__ == "__main__":
    # ตัวอย่างการใช้งานภาษาไทย
    thai_text = "สวัสดีครับ ผมคือระบบผู้ช่วยเสียงของคุณ ยินดีที่ได้รู้จักครับ"
    output_file_thai = text_to_speech_gtts(thai_text, lang='th')