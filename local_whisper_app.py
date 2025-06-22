import pyaudio
import wave
import whisper
import os
import time
import struct
import collections

# --- ตั้งค่าการบันทึกเสียง ---
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000  # สำหรับ Whisper แนะนำให้ใช้ 16kHz
CHUNK = 1024 # ขนาดบัฟเฟอร์
WAVE_OUTPUT_FILENAME = "recorded_audio.wav" # เปลี่ยนชื่อไฟล์ให้ชัดเจนขึ้น

# --- ตั้งค่าการตรวจจับความเงียบ ---
SILENCE_THRESHOLD = 1500 # ค่าความดังเสียงที่ถือว่าเงียบ (ปรับได้ตามไมโครโฟนและสภาพแวดล้อม)
SILENCE_DURATION = 2 # วินาทีที่ถือว่าเงียบแล้วหยุดบันทึก

# --- โหลดโมเดล Whisper (แบบ Local) ---
# โมเดลจะถูกโหลดเพียงครั้งเดียวตอนโปรแกรมเริ่มทำงาน
print("--- กำลังโหลดโมเดล Whisper (small)... นี่อาจใช้เวลาสักครู่ในครั้งแรก ---")
model = whisper.load_model("small")
print("--- โหลดโมเดลเสร็จสิ้น ---")

def record_audio_until_silence(filename=WAVE_OUTPUT_FILENAME,
                               silence_threshold=SILENCE_THRESHOLD,
                               silence_duration=SILENCE_DURATION):
    """
    บันทึกเสียงจากไมโครโฟน และหยุดบันทึกเมื่อตรวจพบความเงียบติดต่อกันตามที่กำหนด.
    Returns: ชื่อไฟล์เสียงที่บันทึกได้ หรือ None หากเกิดข้อผิดพลาด.
    """
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    print(f"--- กำลังบันทึกเสียง (พูดได้เลย! จะหยุดเมื่อเงียบ {silence_duration} วินาที)... ---")
    frames = []
    
    silence_frames_count = 0 # นับจำนวนเฟรมที่เงียบ
    start_record_time = time.time() # เวลาเริ่มต้นการบันทึกจริงจัง

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

            # แปลงข้อมูลเสียงเป็นตัวเลขเพื่อหาความดัง (RMS)
            audio_data = struct.unpack(str(len(data) // 2) + 'h', data)
            rms = sum([n * n for n in audio_data]) / len(audio_data)
            rms = rms**0.5

            # ตรวจสอบความเงียบ
            if rms < silence_threshold:
                silence_frames_count += 1
            else:
                silence_frames_count = 0 # รีเซ็ตเมื่อมีเสียงดังขึ้นมา

            # ถ้าเงียบติดต่อกันนานพอ ให้หยุดบันทึก
            if (silence_frames_count * CHUNK / RATE) >= silence_duration:
                print(f"--- ตรวจพบความเงียบ {silence_duration} วินาที หยุดบันทึก ---")
                break
            
            # จำกัดระยะเวลาบันทึกสูงสุด (เผื่อในกรณีที่ไม่เคยเงียบเลย)
            if time.time() - start_record_time > 20: # บันทึกไม่เกิน 20 วินาที
                print("--- บันทึกนานเกินไป หยุดอัตโนมัติ ---")
                break

    except Exception as e:
        print(f"เกิดข้อผิดพลาดขณะบันทึกเสียง: {e}")
        return None
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

        if not frames:
            print("ไม่สามารถบันทึกเสียงได้ (ไม่มีข้อมูลเสียง)")
            return None

        # บันทึกไฟล์ WAV
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"--- บันทึกเสียงเสร็จสิ้น: {filename} ---")
        return filename

def transcribe_audio_local(audio_file):
    """
    แปลงไฟล์เสียงเป็นข้อความโดยใช้ Whisper AI แบบ Local.
    Returns: ข้อความที่ถอดเสียงได้ หรือ None หากเกิดข้อผิดพลาด.
    """
    try:
        print("\n--- กำลังแปลงเสียงเป็นข้อความ (Local)... ---")
        start_time = time.time()
        result = model.transcribe(audio_file)
        end_time = time.time()
        text = result["text"]
        print(f"(ใช้เวลาแปลงเสียง: {end_time - start_time:.2f} วินาที)")
        return text
    except Exception as e:
        print(f"เกิดข้อผิดพลาดในการแปลงเสียง: {e}")
        return None

def process_voice_command():
    """
    เริ่มต้นจับเสียง บันทึกจนกว่าจะเงียบ แปลงเป็นข้อความ และคืนค่าข้อความนั้น.
    """
    print("--- เริ่มต้นการประมวลผลเสียง ---")
    
    audio_file = record_audio_until_silence()
    
    if audio_file:
        transcribed_text = transcribe_audio_local(audio_file)
        
        # ลบไฟล์เสียงชั่วคราวออก
        if os.path.exists(audio_file):
            os.remove(audio_file)
            
        if transcribed_text:
            print("\n--- ข้อความที่ถอดเสียงได้: ---")
            print(transcribed_text)
            return transcribed_text
        else:
            print("ไม่สามารถแปลงเสียงเป็นข้อความได้")
            return None
    else:
        print("ไม่สามารถบันทึกเสียงได้ จึงไม่ทำการแปลงเป็นข้อความ")
        return None

# --- Main execution block ---
if __name__ == "__main__":
    print("\n" + "="*50 + "\n")
    print("ระบบพร้อมรับคำสั่งเสียง...")
    
    # เรียกใช้ฟังก์ชันเพื่อเริ่มกระบวนการ
    command_text = process_voice_command()
    
    if command_text:
        print(f"\nคุณพูดว่า: '{command_text}'")
    else:
        print("\nไม่ได้รับคำสั่งเสียง หรือเกิดข้อผิดพลาดในการประมวลผล")

    print("\n" + "="*50 + "\n")
    print("--- สิ้นสุดการทำงานของโปรแกรม ---")