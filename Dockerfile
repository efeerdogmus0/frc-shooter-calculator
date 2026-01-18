FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies for GUI (Tkinter) and X11 forwarding
RUN apt-get update && apt-get install -y \
    python3-tk \
    x11-apps \
    libgl1 \
    libegl1 \
    libxkbcommon-x11-0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    libxcb-xfixes0 \
    libdbus-1-3 \
    libglib2.0-0 \
    libxcb-cursor0 \
    libxcb-shape0 \
    libxcb-shm0 \
    libxcb-util1 \
    libx11-xcb1 \
    libfontconfig1 \
    libfreetype6 \
    libxext6 \
    libxi6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
