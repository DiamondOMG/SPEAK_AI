import pvporcupine
import pyaudio  # ตรวจสอบให้แน่ใจว่าติดตั้งแล้ว
import struct
import sys

# แทนที่ด้วย AccessKey ของคุณจาก Picovoice Console
PICOVOICE_ACCESS_KEY = "8QZmFYrFufntomOJGZmf8nSm5BXB+4csXK98vqSdLJ37RZNR7RQc2w=="

# ตัวอย่างการใช้โมเดลสำเร็จรูป (ภาษาอังกฤษ)
# KEYWORDS_TO_USE ต้องเป็น list ของชื่อ keyword ที่ตรงกับใน pvporcupine.KEYWORDS
# เลือกจากที่คุณเห็น: 'picovoice', 'hey google', 'alexa', 'jarvis', ฯลฯ
KEYWORDS_TO_USE = ['jarvis'] # คุณอาจจะลองเปลี่ยนเป็น ['hey google'] หรือ ['alexa'] ก็ได้
KEYWORD_LABELS = KEYWORDS_TO_USE # ใช้ชื่อเดียวกันกับ keyword_to_use เพื่อแสดงผล


def main():
    print("กำลังเริ่มต้น Porcupine Wake Word Detector...")
    print(f"กำลังฟังคำสั่ง: {', '.join(KEYWORD_LABELS)}")

    porcupine = None
    pa = None
    audio_stream = None

    try:
        # ใช้ keywords argument ตรงๆ ตามที่เอกสารและผลลัพธ์ KEYWORDS ของคุณบอก
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keywords=KEYWORDS_TO_USE
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
                # ตรงนี้คุณสามารถเพิ่มโค้ดสำหรับการตอบสนองเมื่อตรวจพบ Wake Word
                # เช่น เรียกใช้ Whisper AI หรือทำอย่างอื่น

    except pvporcupine.PorcupineInvalidArgumentError as e:
        print(f"Error: Invalid argument passed to Porcupine. {e}")
        print("Please ensure your AccessKey is correct and valid, and keywords are correct.")
        print(f"Available keywords: {pvporcupine.KEYWORDS}") # เพิ่มบรรทัดนี้เพื่อแสดง keywords ที่มี
    except Exception as e:
        print(f"เกิดข้อผิดพลาด: {e}")
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()
        print("ปิดโปรแกรม Wake Word Detector")

if __name__ == "__main__":
    main()