import pvporcupine
import pyaudio
import struct
import os

PICOVOICE_ACCESS_KEY = "8QZmFYrFufntomOJGZmf8nSm5BXB+4csXK98vqSdLJ37RZNR7RQc2w=="

CUSTOM_MODEL_FILENAME = "models/jarvis_en_windows_v3_0_0.ppn"
PATH_TO_CUSTOM_JARVIS_MODEL = os.path.join(os.path.dirname(__file__), CUSTOM_MODEL_FILENAME)

KEYWORD_LABELS = ['Jarvis (Custom)']

def listen_for_wake_word(detect_and_exit=False):
    print("Listening for wake word...")
    porcupine = None
    pa = None
    audio_stream = None

    try:
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_ACCESS_KEY,
            keyword_paths=[PATH_TO_CUSTOM_JARVIS_MODEL],
            sensitivities=[0.6]
        )

        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )

        while True:
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)

            result = porcupine.process(pcm)

            if result >= 0:
                return True

    except Exception as e:
        return False
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if pa is not None:
            pa.terminate()

if __name__ == "__main__":
    detected = listen_for_wake_word(detect_and_exit=True)