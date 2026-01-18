import json
import os
import math as m

DEFAULT_FILENAME = 'config.json'

DEFAULT_CONFIG = {
    "P_x": 0.54,
    "P_y": 0.73,
    "O_r": 0,
    "w": 2750,
    "O_b_deg": 70,
    "Z_sh": 0.15,
    "C_D": 0.6,
    "C_L": 0,
    "C_roll": 0.5
}

def load_config(filename=None):
    if not filename:
        filename = DEFAULT_FILENAME

    if not filename.endswith('.json'):
        filename += '.json'

    if not os.path.exists(filename):
        if filename == DEFAULT_FILENAME:
             save_config(DEFAULT_CONFIG, filename)
             return DEFAULT_CONFIG.copy()
        else:
             print(f"Config file {filename} not found, loading defaults.")
             return DEFAULT_CONFIG.copy()
    
    try:
        with open(filename, 'r') as f:
            config = json.load(f)
            # Ensure all keys exist
            for key, val in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = val
            print(f"Loaded config from {filename}")
            return config
    except Exception as e:
        print(f"Error loading config from {filename}, using defaults: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config, filename=None):
    if not filename:
        filename = DEFAULT_FILENAME
    
    if not filename.endswith('.json'):
        filename += '.json'

    try:
        with open(filename, 'w') as f:
            json.dump(config, f, indent=4)
        print(f"Configuration saved to {filename}")
    except Exception as e:
        print(f"Error saving config to {filename}: {e}")
