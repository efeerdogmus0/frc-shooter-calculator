from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QDoubleSpinBox, QPushButton, QComboBox, QGroupBox,
    QTabWidget, QScrollArea, QFileDialog, QSizePolicy
)
from PyQt6.QtCore import Qt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import math as m
import os
import glob
import simulation as sim
import config as cfg

# Constants
L_x = sim.L_x
L_y = sim.L_y
H_H = sim.H_H
H_H2 = sim.H_H2
H_Shoot = sim.H_Shoot

class MplCanvas(FigureCanvas):
    def __init__(self, width=5, height=4, dpi=100, is_3d=False):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        if is_3d:
            self.axes = self.fig.add_subplot(111, projection='3d')
        else:
            self.axes = self.fig.add_subplot(111)
        super(MplCanvas, self).__init__(self.fig)

class ShooterGUI(QMainWindow):
    def __init__(self, initial_params):
        super().__init__()
        self.setWindowTitle("FRC Shooter Simulation (PyQt6)")
        self.resize(1200, 800)
        
        self.params = initial_params.copy()
        
        # Main Layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Left Side: Plots (Tabs)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs, stretch=2)
        
        # Tab 1: 2D Plot
        self.canvas_2d = MplCanvas(width=5, height=4, dpi=100, is_3d=False)
        self.tabs.addTab(self.canvas_2d, "2D View")
        
        # Tab 2: 3D Plot
        self.canvas_3d = MplCanvas(width=5, height=4, dpi=100, is_3d=True)
        self.tabs.addTab(self.canvas_3d, "3D View")
        
        # Right Side: Controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        
        controls_widget = QWidget()
        controls_layout = QVBoxLayout(controls_widget)
        scroll.setWidget(controls_widget)
        
        main_layout.addWidget(scroll, stretch=1)
        
        # --- Control Groups ---
        
        # 1. Config / File I/O
        io_group = QGroupBox("Configuration")
        io_layout = QVBoxLayout(io_group)
        
        self.file_combo = QComboBox()
        self.refresh_file_list()
        self.file_combo.currentTextChanged.connect(self.on_combo_changed)
        io_layout.addWidget(QLabel("Select Config File:"))
        io_layout.addWidget(self.file_combo)
        
        btn_layout = QHBoxLayout()
        self.btn_load = QPushButton("Load from File...")
        self.btn_load.clicked.connect(self.on_load_clicked)
        self.btn_save = QPushButton("Save")
        self.btn_save.clicked.connect(self.on_save)
        self.btn_save_as = QPushButton("Save As...")
        self.btn_save_as.clicked.connect(self.on_save_as)
        
        btn_layout.addWidget(self.btn_load)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_save_as)
        io_layout.addLayout(btn_layout)
        
        controls_layout.addWidget(io_group)
        
        # 2. Shooter Params
        shooter_group = QGroupBox("Shooter Parameters")
        shooter_layout = QVBoxLayout(shooter_group)
        
        # Helper to create inputs
        self.inputs = {}
        
        # Angle
        self.inputs['angle'] = self.create_slider_input(
            shooter_layout, "Angle (deg)", 10, 80, 
            m.degrees(self.params['O_b']), 0.1
        )
        # RPM
        self.inputs['rpm'] = self.create_slider_input(
            shooter_layout, "Wheel RPM", 1000, 5000, 
            self.params['w'], 10
        )
        # C_roll
        self.inputs['C_roll'] = self.create_slider_input(
            shooter_layout, "C_roll", 0, 1, 
            self.params['C_roll'], 0.01
        )
        # C_D
        self.inputs['C_D'] = self.create_slider_input(
            shooter_layout, "C_D", 0, 1, 
            self.params['C_D'], 0.01
        )
        # C_L
        self.inputs['C_L'] = self.create_slider_input(
            shooter_layout, "C_L", 0, 1, 
            self.params['C_L'], 0.01
        )
        
        controls_layout.addWidget(shooter_group)
        
        # 3. Position Params (3D)
        pos_group = QGroupBox("Position Parameters")
        pos_layout = QVBoxLayout(pos_group)
        
        self.inputs['P_x'] = self.create_slider_input(
            pos_layout, "P_x (m)", 0, L_x, 
            self.params['P_x'], 0.05
        )
        self.inputs['P_y'] = self.create_slider_input(
            pos_layout, "P_y (m)", 0, L_y, 
            self.params['P_y'], 0.05
        )
        self.inputs['O_r'] = self.create_slider_input(
            pos_layout, "O_r (deg)", -90, 90, 
            m.degrees(self.params['O_r']), 0.5
        )

        controls_layout.addWidget(pos_group)
        controls_layout.addStretch()

        # Initial Draw
        self.update_plots()

    def create_slider_input(self, parent_layout, label_text, min_val, max_val, init_val, step):
        # Container
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0,0,0,0)
        
        # Label + SpinBox Row
        top_row = QHBoxLayout()
        label = QLabel(label_text)
        spin = QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(init_val)
        spin.setSingleStep(step)
        
        top_row.addWidget(label)
        top_row.addWidget(spin)
        layout.addLayout(top_row)
        
        # Slider Row
        slider = QSlider(Qt.Orientation.Horizontal)
        # Map float range to integer range (0-1000 or similar based on precision)
        # Let's say we want 1000 steps
        self.slider_steps = 1000
        slider.setRange(0, self.slider_steps)
        
        # Helper conversions
        def val_to_slider(v):
            return int((v - min_val) / (max_val - min_val) * self.slider_steps)
            
        def slider_to_val(s):
            return min_val + (s / self.slider_steps) * (max_val - min_val)
            
        slider.setValue(val_to_slider(init_val))
        layout.addWidget(slider)
        
        parent_layout.addWidget(container)
        
        # Connect signals
        # Use lambda with captured variables properly
        spin.valueChanged.connect(lambda v: self.on_spin_change(v, slider, val_to_slider))
        slider.valueChanged.connect(lambda v: self.on_slider_change(v, spin, slider_to_val))
        
        return spin  # Return spinbox as the "source of truth" control handle

    def on_spin_change(self, val, slider, converter):
        slider.blockSignals(True)
        slider.setValue(converter(val))
        slider.blockSignals(False)
        self.update_params_and_plot()

    def on_slider_change(self, val, spin, converter):
        spin.blockSignals(True)
        spin.setValue(converter(val))
        spin.blockSignals(False)
        self.update_params_and_plot()

    def update_params_and_plot(self):
        # Read all inputs
        self.params['O_b'] = m.radians(self.inputs['angle'].value())
        self.params['w'] = self.inputs['rpm'].value()
        self.params['C_roll'] = self.inputs['C_roll'].value()
        self.params['C_D'] = self.inputs['C_D'].value()
        self.params['C_L'] = self.inputs['C_L'].value()
        
        self.params['P_x'] = self.inputs['P_x'].value()
        self.params['P_y'] = self.inputs['P_y'].value()
        self.params['O_r'] = m.radians(self.inputs['O_r'].value())
        
        self.update_plots()

    def update_plots(self):
        # Calc simulation
        res = sim.calculate_simulation(self.params)
        iPoints, ideal_point, frPoints, frIdealPoint, iPoints_xyz, frPoints_xyz = res
        
        # 2D Plot
        ax2 = self.canvas_2d.axes
        ax2.cla()
        ax2.set_xlim(0, L_x * 1.5)
        ax2.set_ylim(0, H_H + H_H2 + 1)
        ax2.set_aspect('equal', adjustable='box')
        ax2.grid(True)
        ax2.set_title('Projectile Motion (2D)')
        
        sim.plotIdeal2D(ax2, iPoints, ideal_point)
        sim.plotFriction2D(ax2, frPoints, frIdealPoint)
        self.canvas_2d.draw()
        
        # 3D Plot
        ax3 = self.canvas_3d.axes
        ax3.cla()
        ax3.set_xlim(0, L_x * 1.5)
        ax3.set_ylim(0, L_y)
        ax3.set_zlim(0, H_H + H_H2 + 1)
        ax3.set_xlabel('X')
        ax3.set_ylabel('Y')
        ax3.set_zlabel('Z')
        ax3.view_init(elev=40, azim=235)
        
        sim.draw_field(ax3)
        sim.plotIdeal3D(ax3, iPoints_xyz)
        sim.plotFriction3D(ax3, frPoints_xyz)
        self.canvas_3d.draw()

    def refresh_file_list(self):
        self.file_combo.clear()
        files = glob.glob("*.json")
        if not files:
            files = ["config.json"] # default fallback
        
        self.file_combo.addItems(sorted(files))
        # Select current file if possible? Default to first.

    def on_combo_changed(self, text):
        if not text:
            return
        # Avoid reloading if it matches current params? 
        # For simplicity, just load.
        self.load_from_file(text)

    def on_load_clicked(self):
        fname, _ = QFileDialog.getOpenFileName(self, "Open Config", "", "JSON Files (*.json)")
        if fname:
            self.load_from_file(fname)
            # Optionally refresh list if it's a new file in same dir
            if os.path.dirname(fname) == os.getcwd() or os.path.dirname(fname) == "":
                 base = os.path.basename(fname)
                 if self.file_combo.findText(base) == -1:
                     self.file_combo.addItem(base)
                     self.file_combo.setCurrentText(base)

    def load_from_file(self, filename):
        print(f"Loading {filename}...")
        new_cfg = cfg.load_config(filename)
        self.apply_config(new_cfg)
        print("Loaded.")

    def apply_config(self, new_cfg):
        # Convert internal values
        if 'O_b_deg' in new_cfg:
            new_cfg['O_b'] = m.radians(new_cfg['O_b_deg'])
        if 'O_r_deg' in new_cfg:
            new_cfg['O_r'] = m.radians(new_cfg['O_r_deg'])
        else:
             new_cfg['O_r'] = m.radians(new_cfg.get('O_r', 0))

        self.params = new_cfg
        
        # Update inputs (signals will trigger redraw, blocking signals to avoid multiple redraws)
        self.inputs['angle'].blockSignals(True)
        self.inputs['angle'].setValue(m.degrees(self.params['O_b']))
        self.inputs['angle'].blockSignals(False)
        
        self.inputs['rpm'].setValue(self.params['w'])
        self.inputs['C_roll'].setValue(self.params['C_roll'])
        self.inputs['C_D'].setValue(self.params['C_D'])
        self.inputs['C_L'].setValue(self.params['C_L'])
        self.inputs['P_x'].setValue(self.params['P_x'])
        self.inputs['P_y'].setValue(self.params['P_y'])
        self.inputs['O_r'].setValue(m.degrees(self.params['O_r']))
        
        # Force single redraw
        self.update_params_and_plot()

    def on_save(self):
        filename = self.file_combo.currentText()
        if not filename:
            filename = "config.json"
        
        self.save_to_file(filename)

    def on_save_as(self):
        # QFileDialog inside Docker might look rudimentary but should work
        fname, _ = QFileDialog.getSaveFileName(self, "Save Config", "", "JSON Files (*.json)")
        if fname:
            if not fname.endswith('.json'):
                fname += '.json'
            self.save_to_file(fname)
            self.refresh_file_list()
            # Select the new file
            index = self.file_combo.findText(os.path.basename(fname))
            if index >= 0:
                self.file_combo.setCurrentIndex(index)

    def save_to_file(self, filename):
        save_data = self.params.copy()
        save_data['O_b_deg'] = m.degrees(save_data['O_b'])
        save_data['O_r_deg'] = m.degrees(save_data['O_r'])
        del save_data['O_b']
        del save_data['O_r']
        
        cfg.save_config(save_data, filename)

    def show(self):
        super().show()
