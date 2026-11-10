import time

import pyautogui

from session_log import log_event
from swipe import SWIPE_COOLDOWN

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


class MusicControls:
    def __init__(self):
        self.previous_gesture = None
        self.gesture_since = 0.0
        self.music_playing = True
        self.controls_enabled = True
        self.last_volume_change = 0.0
        self.track_used = False
        self.toggle_used = False
        self.feedback_until = 0.0
        self.feedback = ""
        self.last_swipe = 0.0

    def update(self, status, swipe=None):
        now = time.monotonic()

        # swipes skip right away with no hold, the cooldown stops one swipe from skipping twice
        if swipe and self.controls_enabled and now - self.last_swipe >= SWIPE_COOLDOWN:
            pyautogui.press(track_commands[swipe])
            self.last_swipe = now
            # restart the hold timer so the open hand doesn't also count as play
            self.gesture_since = now
            self.feedback = f"Swipe: {swipe}"
            self.feedback_until = now + 1.5
            print(self.feedback)
            log_event("swipe", swipe)

        # restart hold time if gesture changes
        if status != self.previous_gesture:
            self.previous_gesture = status
            self.gesture_since = now
            self.last_volume_change = 0.0
        held_seconds = now - self.gesture_since

        # reset track and toggle usage if no hand detected for 0.5 seconds
        if status == "No hand detected" and held_seconds >= 0.5:
            self.track_used = False
            self.toggle_used = False

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
            if ready and not self.toggle_used:
                self.controls_enabled = not self.controls_enabled
                self.toggle_used = True
                self.feedback = (
                    "Controls enabled"
                    if self.controls_enabled
                    else "Controls paused"
                )
                self.feedback_until = time.monotonic() + 1.5
                print(self.feedback)
                log_event("controls", self.feedback)

        # only work when controls enabled
        elif self.controls_enabled and ready:
            action = None
            if status == "Closed hand" and self.music_playing:
                pyautogui.press("playpause")
                self.music_playing = False
                action = "Pause command sent"
            elif status == "Open hand" and not self.music_playing:
                pyautogui.press("playpause")
                self.music_playing = True
                action = "Play command sent"
            elif status in track_commands and not self.track_used:
                pyautogui.press(track_commands[status])
                self.track_used = True
                action = f"{status} command sent"
            elif (
                status in volume_commands
                and now - self.last_volume_change >= VOLUME_INTERVAL
            ):
                pyautogui.press(volume_commands[status])
                self.last_volume_change = time.monotonic()
                log_event("volume", status)

            # provide self.feedback for any action taken
            if action is not None:
                self.feedback = action
                self.feedback_until = time.monotonic() + 1.5
                print(action)
                log_event("held gesture", action)
        if status == "Toggle controls":
            if self.toggle_used:
                instruction = "Remove hand before toggling again"
            else:
                instruction = f"Hold: {held_seconds:.1f}/2.0 seconds"
        elif not self.controls_enabled:
            instruction = "Just pinky finger to resume"
        elif status in volume_commands and ready:
            instruction = "Adjusting volume"
        elif now < self.feedback_until:
            instruction = self.feedback
        elif status in track_commands and self.track_used:
            instruction = "Remove hand for another track command"
        elif valid_gesture and not ready:
            instruction = f"Hold: {held_seconds:.1f}/1.0 seconds"
        elif status == "No hand detected":
            instruction = "Show your hand to the camera"
        else:
            instruction = "Ready"
        return instruction, held_seconds, required_hold, valid_gesture