import os
import pvporcupine
import pyaudio
import struct
import sys
import wave
import time
import threading
import whisper 

# --- การตั้งค่าหลัก ---

# แทนที่ด้วย AccessKey ของคุณจาก Picovoice Console สำหรับ Porcupine
PICOVOICE_ACCESS_KEY = "8QZmFYrFufntomOJGZmf8nSm5BXB+4csXK98vqSdLJ37RZNR7RQc2w==" 

# ** กำหนด Path ไปยังไฟล์ .ppn ที่คุณสร้างขึ้นมาเอง **
# ไฟล์ jarvis_en_windows_v3_0_0.ppn ควรอยู่ในโฟลเดอร์ SPEAKER_AI/models/
CUSTOM_WAKE_WORD_PATH = os.path.join("models", "jarvis_en_windows_v3_0_0.ppn")

# ใช้ argument 'keyword_paths' สำหรับ Custom Wake Word
KEYWORD_PATHS_TO_USE = [CUSTOM_WAKE_WORD_PATH]
KEYWORD_LABELS = ["Jarvis (Custom)"] # ตั้งชื่อ Label เพื่อให้แสดงผลได้ถูกต้อง

# คุณสามารถกำหนด sensitivity ได้ด้วย (ค่าระหว่าง 0.0 ถึง 1.0)
CUSTOM_SENSITIVITIES = [0.7] # ลองปรับค่านี้ดูครับ 0.6-0.8 มักเป็นค่าที่ดี

# --- การตั้งค่า Whisper AI (Local Model) ---
# เลือกขนาดของโมเดล: "tiny", "base", "small", "medium", "large"
# "small" หรือ "base" เป็นจุดเริ่มต้นที่ดีสำหรับ CPU (ถ้าไม่มี GPU)
# "medium" หรือ "large" ต้องการ GPU ที่ดี
WHISPER_LOCAL_MODEL_SIZE = "small" 
# กำหนดภาษา หากต้องการให้ถอดเสียงในภาษาใดภาษาหนึ่งโดยเฉพาะ
# "th" สำหรับภาษาไทย, "en" สำหรับภาษาอังกฤษ, หรือ None เพื่อให้ Whisper ตรวจจับอัตโนมัติ
WHISPER_LANGUAGE = None # "th" หรือ "en" หรือ None

# --- การตั้งค่าการบันทึกเสียง ---
RECORDING_DURATION = 5 # จับเวลา 5 วินาที
TEMP_AUDIO_DIR = "temp_audio"
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True) # สร้างโฟลเดอร์สำหรับเก็บไฟล์เสียงชั่วคราว

# --- ฟังก์ชันสำหรับแสดง countdown ---
def countdown_timer():
    """แสดง countdown timer 5 วินาที"""
    for i in range(RECORDING_DURATION, 0, -1):
        print(f"\rกำลังบันทึก... {i} วินาที", end="", flush=True)
        time.sleep(1)
    print(f"\rบันทึกเสียงเสร็จสิ้น ({RECORDING_DURATION} วินาที)", flush=True)

# --- ฟังก์ชันหลัก ---

