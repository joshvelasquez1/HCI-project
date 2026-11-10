from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# draw hand sekeleton
connections = [
    (0, 1), (1, 2), (2, 3), (3, 4),
    (0, 5), (5, 6), (6, 7), (7, 8),
    (5, 9), (9, 10), (10, 11), (11, 12),
    (9, 13), (13, 14), (14, 15), (15, 16),
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
]

#colors
BG_PANEL = (44, 28, 26)       # #1A1C2C
BG_CAM = (111, 54, 41)        # #29366F
ACCENT_CYAN = (255, 210, 0)   # #00D2FF
ACCENT_PINK = (108, 37, 244)  # #F4256C
TEXT_WHITE = (244, 244, 244)  # #F4F4F4

# font file sits next to this script like the model does
font_path = Path(__file__).with_name("VT323-Regular.ttf")
fonts = {}

# information panel this is where we change the font
def panel_text(panel, text, y, color=(244, 244, 244), scale=0.5, thickness=1, x=20):
    font_size = int(scale * 40)

    # load each font size once instead of reloading it from disk every frame
    if font_size not in fonts:
        try:
            fonts[font_size] = ImageFont.truetype(str(font_path), font_size)
        except IOError:
            fonts[font_size] = ImageFont.load_default()
    font = fonts[font_size]

    # only convert the strip of the panel the text sits on instead of the whole panel
    top = max(y - 6, 0)
    strip = panel[top:top + font_size * 2]
    pil_img = Image.fromarray(cv2.cvtColor(strip, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)

    color_rgb = (color[2], color[1], color[0])

    draw.text((x, y - 6 - top), text, font=font, fill=color_rgb)

    converted_back = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    np.copyto(strip, converted_back)

def draw_hand(frame, hand, width, height):
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


def draw_static_panel(testing=False):
    # the parts of the panel that never change get drawn once here instead of every frame,
    # the pixel font is slow to draw so redrawing all of it every frame was killing the frame rate
    panel = np.full(
        (600, 440, 3), BG_PANEL, dtype=np.uint8,
    )

    panel_text(
        panel, "GESTURE MUSIC CONTROLS",
        35, ACCENT_PINK, 0.7, 2,
    )

    panel_text(panel, "Closed: Pause music", 100, TEXT_WHITE, 0.48)
    panel_text(panel, "Open: Play music", 125, TEXT_WHITE, 0.48)
    panel_text(panel, "Index: Volume up", 150, TEXT_WHITE, 0.48)
    panel_text(panel, "Index & Middle: Volume down", 175, TEXT_WHITE, 0.48)
    panel_text(panel, "Swipe right / 3 fingers: Next track", 200, TEXT_WHITE, 0.48)
    panel_text(panel, "Swipe left / Index & Pinky: Prev track", 225, TEXT_WHITE, 0.48)
    panel_text(panel, "Pinky: Pause/ resume", 250, TEXT_WHITE, 0.48)
    panel_text(panel, "controls", 270, TEXT_WHITE, 0.48)
    panel_text(panel, "(Hold for 2 seconds)", 295, TEXT_WHITE, 0.48)

    panel_text(panel, "Keep holding to adjust volume.", 335, TEXT_WHITE, 0.45)
    panel_text(panel, "Remove hand 0.5s before toggling another", 357, TEXT_WHITE, 0.45)
    panel_text(panel, "control.", 379, TEXT_WHITE, 0.45)

    panel_text(panel, "Detected: ", 415, ACCENT_CYAN, 0.52, 1)

    # exit box
    exit_w, exit_h = 130, 42
    exit_x = 440 - exit_w - 20  # 290 px from left
    exit_y = 535

    # button background and pink border
    cv2.rectangle(panel, (exit_x, exit_y), (exit_x + exit_w, exit_y + exit_h), (26, 28, 44), -1, cv2.LINE_AA)
    cv2.rectangle(panel, (exit_x, exit_y), (exit_x + exit_w, exit_y + exit_h), ACCENT_PINK, 2, cv2.LINE_AA)

    # inner "Q" icon box on the left side of the button
    cv2.rectangle(panel, (exit_x + 10, exit_y + 8), (exit_x + 36, exit_y + 34), ACCENT_PINK, 1, cv2.LINE_AA)

    panel_text(panel, "Q", exit_y + 12, ACCENT_PINK, 0.55, 1, x=exit_x + 16)
    panel_text(panel, "EXIT", exit_y + 13, TEXT_WHITE, 0.48, 1, x=exit_x + 44)

    # reminder for whoever is running a user test
    if testing:
        panel_text(panel, "TEST  M: missed  F: false", 548, ACCENT_PINK, 0.45)

    return panel


def render_display(frame, status, controls_enabled, instruction,
                   held_seconds, required_hold, valid_gesture, static_panel):
    height, width = frame.shape[:2]
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

    # copy the parts of the panel that never change
    panel = static_panel.copy()

    mode = "ACTIVE" if controls_enabled else "PAUSED"
    mode_color = (
        (0, 255, 180) if controls_enabled else (0, 180, 255)
    )
    panel_text(panel, f"Controls: {mode}", 70, ACCENT_CYAN, 0.7, 1)
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

    # combine camera preview and information panel
    return np.hstack((preview, panel))