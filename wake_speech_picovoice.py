import os
import pvporcupine
import pyaudio
import struct
import sys
import pvcheetah # เพิ่ม import สำหรับ Picovoice Cheetah

# --- การตั้งค่าหลัก ---

# แทนที่ด้วย AccessKey ของคุณจาก Picovoice Console
PICOVOICE_ACCESS_KEY = "8QZmFYrFufntomOJGZmf8nSm5BXB+4csXK98vqSdLJ37RZNR7RQc2w==" 

# ** กำหนด Path ไปยังไฟล์ .ppn ที่คุณสร้างขึ้นมาเอง **
# ไฟล์ jarvis_en_windows_v3_0_0.ppn ควรอยู่ในโฟลเดอร์ SPEAKER_AI/models/
CUSTOM_WAKE_WORD_PATH = os.path.join("models", "jarvis_en_windows_v3_0_0.ppn")

# ใช้ argument 'keyword_paths' สำหรับ Custom Wake Word
KEYWORD_PATHS_TO_USE = [CUSTOM_WAKE_WORD_PATH]
KEYWORD_LABELS = ["Jarvis (Custom)"] # ตั้งชื่อ Label เพื่อให้แสดงผลได้ถูกต้อง

# คุณสามารถกำหนด sensitivity ได้ด้วย (ค่าระหว่าง 0.0 ถึง 1.0)
CUSTOM_SENSITIVITIES = [0.7] # ลองปรับค่านี้ดูครับ 0.6-0.8 มักเป็นค่าที่ดี

# --- การตั้งค่า Cheetah ---
# ภาษาสำหรับ Cheetah (เช่น "en" สำหรับอังกฤษ, "th" สำหรับไทย)
# ตรวจสอบว่า AccessKey ของคุณรองรับภาษาไทยสำหรับ Cheetah หรือไม่
CHEETAH_LANGUAGE = "en" 
# ถ้ามี Custom Language Model สำหรับ Cheetah (ไฟล์ .pv)
# CHEETAH_MODEL_PATH = os.path.join("models", "your_custom_cheetah_model.pv") # หากมี
CHEETAH_MODEL_PATH = None # ถ้าไม่มี ให้ตั้งเป็น None เพื่อใช้ Default English model

# --- ฟังก์ชันหลัก ---

