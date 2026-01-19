# 🎯 FRC Shooter Calculator

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green?logo=qt&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&logoColor=white)
![FRC](https://img.shields.io/badge/FRC-2026%20Rebuilt-red)
![License](https://img.shields.io/badge/License-MIT-yellow)

**An advanced shooter trajectory simulation tool for FRC robotics teams**

[📖 ChiefDelphi Thread](https://www.chiefdelphi.com/t/team-nf-9029-rebuilt-2026-shooter-calculations-tests/511928) • [🤖 Team NF 9029](https://github.com/efeerdogmus0)

</div>

---

## 👥 Credits & Background

This project was developed by **Team NF 9029** for the **FRC 2026 Rebuilt** season.

### Physics Foundation
All physics calculations and theoretical foundations were developed by **Tuna Ercan** ([@StayPuft on ChiefDelphi](https://www.chiefdelphi.com/u/StayPuft)).

> *"Hello everyone! We plan to share our shooter tests, calculations, and the tools we've created for ourselves throughout this year's competition timeline under this topic. Currently, we have created two separate "calculators," one a Desmos project and the other a Python program. In the Desmos project, the effects of weather are not included, whereas in the Python program, we attempted to calculate these effects (Magnus & drag) using numerical iteration. We believe we obtained results close to what we calculated in our tests, and we have plans for next week to create a better testing environment and methodology."*
> 
> — Tuna Ercan, ChiefDelphi

### GUI & Advanced Features
The PyQt6 GUI, optimal angle calculator, impact zone visualization, and additional features were built on top of Tuna's physics engine.

---

## ✨ Features

### Core Simulation
- **2D & 3D Trajectory Visualization** - Interactive plots showing projectile paths
- **Realistic Physics** - Air drag (C_D), Magnus effect (C_L), and ball spin calculations
- **Ideal vs Real Comparison** - See the difference between theoretical and actual trajectories

### 🎯 Optimal Angle Calculator
Automatically calculate the best launch angle for any target distance:
- Input your target distance (0.5m - 10m)
- Get the optimal angle, flight time, and landing error
- One-click apply to see the trajectory

### 🎪 Impact Zone Visualization
See where your shots will actually land:
- Monte Carlo-style spread analysis
- Adjustable angle variance (±0.5° to ±5°)
- Adjustable RPM variance (±1% to ±10%)
- Visual probability display in 3D

### 📊 Real-Time Statistics
- Distance to target
- Flight time
- Accuracy percentage
- Spread radius
- On-target status indicator


---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/)

#### Linux
```bash
bash run.sh
```

#### Windows (WSL2)
1. Install [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install)
2. Open your WSL terminal (Ubuntu)
3. Clone this repo and run:
```bash
bash run.sh
```

#### macOS
1. Install [XQuartz](https://www.xquartz.org/)
2. Enable "Allow connections from network clients" in XQuartz preferences
3. Run:
```bash
xhost +localhost
bash run.sh
```

### Option 2: Native Python

**Prerequisites:** Python 3.10+

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

---

## 📐 Physics Model

### Equations Used

**Ball Exit Velocity:**
```
V_ball = V_surface × C_roll
V_surface = (RPM / 60) × 2π × R_wheel
```

**Drag Force:**
```
F_drag = 0.5 × C_D × ρ × A × v²
```

**Magnus Force (Lift):**
```
F_magnus = 0.5 × ρ × A × R_ball × ω_ball × v × C_L
```

### Constants (FRC 2022 Rapid React)
| Parameter | Value | Description |
|-----------|-------|-------------|
| `R_wheel` | 5.08 cm | Flywheel radius |
| `R_ball` | 7.5 cm | Cargo ball radius |
| `m_ball` | 0.225 kg | Ball mass |
| `ρ` | 1.2 kg/m³ | Air density |
| `g` | 9.81 m/s² | Gravity |

---

## 🎮 Usage Guide

### Parameters

| Parameter | Range | Description |
|-----------|-------|-------------|
| **Angle** | 10° - 80° | Launch angle from horizontal |
| **RPM** | 1000 - 5000 | Flywheel rotation speed |
| **C_roll** | 0 - 1 | Rolling coefficient (energy transfer) |
| **C_D** | 0 - 1 | Drag coefficient |
| **C_L** | 0 - 1 | Lift coefficient (Magnus effect) |
| **P_x, P_y** | Field dims | Robot position on field |
| **O_r** | -90° - 90° | Robot orientation angle |

### Workflow

1. **Set your robot position** using P_x, P_y, and O_r sliders
2. **Adjust shooter parameters** (angle, RPM, coefficients)
3. **Use Optimal Angle Calculator** for automatic tuning
4. **Check Impact Zone** to see shot consistency
5. **Monitor Statistics** for real-time feedback
6. **Save configuration** for match day

---

## 📁 Project Structure

```
frcshooter/
├── main.py          # Entry point
├── gui.py           # PyQt6 interface (controls, plots, dialogs)
├── simulation.py    # Physics engine (trajectories, optimization)
├── config.py        # JSON save/load logic
├── config.json      # Default configuration
├── Dockerfile       # Container setup
├── docker-compose.yml
├── run.sh           # Linux/macOS launcher
└── requirements.txt # Python dependencies
```

---

## 🤝 Contributing

We welcome contributions from other FRC teams! Feel free to:
- Open issues for bugs or feature requests
- Submit pull requests
- Share your testing data and feedback

---

## 📜 License

MIT License - Feel free to use this for your FRC team!

---

## 🔗 Links

- **ChiefDelphi Thread:** [Team NF 9029 - 2026 Shooter Calculations & Tests](https://www.chiefdelphi.com/t/team-nf-9029-rebuilt-2026-shooter-calculations-tests/511928)
- **Team:** NF 9029
- **Season:** FRC 2026 Rebuilt

---

<div align="center">

**Made with 💜 by Team NF 9029**

*Good luck to all teams in the 2026 Rebuilt season!*

</div>
