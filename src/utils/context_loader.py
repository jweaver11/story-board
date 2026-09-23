''' Loads our settings and contexts from JSON files '''
import os
import json
from dataclasses import asdict
from constants import SETTINGS_FILE_PATH, PAINT_SETTINGS_FILE_PATH, DRAWING_SETTINGS_FILE_PATH, TEXT_SETTINGS_FILE_PATH

def check_file(file_path: str, default_data: dict = None):
    ''' Checks if a file exists, and creates it with default data if it doesn't '''
    if not os.path.exists(file_path):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure directory exists
        with open(file_path, "w", encoding='utf-8') as f:
            json.dump(default_data if default_data is not None else {}, f)
        return False

def load_app_settings():
    ''' Loads our settings from a JSON file into our rendered settings control. If none exist, creates default settings '''
    from contexts.app_settings import AppSettings
    
    check_file(SETTINGS_FILE_PATH, default_data=asdict(AppSettings())) # Check the file exists
    
    try:
        # Read the JSON file
        with open(SETTINGS_FILE_PATH, "r", encoding='utf-8') as f:
            settings_data = json.load(f)

    # If no file exists, create one with default settings
    except(FileNotFoundError):
        print("Settings file not found, creating default settings.")
        settings_data = None  # If there's an error, we will create default settings
            
    # Other errors
    except Exception as e:
        print(f"Error loading settings {SETTINGS_FILE_PATH}: {e}")
        settings_data = None  # If there's an error, we will create default settings

    # Sets our app settings to our loaded settings. If none were loaded (I.E. first launch), Settings with create its own defaults
    return AppSettings(**(settings_data or {}))

def load_paint_settings():
    from contexts.paint_settings import PaintSettings
    
    check_file(PAINT_SETTINGS_FILE_PATH, default_data=asdict(PaintSettings()))
    
    try:
        with open(PAINT_SETTINGS_FILE_PATH, "r", encoding='utf-8') as f:
            paint_settings_data = json.load(f)
    except(FileNotFoundError):
        print("Paint settings file not found, creating default settings.")
        paint_settings_data = None
    except Exception as e:
        print(f"Error loading paint settings {PAINT_SETTINGS_FILE_PATH}: {e}")
        paint_settings_data = None

    return PaintSettings(**(paint_settings_data or {}))

def load_drawing_settings():
    from contexts.drawing_settings import DrawingSettings
    
    check_file(DRAWING_SETTINGS_FILE_PATH, default_data=asdict(DrawingSettings()))
    
    try:
        with open(DRAWING_SETTINGS_FILE_PATH, "r", encoding='utf-8') as f:
            drawing_settings_data = json.load(f)
    except(FileNotFoundError):
        print("Drawing settings file not found, creating default settings.")
        drawing_settings_data = None
    except Exception as e:
        print(f"Error loading drawing settings {DRAWING_SETTINGS_FILE_PATH}: {e}")
        drawing_settings_data = None

    return DrawingSettings(**(drawing_settings_data or {}))

def load_text_settings():
    from contexts.text_settings import TextSettings
    
    check_file(TEXT_SETTINGS_FILE_PATH, default_data=asdict(TextSettings()))
    
    try:
        with open(TEXT_SETTINGS_FILE_PATH, "r", encoding='utf-8') as f:
            text_settings_data = json.load(f)
    except(FileNotFoundError):
        print("Text settings file not found, creating default settings.")
        text_settings_data = None
    except Exception as e:
        print(f"Error loading text settings {TEXT_SETTINGS_FILE_PATH}: {e}")
        text_settings_data = None

    return TextSettings(**(text_settings_data or {}))