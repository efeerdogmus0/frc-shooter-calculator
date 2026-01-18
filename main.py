import math as m
import sys
from PyQt6.QtWidgets import QApplication
import config
import gui

def main():
    print("Loading configuration...")
    cfg_data = config.load_config()
    
    # Pre-process config
    params = cfg_data.copy()
    
    if 'O_b_deg' in params:
        params['O_b'] = m.radians(params['O_b_deg'])
    
    if 'O_r_deg' in params:
        params['O_r'] = m.radians(params['O_r_deg'])
    else:
        params['O_r'] = m.radians(params.get('O_r', 0))

    print("Starting GUI (Qt)...")
    app = QApplication(sys.argv)
    window = gui.ShooterGUI(params)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
