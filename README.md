# FRC Shooter Calculator

A Dockerized Python application for simulating FRC shooter mechanics, featuring a PyQt6 GUI with 2D/3D visualizations and adjustable parameters.

## Features
- **2D & 3D Visualization**: Interactive plots showing projectile trajectories.
- **Physics Simulation**: Drag, lift (Magnus effect), and friction calculations.
- **PyQt6 GUI**: Modern interface with sliders, spinboxes, and configuration management.
- **Config Management**: Save and load simulation parameters to/from JSON files.

## Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) or Docker Engine.

## How to Run

### Linux
1. Open a terminal.
2. Run the start script:
   ```bash
   bash run.sh
   ```
   This script automatically handles X11 permissions (`xhost`) and builds the container.

### Windows (WSL2)
**Requirement**: Windows 10 Build 19044+ or Windows 11.
1. Install [WSL2](https://learn.microsoft.com/en-us/windows/wsl/install).
2. Ensure you have a Linux distribution installed (e.g., Ubuntu).
3. **Windows 11**: GUI apps work out of the box (WSLg).
4. **Windows 10**: You may need to install an X Server like [VcXsrv](https://sourceforge.net/projects/vcxsrv/).
5. Open your WSL terminal (Ubuntu).
6. Clone this repo and navigate to the folder.
7. Run:
   ```bash
   bash run.sh
   ```

### macOS
1. Install [XQuartz](https://www.xquartz.org/).
2. Open XQuartz preferences -> Security -> Enable "Allow connections from network clients".
3. Restart XQuartz.
4. Run in terminal:
   ```bash
   xhost +localhost
   bash run.sh
   ```

### Native (No Docker)
You can run the application directly on any computer (Windows, Mac, Linux) if you have Python installed.

**Prerequisites**:
- Python 3.10 or newer.

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Run**:
   ```bash
   python main.py
   ```

## Troubleshooting
- **"Authorization required..."**: Ensure you ran `bash run.sh` or executed `xhost +local:docker` manually.
- **XCB errors**: The Dockerfile includes all necessary `libxcb` dependencies. Try rebuilding with `docker compose build --no-cache`.

## Project Structure
- `main.py`: Entry point.
- `gui.py`: PyQt6 Interface.
- `simulation.py`: Physics logic.
- `config.py`: JSON save/load logic.
