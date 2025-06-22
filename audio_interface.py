import platform
import importlib
from abc import ABC, abstractmethod

class AudioInterface(ABC):
    @abstractmethod
    def record_audio(self, filename, silence_threshold, silence_duration):
        pass
    
    @abstractmethod
    def play_audio(self, filename):
        pass
    
    @abstractmethod
    def text_to_speech(self, text, lang, filename):
        pass

def get_audio_handler():
    system = platform.system().lower()
    
    if system == "windows":
        try:
            audio_module = importlib.import_module("audio_windows")
            return audio_module.WindowsAudioHandler()
        except ImportError:
            pass
    
    elif system == "linux":
        try:
            audio_module = importlib.import_module("audio_linux")
            return audio_module.LinuxAudioHandler()
        except ImportError:
            pass
    
    elif system == "darwin":  # macOS
        try:
            audio_module = importlib.import_module("audio_macos")
            return audio_module.MacOSAudioHandler()
        except ImportError:
            pass
    
    # Fallback to default
    try:
        audio_module = importlib.import_module("audio_default")
        return audio_module.DefaultAudioHandler()
    except ImportError:
        raise RuntimeError("No audio handler available for this system")