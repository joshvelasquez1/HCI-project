from pathlib import Path
import time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from controls import MusicControls
from display import draw_hand, draw_static_panel, render_display
from gestures import classify_gesture
from session_log import start_log, log_event, stop_log
from swipe import update_history, check_swipe


def run_app(testing=False):
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

    #open webcam
    camera = cv2.VideoCapture(0)
    window_name = "Gesture Music Controls - Press Q to exit"
    last_timestamp = -1
    controls = MusicControls()
    static_panel = draw_static_panel(testing)
    wrist_history = []

    if testing:
        start_log()

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
                swipe = None
                for hand in result.hand_landmarks:
                    status = classify_gesture(hand)
                    draw_hand(frame, hand, width, height)

                    # swipes only count with an open hand, hand[0] is the wrist
                    if status == "Open hand":
                        update_history(wrist_history, time.monotonic(), hand[0].x, hand[0].y)
                        swipe = check_swipe(wrist_history)
                        if swipe:
                            wrist_history.clear()

                instruction, held_seconds, required_hold, valid_gesture = controls.update(status, swipe)
                display = render_display(
                    frame, status, controls.controls_enabled, instruction,
                    held_seconds, required_hold, valid_gesture, static_panel,
                )
                cv2.imshow(window_name, display)

                #exit, in test mode M marks a missed gesture and F marks a false trigger
                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("m"):
                    log_event("marked missed")
                if key == ord("f"):
                    log_event("marked false trigger")
                #exit if window closed
                if cv2.getWindowProperty(
                    window_name, cv2.WND_PROP_VISIBLE
                ) < 1:
                    break

    finally:
        stop_log()
        camera.release()
        cv2.destroyAllWindows()