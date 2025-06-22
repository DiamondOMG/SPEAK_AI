import pyaudio
import wave
import struct
import time
import os
import pygame
from gtts import gTTS
from audio_interface import AudioInterface

class WindowsAudioHandler(AudioInterface):
    def __init__(self):
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024

    def record_audio(self, filename, silence_threshold=1500, silence_duration=2):
        audio = pyaudio.PyAudio()
        stream = audio.open(format=self.FORMAT, channels=self.CHANNELS,
                            rate=self.RATE, input=True,
                            frames_per_buffer=self.CHUNK)

        frames = []
        silence_frames_count = 0
        start_record_time = time.time()

        try:
            while True:
                data = stream.read(self.CHUNK, exception_on_overflow=False)
                frames.append(data)

                audio_data = struct.unpack(str(len(data) // 2) + 'h', data)
                rms = sum([n * n for n in audio_data]) / len(audio_data)
                rms = rms**0.5

                if rms < silence_threshold:
                    silence_frames_count += 1
                else:
                    silence_frames_count = 0

                if (silence_frames_count * self.CHUNK / self.RATE) >= silence_duration:
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
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(audio.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            return filename

    def play_audio(self, filename):
        try:
            pygame.mixer.quit()
            pygame.mixer.init()
            pygame.mixer.music.load(filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
            pygame.mixer.quit()
            return True
        except Exception as e:
            return False

    def text_to_speech(self, text, lang='th', filename="temp_audio.mp3"):
        try:
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(filename)
            return filename
        except Exception as e:
            return None