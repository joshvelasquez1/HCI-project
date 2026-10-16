from pathlib import Path
import time
import cv2
import numpy as np
import mediapipe as mp
import pyautogui
from PIL import Image, ImageDraw, ImageFont
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

# Load the hand landmarker model.
model_path = Path(__file__).with_name("hand_landmarker.task")
if not model_path.is_file():
    raise FileNotFoundError(f"Missing model: {model_path}")

# one hand using
options = vision.HandLandmarkerOptions(
    base_options=python.BaseOptions(model_asset_path=str(model_path)),
    running_mode=vision.RunningMode.VIDEO,
    num_hands=1,
)

# draw hand sekeleton
connections = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
]

# volume
volume_commands = {
    "Volume up": "volumeup",
    "Volume down": "volumedown",
}

#tracks
track_commands = {
    "Next track": "nexttrack",
    "Previous track": "prevtrack",
}

#time to hold gesture before action
HOLD_SECONDS = 1.0
TOGGLE_SECONDS = 2.0
VOLUME_INTERVAL = 0.3

#colors
BG_PANEL = (44, 28, 26)       # #1A1C2C 
BG_CAM = (111, 54, 41)        # #29366F 
ACCENT_CYAN = (255, 210, 0)   # #00D2FF 
ACCENT_PINK = (108, 37, 244)  # #F4256C 
TEXT_WHITE = (244, 244, 244)  # #F4F4F4 