def main():
    print("กำลังเริ่มต้น Porcupine Wake Word Detector และ Whisper (Local) STT...")
    print(f"กำลังฟังคำสั่ง: {', '.join(KEYWORD_LABELS)}")

    porcupine = None
    whisper_model = None
    pa = None
    audio_stream = None

    try:
        # 1. สร้าง Instance ของ Porcupine Engine
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keyword_paths=KEYWORD_PATHS_TO_USE,
            sensitivities=CUSTOM_SENSITIVITIES
        )

        # 2. โหลด Whisper Model (Local)
        print(f"กำลังโหลด Whisper model '{WHISPER_LOCAL_MODEL_SIZE}'...")
        whisper_model = whisper.load_model(WHISPER_LOCAL_MODEL_SIZE)
        print("โหลด Whisper model เรียบร้อย.")

        # 3. ตั้งค่า PyAudio สำหรับการบันทึกเสียง
        pa = pyaudio.PyAudio()

        # ตรวจสอบและแสดงรายการไมโครโฟนที่มี
        print("\n--- Available Audio Input Devices ---")
        input_device_index = -1 
        for i in range(pa.get_device_count()):
            info = pa.get_device_info_by_index(i)
            if info["maxInputChannels"] > 0:
                print(f"Device {i}: {info['name']}")
        print("------------------------------------\n")

        # PyAudio Stream จะใช้ sample_rate และ frame_length ของ Porcupine
        audio_stream = pa.open(
            rate=porcupine.sample_rate, # ใช้ sample_rate ของ Porcupine (16kHz)
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length, # ใช้ frame_length ของ Porcupine (512 samples)
            input_device_index=input_device_index
        )

        print("พร้อมรับคำสั่งเสียง...")
        print(f"พูด '{KEYWORD_LABELS[0]}' เพื่อปลุกระบบ...")

        # 4. วนลูปเพื่อประมวลผลเสียง (Wake Word Detection)
        while True:
            pcm_porcupine = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm_porcupine = struct.unpack_from("h" * porcupine.frame_length, pcm_porcupine)

            result = porcupine.process(pcm_porcupine)

            # 5. ถ้าตรวจพบ Wake Word
            if result >= 0:
                print(f"\n!!! ตรวจพบคำสั่ง: {KEYWORD_LABELS[result]} !!!")
                print("เริ่มบันทึกเสียง...")

                # เริ่ม countdown timer ในเธรดแยก
                timer_thread = threading.Thread(target=countdown_timer)
                timer_thread.start()

                frames = [] # สำหรับเก็บข้อมูลเสียงที่จะบันทึก
                
                # บันทึกเสียงเป็นเวลา 5 วินาที
                frames_to_record = int(porcupine.sample_rate * RECORDING_DURATION / porcupine.frame_length)
                
                for _ in range(frames_to_record):
                    pcm_data = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
                    frames.append(pcm_data)
                
                # รอให้ timer thread เสร็จสิ้น
                timer_thread.join()
                
                print("\nกำลังประมวลผลคำสั่ง...")

                # 6. บันทึกเสียงที่ได้เป็นไฟล์ .wav ชั่วคราว
                temp_audio_file = os.path.join(TEMP_AUDIO_DIR, f"command_{int(time.time())}.wav")
                wf = wave.open(temp_audio_file, 'wb')
                wf.setnchannels(1)
                wf.setsampwidth(pa.get_sample_size(pyaudio.paInt16))
                wf.setframerate(porcupine.sample_rate)
                wf.writeframes(b''.join(frames))
                wf.close()

                # 7. ส่งไฟล์เสียงไปยัง Whisper Local Model
                try:
                    # ใช้ model.transcribe() ของ Whisper library
                    result_whisper = whisper_model.transcribe(
                        temp_audio_file, 
                        language=WHISPER_LANGUAGE # ระบุภาษา (เช่น "th" หรือ "en") หรือ None
                    )
                    final_transcript = result_whisper["text"].strip()
                    print(f"\n=== ผลการถอดเสียง ===")
                    print(f"คุณพูดว่า: \"{final_transcript}\"")
                    print("=====================")

                    # --- ตรงนี้คือส่วนที่คุณจะนำ final_transcript ไปประมวลผลต่อ ---
                    # เช่น:
                    # if "เปิดไฟ" in final_transcript.lower():
                    #     print("เปิดไฟ...")
                    # elif "กี่โมงแล้ว" in final_transcript.lower():
                    #     print("ตอนนี้เป็นเวลา 8 โมงเย็นครับ")
                    # ----------------------------------------------------

                except Exception as e:
                    print(f"เกิดข้อผิดพลาดในการถอดเสียงด้วย Whisper (Local): {e}")
                finally:
                    # 8. ลบไฟล์เสียงชั่วคราว
                    if os.path.exists(temp_audio_file):
                        os.remove(temp_audio_file)

                print(f"\nกลับสู่โหมด Wake Word Detection...")
                print(f"พูด '{KEYWORD_LABELS[0]}' เพื่อปลุกระบบ...")

    # --- การจัดการข้อผิดพลาด ---
    except pvporcupine.PorcupineInvalidArgumentError as e:
        print(f"\nError: Invalid argument passed to Porcupine. {e}")
        print("Please ensure your AccessKey is correct and valid, and keyword paths are correct.")
        print(f"Make sure '{CUSTOM_WAKE_WORD_PATH}' exists in the specified path.")
    except ImportError as e:
        print(f"\nError: A required library is not installed or configured correctly: {e}")
        if "pyaudio" in str(e).lower():
            print("Please install PyAudio: pip install pyaudio")
            print("If you have issues, you might need to install Visual C++ build tools or download a wheel file.")
        elif "whisper" in str(e).lower() or "openai_whisper" in str(e).lower():
            print("Please install Whisper AI: pip install -U openai-whisper")
            print("You might also need to install PyTorch: pip install torch torchvision torchaudio")
            print("For GPU support, follow PyTorch installation instructions specific to your CUDA version.")
        elif "porcupine" in str(e).lower():
            print("Please install Picovoice Porcupine: pip install picovoice-porcupine")
    except KeyboardInterrupt:
        print("\n\nโปรแกรมถูกหยุดโดยผู้ใช้ (Ctrl+C)")
    except Exception as e:
        print(f"\nเกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
        import traceback
        traceback.print_exc()
    
    # --- การทำความสะอาดทรัพยากร ---
    finally:
        if porcupine is not None:
            porcupine.delete() 
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()
        print("\nปิดโปรแกรม Wake Word Detector")

if __name__ == "__main__":
    main()