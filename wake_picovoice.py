import pvporcupine
import pyaudio
import struct
import sys
import os # เพิ่ม import os เพื่อช่วยในการระบุ path

# แทนที่ด้วย AccessKey ของคุณจาก Picovoice Console
PICOVOICE_ACCESS_KEY = "8QZmFYrFufntomOJGZmf8nSm5BXB+4csXK98vqSdLJ37RZNR7RQc2w=="

# --- การกำหนดค่าสำหรับ Custom Model ---
# ตั้งค่าชื่อไฟล์ .ppn ของคุณ
CUSTOM_MODEL_FILENAME = "models/jarvis_en_windows_v3_0_0.ppn"
# สร้าง full path ไปยังไฟล์ .ppn
# os.path.join จะช่วยให้ path ทำงานได้ทั้งบน Windows, macOS, Linux
PATH_TO_CUSTOM_JARVIS_MODEL = os.path.join(os.path.dirname(__file__), CUSTOM_MODEL_FILENAME)

# Label สำหรับแสดงผลเมื่อตรวจพบ
KEYWORD_LABELS = ['Jarvis (Custom)']

def listen_for_wake_word(detect_and_exit=False):
    print(f"กำลังฟังคำสั่ง: {', '.join(KEYWORD_LABELS)}")

    porcupine = None
    pa = None
    audio_stream = None

    try:
        # ใช้ keyword_paths แทน keywords เพื่อชี้ไปยังไฟล์ .ppn ของคุณ
        # sensitivities สามารถปรับได้เช่นกัน (ต้องเป็น list ที่มีขนาดเท่ากับ keyword_paths)
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keyword_paths=[PATH_TO_CUSTOM_JARVIS_MODEL], # ใช้ list เพราะอาจมีหลาย keyword
            sensitivities=[0.6] # ลองปรับค่านี้ดู ถ้า 1.0 ยังไม่พอใจ (0.0-1.0)
        )

        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        print("พร้อมรับคำสั่งเสียง...")

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            result = porcupine.process(pcm)

            if result >= 0:
                print(f"!!! ตรวจพบคำสั่ง: {KEYWORD_LABELS[result]} !!!")
                print("--- พร้อมรับคำสั่งหลัก ---") # เพิ่มข้อความนี้
                return True  # คืนค่า True เมื่อตรวจพบ Wake Word

    except pvporcupine.PorcupineInvalidArgumentError as e:
        print(f"Error: Invalid argument passed to Porcupine. {e}")
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()

if __name__ == "__main__":
    detected = listen_for_wake_word(detect_and_exit=True)
