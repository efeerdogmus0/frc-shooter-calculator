from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QSlider, QDoubleSpinBox, QPushButton, QComboBox, QGroupBox,
    QTabWidget, QScrollArea, QFileDialog, QSizePolicy, QCheckBox,
    QFrame, QSpinBox, QMessageBox
)
from PyQt6.QtCore import Qt, QTimer
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
        
        # Debounce timer for performance - prevents excessive recalculation
        self._update_timer = QTimer()
        self._update_timer.setSingleShot(True)
        self._update_timer.setInterval(100)  # 100ms debounce
        self._update_timer.timeout.connect(self._do_update)
        
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
        
        # Tab 2: 3D Plot with help button
        tab3d_widget = QWidget()
        tab3d_layout = QVBoxLayout(tab3d_widget)
        tab3d_layout.setContentsMargins(0, 0, 0, 0)
        
        # Help button row
        help_row = QHBoxLayout()
        help_row.addStretch()
        self.btn_3d_help = QPushButton("❓ Legend")
        self.btn_3d_help.setFixedWidth(100)
        self.btn_3d_help.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 5px 10px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        self.btn_3d_help.clicked.connect(self.show_3d_legend)
        help_row.addWidget(self.btn_3d_help)
        tab3d_layout.addLayout(help_row)
        
        self.canvas_3d = MplCanvas(width=5, height=4, dpi=100, is_3d=True)
        tab3d_layout.addWidget(self.canvas_3d)
        
        self.tabs.addTab(tab3d_widget, "3D View")
        
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
        
        # 4. Optimal Angle Calculator
        optimal_group = QGroupBox("🎯 Optimal Angle Calculator")
        optimal_layout = QVBoxLayout(optimal_group)
        
        # Target distance input
        dist_row = QHBoxLayout()
        dist_row.addWidget(QLabel("Target Distance (m):"))
        self.target_distance_spin = QDoubleSpinBox()
        self.target_distance_spin.setRange(0.5, 10.0)
        self.target_distance_spin.setValue(3.0)
        self.target_distance_spin.setSingleStep(0.1)
        dist_row.addWidget(self.target_distance_spin)
        optimal_layout.addLayout(dist_row)
        
        # Calculate button
        self.btn_calc_optimal = QPushButton("Calculate Optimal Angle")
        self.btn_calc_optimal.clicked.connect(self.on_calculate_optimal)
        self.btn_calc_optimal.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        optimal_layout.addWidget(self.btn_calc_optimal)
        
        # Result display
        self.optimal_result_label = QLabel("Click to calculate...")
        self.optimal_result_label.setWordWrap(True)
        self.optimal_result_label.setStyleSheet("background-color: #f0f0f0; padding: 8px; border-radius: 4px;")
        optimal_layout.addWidget(self.optimal_result_label)
        
        # Apply optimal button
        self.btn_apply_optimal = QPushButton("Apply Optimal Angle")
        self.btn_apply_optimal.clicked.connect(self.on_apply_optimal)
        self.btn_apply_optimal.setEnabled(False)
        optimal_layout.addWidget(self.btn_apply_optimal)
        
        controls_layout.addWidget(optimal_group)
        
        # 5. Impact Zone Settings
        impact_group = QGroupBox("🎪 Impact Zone Visualization")
        impact_layout = QVBoxLayout(impact_group)
        
        self.show_impact_zone = QCheckBox("Show Impact Zone (3D)")
        self.show_impact_zone.setChecked(True)
        self.show_impact_zone.stateChanged.connect(self.update_params_and_plot)
        impact_layout.addWidget(self.show_impact_zone)
        
        # Variance controls
        var_row1 = QHBoxLayout()
        var_row1.addWidget(QLabel("Angle variance (±deg):"))
        self.angle_variance_spin = QDoubleSpinBox()
        self.angle_variance_spin.setRange(0.5, 5.0)
        self.angle_variance_spin.setValue(2.0)
        self.angle_variance_spin.setSingleStep(0.5)
        self.angle_variance_spin.valueChanged.connect(self.update_params_and_plot)
        var_row1.addWidget(self.angle_variance_spin)
        impact_layout.addLayout(var_row1)
        
        var_row2 = QHBoxLayout()
        var_row2.addWidget(QLabel("RPM variance (±%):"))
        self.rpm_variance_spin = QDoubleSpinBox()
        self.rpm_variance_spin.setRange(1.0, 10.0)
        self.rpm_variance_spin.setValue(3.0)
        self.rpm_variance_spin.setSingleStep(0.5)
        self.rpm_variance_spin.valueChanged.connect(self.update_params_and_plot)
        var_row2.addWidget(self.rpm_variance_spin)
        impact_layout.addLayout(var_row2)
        
        controls_layout.addWidget(impact_group)
        
        # 6. Statistics Panel
        stats_group = QGroupBox("📊 Shot Statistics")
        stats_layout = QVBoxLayout(stats_group)
        self.stats_label = QLabel("Calculating...")
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("font-family: monospace; background-color: #1e1e1e; color: #00ff00; padding: 10px; border-radius: 4px;")
        stats_layout.addWidget(self.stats_label)
        controls_layout.addWidget(stats_group)
        
        controls_layout.addStretch()
        
        # Store last optimal result
        self._last_optimal_result = None

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
        """Schedule an update with debounce to prevent excessive recalculation."""
        self._update_timer.start()  # Restarts the timer if already running
    
    def _do_update(self):
        """Actually perform the parameter update and redraw plots."""
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
        
        # Calculate impact zone if enabled
        impact_zone = None
        if self.show_impact_zone.isChecked():
            impact_zone = sim.calculate_impact_zone(
                self.params,
                angle_variance_deg=self.angle_variance_spin.value(),
                rpm_variance_pct=self.rpm_variance_spin.value()
            )
        
        # Update statistics
        self.update_statistics(frIdealPoint, impact_zone)
        
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
        
        # Draw impact zone if enabled
        if impact_zone and self.show_impact_zone.isChecked():
            sim.draw_impact_zone(ax3, impact_zone)
        
        self.canvas_3d.draw()
    
    def update_statistics(self, frIdealPoint, impact_zone):
        """Update the statistics display panel."""
        stats_lines = []
        
        # Flight info
        if frIdealPoint:
            stats_lines.append(f"Distance:     {frIdealPoint[0]:.2f} m")
            stats_lines.append(f"Flight Time:  {frIdealPoint[2]:.3f} s")
            stats_lines.append(f"Target Height:{frIdealPoint[1]:.2f} m")
        else:
            stats_lines.append("Ball does not reach target height")
        
        stats_lines.append("─" * 25)
        
        # Impact zone info
        if impact_zone:
            stats_lines.append(f"Accuracy:     {impact_zone['target_probability']:.0f}%")
            stats_lines.append(f"Spread:       {impact_zone['radius']*100:.1f} cm")
            stats_lines.append(f"Max Height:   {impact_zone['max_height']:.2f} m")
            
            if impact_zone['in_target']:
                stats_lines.append("Status:       ✅ ON TARGET")
            else:
                stats_lines.append("Status:       ❌ OFF TARGET")
        
        self.stats_label.setText("\n".join(stats_lines))
    
    def on_calculate_optimal(self):
        """Calculate the optimal angle for the target distance."""
        target_dist = self.target_distance_spin.value()
        
        self.optimal_result_label.setText("Calculating...")
        self.optimal_result_label.repaint()
        
        result = sim.calculate_optimal_angle(self.params, target_dist)
        self._last_optimal_result = result
        
        if result['success']:
            text = f"✅ Optimal Angle: {result['optimal_angle_deg']:.1f}°\n"
            text += f"Flight Time: {result['flight_time']:.3f}s\n"
            text += f"Landing Error: {result['error']*100:.1f}cm"
            self.optimal_result_label.setStyleSheet("background-color: #c8e6c9; padding: 8px; border-radius: 4px;")
            self.btn_apply_optimal.setEnabled(True)
        else:
            text = f"⚠️ {result['message']}\n"
            text += f"Best angle: {result['optimal_angle_deg']:.1f}°\n"
            text += f"Consider increasing RPM"
            self.optimal_result_label.setStyleSheet("background-color: #ffcdd2; padding: 8px; border-radius: 4px;")
            self.btn_apply_optimal.setEnabled(True)
        
        self.optimal_result_label.setText(text)
    
    def on_apply_optimal(self):
        """Apply the calculated optimal angle."""
        if self._last_optimal_result:
            optimal_angle = self._last_optimal_result['optimal_angle_deg']
            self.inputs['angle'].setValue(optimal_angle)
            # This will trigger update_params_and_plot via signal
    
    def show_3d_legend(self):
        """Show a legend explaining all 3D graph elements."""
        legend_text = """
<h2>🎯 3D Grafik Açıklaması / 3D Graph Legend</h2>

<h3>📍 Trajektori Çizgileri / Trajectory Lines</h3>
<table border="1" cellpadding="5">
<tr><td style="background-color: black; color: white;">■ Siyah / Black</td>
    <td><b>İdeal Trajektori / Ideal Trajectory</b><br>
    Hava direnci olmadan / Without air resistance</td></tr>
<tr><td style="background-color: green; color: white;">■ Yeşil / Green</td>
    <td><b>Gerçekçi Trajektori / Realistic Trajectory</b><br>
    Hava direnci + Magnus etkisi / With drag + Magnus effect</td></tr>
</table>

<h3>🏟️ Saha Elemanları / Field Elements</h3>
<table border="1" cellpadding="5">
<tr><td style="background-color: gray;">■ Gri / Gray</td>
    <td><b>Zemin ve Duvarlar / Ground & Walls</b><br>
    FRC sahası sınırları / FRC field boundaries</td></tr>
<tr><td style="background-color: purple; color: white;">■ Mor / Purple</td>
    <td><b>Hub (Hedef / Target)</b><br>
    Topun girmesi gereken hedef / Ball scoring target</td></tr>
<tr><td style="background-color: black; color: white;">■ Siyah / Black Lines</td>
    <td><b>Hub Direği / Hub Post</b><br>
    Hub'ı tutan yapı / Supporting structure</td></tr>
</table>

<h3>🎪 İsabet Zonu / Impact Zone</h3>
<table border="1" cellpadding="5">
<tr><td style="background-color: red; color: white;">● Kırmızı / Red Dots</td>
    <td><b>Olası Düşme Noktaları / Possible Landing Points</b><br>
    Açı ve RPM varyansına göre / Based on angle & RPM variance</td></tr>
<tr><td style="background-color: red; color: white;">○ Kırmızı Daire / Red Circle</td>
    <td><b>Yayılma Alanı / Spread Area</b><br>
    Tüm noktaları kapsayan / Encompasses all points</td></tr>
<tr><td style="background-color: yellow;">★ Sarı Yıldız / Yellow Star</td>
    <td><b>Merkez Nokta / Center Point</b><br>
    Ortalama düşme noktası / Average landing position</td></tr>
</table>

<h3>📐 Eksenler / Axes</h3>
<ul>
<li><b>X:</b> Sahanın uzunluğu / Field length (robot → hub)</li>
<li><b>Y:</b> Sahanın genişliği / Field width</li>
<li><b>Z:</b> Yükseklik / Height</li>
</ul>

<h3>🎮 Kontroller / Controls</h3>
<ul>
<li><b>Sol tık + sürükle / Left click + drag:</b> Döndür / Rotate</li>
<li><b>Sağ tık + sürükle / Right click + drag:</b> Yakınlaştır / Zoom</li>
<li><b>Orta tık + sürükle / Middle click + drag:</b> Kaydır / Pan</li>
</ul>

<hr>
<i>Hub Yüksekliği / Height: ~1.87m | Hub Yarıçapı / Radius: ~0.57m</i>
"""
        
        msg = QMessageBox(self)
        msg.setWindowTitle("3D Grafik Açıklaması / 3D Graph Legend")
        msg.setTextFormat(Qt.TextFormat.RichText)
        msg.setText(legend_text)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg.exec()

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
