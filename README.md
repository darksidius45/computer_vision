# HSMG_CV - Exercise Tracking Computer Vision System

## Overview

HSMG_CV is an advanced computer vision system designed to track and analyze exercise movements using colored markers. The system detects exercise machines, tracks weightlifting movements, counts repetitions and sets, and estimates weights used during workouts.

## Features

- **Automated Exercise Detection**: Detects and tracks exercise machine movements using color markers
- **Weight Tracking**: Identifies and estimates weights used during exercises
- **Rep and Set Counting**: Automatically counts repetitions and sets during workouts
- **Video Recording**: Records workout sessions for later analysis
- **Multi-threaded Processing**: Uses separate threads for video recording and analysis
- **Exercise Data Collection**: Collects comprehensive workout data including weight used, repetition count, and rest time
- **Configurable Settings**: Adaptable parameters for different camera setups and environments

## Requirements

- Python 3.8+
- OpenCV 4.11+
- NumPy
- PyWin32
- Other dependencies listed in requirements.txt

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/HSMG_CV.git
cd HSMG_CV
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
.venv\Scripts\activate
```

3. Install required packages:
```bash
pip install -r settings/requirements.txt
```

4. Prepare test videos (LFS tracked):
```bash
git lfs pull
```

## Project Structure

```
HSMG_CV/
│
├── video_processing/         # Core video processing modules
│   ├── __init__.py           
│   ├── camera.py             # Camera interfacing and frame processing
│   ├── config.py             # Configuration for different camera types
│   ├── machine.py            # Exercise machine movement tracking
│   ├── video_processing.py   # Main video analysis pipeline
│   └── weights.py            # Weight detection functionality
│
├── settings/                 # Configuration and setup tools
│   ├── requirements.txt      # Project dependencies
│   └── set_up.py             # Camera and marker setup utility
│
├── test_videos/              # Test video files (tracked with Git LFS)
│
├── main.py                   # Main application with backend integration
├── record_video.py           # Video recording functionality
├── test_main.py              # Test interface for system
└── README.md                 # This file
```

## Usage

### Basic Testing

Run the test interface to try the system:

```bash
python test_main.py
```

- Press 'r' to begin recording a video
- Press 'q' to quit the program

### Configuration

To configure camera and marker settings:

```bash
python settings/set_up.py
```

This utility helps you:
- Set color ranges for markers
- Define regions of interest (ROI)
- Calibrate tracking parameters

### Custom Integration

The system can be integrated into larger applications by importing and using its components:

```python
from video_processing.video_processing import init_system, stop_system
from record_video import record_video

# Initialize video processing system
init_system("rasberry")

# Record a workout video
record_video("rasberry", "workout_session.mp4")

# Clean up when done
stop_system()
```

## Camera Configuration

The system supports multiple camera configurations defined in config.py:
- rasberry
- vivo
- pixel_stable
- pixel_not_stable

Each configuration includes settings for:
- HSV color ranges for machine and weight markers
- Region of interest coordinates
- Movement detection thresholds
- Timer settings

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b new-feature`
3. Commit your changes: `git commit -am 'Add new feature'`
4. Push to the branch: `git push origin new-feature`
5. Submit a pull request

## License

[Specify your license here]

## Acknowledgements

- OpenCV team for the computer vision library
- [List any other acknowledgements]