def main():
    print("กำลังเริ่มต้น Porcupine Wake Word Detector และ Cheetah STT...")
    print(f"กำลังฟังคำสั่ง: {', '.join(KEYWORD_LABELS)}")

    porcupine = None
    cheetah = None
    pa = None
    audio_stream = None

    try:
        # 1. สร้าง Instance ของ Porcupine Engine
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keyword_paths=KEYWORD_PATHS_TO_USE,
            sensitivities=CUSTOM_SENSITIVITIES
        )

        # 2. สร้าง Instance ของ Cheetah Engine
        # Cheetah 250 minutes/month (ตรวจสอบโควต้าของคุณ)
        print(f"กำลังสร้าง Cheetah model...") # เปลี่ยนข้อความให้ถูกต้อง
        cheetah = pvcheetah.create( #
            access_key=PICOVOICE_ACCESS_KEY, #
            endpoint_duration_sec=1.5, # กำหนดระยะเวลาเงียบก่อนจะถือว่าจบประโยค (วินาที)
            enable_automatic_punctuation=True, # เปิดใช้งานการใส่เครื่องหมายวรรคตอนอัตโนมัติ
            model_path=CHEETAH_MODEL_PATH # ใช้ Custom Model ถ้ามี
        )
        print("สร้าง Cheetah model เรียบร้อย.")

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

        # ใช้ sample_rate และ frame_length จาก Cheetah สำหรับ Audio Stream เพื่อความเข้ากันได้ดีที่สุด
        audio_stream = pa.open(
            rate=cheetah.sample_rate, # ใช้ sample_rate ของ Cheetah
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=cheetah.frame_length, # ใช้ frame_length ของ Cheetah
            input_device_index=input_device_index
        )

        print("พร้อมรับคำสั่งเสียง...")
        print(f"พูด '{KEYWORD_LABELS[0]}' เพื่อปลุกระบบ...")

        # 4. วนลูปเพื่อประมวลผลเสียง (Wake Word Detection)
        while True:
            # อ่านข้อมูลเสียงจากไมโครโฟนเพื่อตรวจจับ Wake Word
            # Note: Porcupine และ Cheetah มี sample_rate และ frame_length ที่เข้ากันได้ดี
            # โดยทั่วไปจะเป็น 16kHz และ 512 samples
            pcm_porcupine = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm_porcupine = struct.unpack_from("h" * porcupine.frame_length, pcm_porcupine)

            result = porcupine.process(pcm_porcupine)

            # 5. ถ้าตรวจพบ Wake Word
            if result >= 0:
                print(f"\n!!! ตรวจพบคำสั่ง: {KEYWORD_LABELS[result]} !!!")
                print("โปรดพูดคำสั่งของคุณ... (ระบบจะประมวลผลเมื่อคุณหยุดพูด)")

                cheetah_transcript_buffer = "" # เก็บ partial transcript
                
                # เข้าสู่โหมดฟังคำสั่ง (Streaming STT ด้วย Cheetah)
                while True:
                    # อ่านข้อมูลเสียงสำหรับ Cheetah
                    pcm_cheetah = audio_stream.read(cheetah.frame_length, exception_on_overflow=False)
                    pcm_cheetah = struct.unpack_from("h" * cheetah.frame_length, pcm_cheetah)

                    # ส่งข้อมูลเสียงให้ Cheetah ประมวลผล
                    partial_transcript, is_endpoint = cheetah.process(pcm_cheetah) #
                    
                    if partial_transcript:
                        cheetah_transcript_buffer += partial_transcript
                        sys.stdout.write(f"\rPartial: {cheetah_transcript_buffer.strip()}") # แสดงผลแบบ real-time
                        sys.stdout.flush()

                    # ถ้าตรวจพบว่าผู้ใช้หยุดพูด (endpoint)
                    if is_endpoint: 
                        # cheetah.flush() คืนค่าเป็น string ของ transcript โดยตรงในเวอร์ชันนี้
                        final_transcript = cheetah_transcript_buffer + cheetah.flush() # <-- แก้ไขบรรทัดนี้
                        sys.stdout.write("\r" + " " * 80 + "\r") 
                        sys.stdout.flush()
                        print(f"คุณพูดว่า: \"{final_transcript.strip()}\"")
                        
                        # --- ตรงนี้คือส่วนที่คุณจะนำ final_transcript ไปประมวลผลต่อ ---
                        # เช่น:
                        # if "turn on the light" in final_transcript.lower():
                        #     print("เปิดไฟ...")
                        # elif "what time is it" in final_transcript.lower():
                        #     print("ตอนนี้เป็นเวลา 8 โมงเย็นครับ")
                        # หรือส่งไปให้ LLM API เช่น Gemini
                        # ----------------------------------------------------
                        cheetah_transcript_buffer = "" # รีเซ็ต buffer สำหรับคำสั่งถัดไป
                        break # ออกจากลูปฟังคำสั่งและกลับไปฟัง Wake Word

                print("\nพร้อมรับคำสั่งเสียงอีกครั้ง...") 
                print(f"พูด '{KEYWORD_LABELS[0]}' เพื่อปลุกระบบ...")


    # --- การจัดการข้อผิดพลาด ---
    except pvporcupine.PorcupineInvalidArgumentError as e:
        print(f"\nError: Invalid argument passed to Porcupine. {e}")
        print("Please ensure your AccessKey is correct and valid, and keyword paths are correct.")
        print(f"Make sure '{CUSTOM_WAKE_WORD_PATH}' exists in the specified path.")
    except pvcheetah.CheetahInvalidArgumentError as e:
        print(f"\nError: Invalid argument passed to Cheetah. {e}")
        print("Please ensure your AccessKey is correct and valid, and language/model path are supported.")
    except ImportError as e:
        print(f"\nError: A required library is not installed or configured correctly: {e}")
        if "pyaudio" in str(e).lower():
            print("Please install PyAudio: pip install pyaudio")
            print("If you have issues, you might need to install Visual C++ build tools or download a wheel file.")
        elif "cheetah" in str(e).lower():
            print("Please install Picovoice Cheetah: pip install picovoice-cheetah")
    except Exception as e:
        print(f"\nเกิดข้อผิดพลาดที่ไม่คาดคิด: {e}")
        import traceback
        traceback.print_exc()
    
    # --- การทำความสะอาดทรัพยากร ---
    finally:
        if porcupine is not None:
            porcupine.delete() 
        if cheetah is not None:
            cheetah.delete() # สำคัญ: ต้อง release resources ของ Cheetah ด้วย
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()
        print("\nปิดโปรแกรม Wake Word Detector")

if __name__ == "__main__":
    main()