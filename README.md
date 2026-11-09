# HCI-project

# How to Run
Install the libraries once:
```
pip install -r requirements.txt
```
Then run it from this folder and press Q in the window to quit:
```
python main.py
```

# Gestures
| Gesture | What it does |
|---|---|
| Swipe an open hand right | Next track |
| Swipe an open hand left | Previous track |
| Index, middle and ring finger up (hold 1 second) | Next track |
| Index and pinky up (hold 1 second) | Previous track |
| Fist (hold 1 second) | Pause |
| Open hand (hold 1 second) | Play |
| Index finger up (keep holding) | Volume up |
| Index and middle finger up (keep holding) | Volume down |
| Pinky up only (hold 2 seconds) | Pause or resume gesture controls |

# Test Mode
For user testing, start it with:
```
python main.py test
```
Every command the app sends gets saved to a CSV in the logs folder. While someone is testing, press M when the app misses a gesture they tried and F when it does something they didn't mean. When you quit, it prints a count of each.

# Code Sources

I developed this program using Python documentation, OpenCV documentation, and the MediaPipe source code from Google AI Edge on GitHub.
References:
- Python documentation:
  https://pypi.org/
  https://docs.python.org/3/
- OpenCV documentation: https://docs.opencv.org/4.x/
- MediaPipe landmark source code:
  https://github.com/google-ai-edge/mediapipe/blob/master/mediapipe/tasks/python/components/containers/landmark.py

I also used AI assistance to help refine and organize the code.
The program uses OpenCV for webcam input and display, MediaPipe Hand Landmarker for hand tracking, and PyAutoGUI to send music control commands.