# information panel this is where we change the font
def panel_text(panel, text, y, color=(244, 244, 244), scale=0.5, thickness=1, x=20):
    pil_img = Image.fromarray(cv2.cvtColor(panel, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    
    try:
        font_size = int(scale * 40)
        font = ImageFont.truetype("VT323-Regular.ttf", font_size)
    except IOError:
        font = ImageFont.load_default()
        
    color_rgb = (color[2], color[1], color[0])
    
    draw.text((x, y - 6), text, font=font, fill=color_rgb)
    
    converted_back = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    np.copyto(panel, converted_back)

def landmark_distance(hand, a, b, width, height):
    return np.hypot(
        (hand[a].x - hand[b].x) * width,
        (hand[a].y - hand[b].y) * height,
    )

#open webcam
camera = cv2.VideoCapture(0)
window_name = "Gesture Music Controls - Press Q to exit"
last_timestamp = -1

# state variables
previous_gesture = None
gesture_since = 0.0
music_playing = True
controls_enabled = True
last_volume_change = 0.0
track_used = False
toggle_used = False
feedback_until = 0.0
feedback = ""
try:
    if not camera.isOpened():
        raise RuntimeError("Cannot open webcam.")

    #create and close when done
    with vision.HandLandmarker.create_from_options(options) as detector:
        while True:
            # read frame from webcam
            success, frame = camera.read()
            if not success:
                print("Cannot read webcam image.")
                break

            # flip and convert to RGB
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame,
            )

            # get timestamp in mseconds
            timestamp = max(
                time.monotonic_ns() // 1_000_000,
                last_timestamp + 1,
            )
            last_timestamp = timestamp
            result = detector.detect_for_video(image, timestamp)
            height, width = frame.shape[:2]
            status = "No hand detected"
            for hand in result.hand_landmarks:
                # determine which fingers open
                fingers = [
                    hand[tip].y < hand[joint].y
                    for tip, joint in [(8, 6), (12, 10), (16, 14), (20, 18)]
                ]

                # determine if thumb is open
                palm_width = max(
                    landmark_distance(hand, 5, 17, width, height),
                    1.0,
                )
                thumb_ratio = (
                    landmark_distance(hand, 4, 5, width, height)
                    / palm_width
                )
                thumb_open = thumb_ratio > 0.65

                if all(fingers) and not thumb_open:
                    status = "Toggle controls"
                elif all(fingers):
                    status = "Open hand"
                elif not any(fingers):
                    status = "Closed hand"
                elif fingers == [True, False, False, False]:
                    status = "Volume up"
                elif fingers == [True, True, False, False]:
                    status = "Volume down"
                elif fingers == [True, True, True, False]:
                    status = "Next track"
                elif fingers == [True, False, False, True]:
                    status = "Previous track"
                else:
                    status = "Other gesture"

                # convert normalized coordinates to pixel coordinates
                points = [
                    (int(point.x * width), int(point.y * height))
                    for point in hand
                ]

                # draw hand skeleton
                for start, end in connections:
                    cv2.line(
                        frame, points[start], points[end],
                        (0, 255, 0), 2,
                    )

                for point in points:
                    cv2.circle(frame, point, 4, (0, 0, 255), -1)

            now = time.monotonic()

            # restart hold time if gesture changes
            if status != previous_gesture:
                previous_gesture = status
                gesture_since = now
                last_volume_change = 0.0
            held_seconds = now - gesture_since

            # reset track and toggle usage if no hand detected for 0.5 seconds
            if status == "No hand detected" and held_seconds >= 0.5:
                track_used = False
                toggle_used = False

            # determine if gesture is valid and ready for action
            valid_gesture = (
                status in ("Open hand", "Closed hand", "Toggle controls")
                or status in volume_commands
                or status in track_commands
            )

            #longer hold time for toggle gesture
            required_hold = (
                TOGGLE_SECONDS
                if status == "Toggle controls"
                else HOLD_SECONDS
            )
            ready = valid_gesture and held_seconds >= required_hold

            # still work when controls pause
            if status == "Toggle controls":
                if ready and not toggle_used:
                    controls_enabled = not controls_enabled
                    toggle_used = True
                    feedback = (
                        "Controls enabled"
                        if controls_enabled
                        else "Controls paused"
                    )
                    feedback_until = time.monotonic() + 1.5
                    print(feedback)

            # only work when controls enabled
            elif controls_enabled and ready:
                action = None
                if status == "Closed hand" and music_playing:
                    pyautogui.press("playpause")
                    music_playing = False
                    action = "Pause command sent"
                elif status == "Open hand" and not music_playing:
                    pyautogui.press("playpause")
                    music_playing = True
                    action = "Play command sent"
                elif status in track_commands and not track_used:
                    pyautogui.press(track_commands[status])
                    track_used = True
                    action = f"{status} command sent"
                elif (
                    status in volume_commands
                    and now - last_volume_change >= VOLUME_INTERVAL
                ):
                    pyautogui.press(volume_commands[status])
                    last_volume_change = time.monotonic()

                # provide feedback for any action taken
                if action is not None:
                    feedback = action
                    feedback_until = time.monotonic() + 1.5
                    print(action)
            if status == "Toggle controls":
                if toggle_used:
                    instruction = "Remove hand before toggling again"
                else:
                    instruction = f"Hold: {held_seconds:.1f}/2.0 seconds"
            elif not controls_enabled:
                instruction = "4 fingers, thumb folded to resume"
            elif status in volume_commands and ready:
                instruction = "Adjusting volume"
            elif now < feedback_until:
                instruction = feedback
            elif status in track_commands and track_used:
                instruction = "Remove hand for another track command"
            elif valid_gesture and not ready:
                instruction = f"Hold: {held_seconds:.1f}/1.0 seconds"
            elif status == "No hand detected":
                instruction = "Show your hand to the camera"
            else:
                instruction = "Ready"

            # fit camera frame
            preview = np.full(
                (600, 640, 3), BG_CAM, dtype=np.uint8,
            )
            feed_box_width = 600
            ratio = feed_box_width / width
            resized_width = feed_box_width
            resized_height = int(height * ratio)

            x = 20
            y = 46

            # draw outer window border 
            cv2.rectangle(preview, (20, 16), (620, y + resized_height), (220, 220, 220), 6, cv2.LINE_AA)

            # draw top bar
            cv2.rectangle(preview, (20, 16), (620, 46), (220, 220, 220), -1)
            cv2.putText(
                preview, "CAM_FEED.EXE", (30, 37),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (30, 30, 30), 1, cv2.LINE_AA,
            )
            cv2.putText(
                preview, "X", (595, 37),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (30, 30, 30), 2, cv2.LINE_AA,
            )

            # camera feed
            resized = cv2.resize(
                frame, (resized_width, resized_height),
            )
            preview[y:y + resized_height, x:x + resized_width] = resized

            # Create information panel
            panel = np.full(
                (600, 440, 3), BG_PANEL, dtype=np.uint8,
            )

            panel_text(
                panel, "GESTURE MUSIC CONTROLS",
                35, ACCENT_PINK, 0.7, 2,
            )

            mode = "ACTIVE" if controls_enabled else "PAUSED"
            mode_color = (
                (0, 255, 180) if controls_enabled else (0, 180, 255)
            )
            panel_text(panel, f"Controls: {mode}", 70, ACCENT_CYAN, 0.7, 1)

            panel_text(panel, "Closed: Pause music", 100, TEXT_WHITE, 0.48)
            panel_text(panel, "Open: Play music", 125, TEXT_WHITE, 0.48)
            panel_text(panel, "Index: Volume up", 150, TEXT_WHITE, 0.48)
            panel_text(panel, "Index & Middle: Volume down", 175, TEXT_WHITE, 0.48)
            panel_text(panel, "Index & Middle & Ring: Next track", 200, TEXT_WHITE, 0.48)
            panel_text(panel, "Index & Pinky: Previous track", 225, TEXT_WHITE, 0.48)
            panel_text(panel, "Middle & Ring & Pinky: Pause/ resume", 250, TEXT_WHITE, 0.48)
            panel_text(panel, "controls", 270, TEXT_WHITE, 0.48)
            panel_text(panel, "(Hold for 2 seconds)", 295, TEXT_WHITE, 0.48)

            panel_text(panel, "Keep holding to adjust volume.", 335, TEXT_WHITE, 0.45)
            panel_text(panel, "Remove hand 0.5s before toggling another", 357, TEXT_WHITE, 0.45)
            panel_text(panel, "control.", 379, TEXT_WHITE, 0.45)

            panel_text(panel, "Detected: ", 415, ACCENT_CYAN, 0.52, 1)
            panel_text(panel, f"            {status}", 415, TEXT_WHITE, 0.52, 1)

            # show progress bar for hold time
            progress = (
                min(held_seconds / required_hold, 1.0)
                if valid_gesture
                and (controls_enabled or status == "Toggle controls")
                else 0.0
            )
            # loading bar
            bar_x, bar_y, bar_w, bar_h = 20, 445, 400, 22
            cv2.rectangle(panel, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (0, 0, 0), -1, cv2.LINE_AA)
            
            block_size = 12    
            block_spacing = 4  
            step = block_size + block_spacing
            available_w = bar_w - 16
            total_blocks = available_w // step
            total_blocks_width = (total_blocks * block_size) + ((total_blocks - 1) * block_spacing)
            start_x = bar_x + (bar_w - total_blocks_width) // 2
            
            lit_blocks = int(total_blocks * progress)
            
            for i in range(total_blocks):
                bx = start_x + (i * step)
                by = bar_y + (bar_h - block_size) // 2
                
                if i < lit_blocks:
                    cv2.rectangle(panel, (bx, by), (bx + block_size, by + block_size), ACCENT_CYAN, -1, cv2.LINE_AA)
                else:
                    cv2.rectangle(panel, (bx, by), (bx + block_size, by + block_size), (0, 0, 0), -1, cv2.LINE_AA)
                    
            panel_text(panel, instruction, 505, ACCENT_CYAN, 0.45)

            # Compact, Right-Aligned Retro EXIT button box
            exit_w, exit_h = 130, 42
            exit_x = 440 - exit_w - 20  # 290 px from left
            exit_y = 535
            
            # Button background and pink border
            cv2.rectangle(panel, (exit_x, exit_y), (exit_x + exit_w, exit_y + exit_h), (26, 28, 44), -1, cv2.LINE_AA)
            cv2.rectangle(panel, (exit_x, exit_y), (exit_x + exit_w, exit_y + exit_h), ACCENT_PINK, 2, cv2.LINE_AA)
            
            # Inner "Q" icon box on the left side of the button
            cv2.rectangle(panel, (exit_x + 10, exit_y + 8), (exit_x + 36, exit_y + 34), ACCENT_PINK, 1, cv2.LINE_AA)
            
            # Custom font text positioned correctly inside the button using the new x parameter
            panel_text(panel, "Q", exit_y + 12, ACCENT_PINK, 0.55, 1, x=exit_x + 16)
            panel_text(panel, "EXIT", exit_y + 13, TEXT_WHITE, 0.48, 1, x=exit_x + 44)

            # combine camera preview and information panel
            display = np.hstack((preview, panel))
            cv2.imshow(window_name, display)

            #exit
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            #exit if window closed
            if cv2.getWindowProperty(
                window_name, cv2.WND_PROP_VISIBLE
            ) < 1:
                break

finally:
    camera.release()
    cv2.destroyAllWindows()