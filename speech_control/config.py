"""
Configuration settings for Speech Recognition Desktop Application
"""

import os
import json

class Config:
    """Application configuration"""
    
    # Database settings
    DATABASE_PATH = "speech_recognition.db"
    
    # Speech recognition settings
    SPEECH_RECOGNITION_TIMEOUT = 1
    SPEECH_RECOGNITION_PHRASE_LIMIT = 5
    DEFAULT_CONFIDENCE_THRESHOLD = 0.7
    
    # Text-to-speech settings
    TTS_RATE = 150
    TTS_VOLUME = 0.8
    
    # UI settings
    WINDOW_WIDTH = 1200
    WINDOW_HEIGHT = 800
    THEME = "default"
    
    # System settings
    AUTO_START_LISTENING = False
    ENABLE_WAKE_WORD = True
    DEFAULT_WAKE_WORD = "hey moody"
    
    # AI integration settings
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    USE_ONLINE_AI = False
    
    # Logging settings
    LOG_LEVEL = "INFO"
    LOG_FILE = "speech_recognition.log"
    
    @classmethod
    def load_from_file(cls, config_file="config.json"):
        """Load configuration from JSON file"""
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                    
                for key, value in config_data.items():
                    if hasattr(cls, key.upper()):
                        setattr(cls, key.upper(), value)
                        
            except Exception as e:
                print(f"Error loading config: {e}")
    
    @classmethod
    def save_to_file(cls, config_file="config.json"):
        """Save configuration to JSON file"""
        config_data = {}
        
        for attr in dir(cls):
            if not attr.startswith('_') and not callable(getattr(cls, attr)):
                config_data[attr.lower()] = getattr(cls, attr)
        
        try:
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception as e:
            print(f"Error saving config: {e}")

# Load configuration on import
Config.load_from_file()
