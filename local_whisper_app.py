import pyaudio
import wave
import whisper
import os
import time
import struct

FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
WAVE_OUTPUT_FILENAME = "recorded_audio.wav"

SILENCE_THRESHOLD = 1500
SILENCE_DURATION = 2

model = whisper.load_model("small")

def record_audio_until_silence(filename=WAVE_OUTPUT_FILENAME,
                               silence_threshold=SILENCE_THRESHOLD,
                               silence_duration=SILENCE_DURATION):
    audio = pyaudio.PyAudio()
    stream = audio.open(format=FORMAT, channels=CHANNELS,
                        rate=RATE, input=True,
                        frames_per_buffer=CHUNK)

    frames = []
    silence_frames_count = 0
    start_record_time = time.time()

    try:
        while True:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

            audio_data = struct.unpack(str(len(data) // 2) + 'h', data)
            rms = sum([n * n for n in audio_data]) / len(audio_data)
            rms = rms**0.5

            if rms < silence_threshold:
                silence_frames_count += 1
            else:
                silence_frames_count = 0

            if (silence_frames_count * CHUNK / RATE) >= silence_duration:
                break
            
            if time.time() - start_record_time > 20:
                break

    except Exception as e:
        return None
    finally:
        stream.stop_stream()
        stream.close()
        audio.terminate()

        if not frames:
            return None

        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        return filename

def transcribe_audio_local(audio_file):
    try:
        result = model.transcribe(audio_file)
        return result["text"]
    except Exception as e:
        return None

def process_voice_command():
    print("กำลังบันทึกเสียง... พูดคำสั่งของคุณ (กด Ctrl+C เพื่อหยุด)")
    audio_file = record_audio_until_silence()
    
    if audio_file:
        transcribed_text = transcribe_audio_local(audio_file)
        
        if os.path.exists(audio_file):
            os.remove(audio_file)
            
        if transcribed_text:
            return transcribed_text
        else:
            return None
    else:
        return None

if __name__ == "__main__":
    command_text = process_voice_command()
    
    if command_text:
        print(f"คุณพูดว่า: '{command_text}'")
    else:
        print("ไม่ได้รับคำสั่งเสียง")