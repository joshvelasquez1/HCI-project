# swipe detection for skipping songs
# keeps the last half second of wrist positions and checks how far the hand moved

SWIPE_WINDOW = 0.5      # seconds of wrist positions to look at
SWIPE_DISTANCE = 0.25   # how far the wrist has to move, as a fraction of the frame width
SWIPE_COOLDOWN = 1.0    # seconds to wait after a swipe so one swipe can't skip twice


def update_history(history, now, x, y):
    # add the newest wrist position and drop anything older than the window
    history.append((now, x, y))
    while now - history[0][0] > SWIPE_WINDOW:
        history.pop(0)


def check_swipe(history):
    # need a few frames before it can count as a swipe
    if len(history) < 3:
        return None

    start_time, start_x, start_y = history[0]
    end_time, end_x, end_y = history[-1]
    moved_x = end_x - start_x
    moved_y = end_y - start_y

    # mostly sideways only, so moving your hand up or down doesn't count
    if abs(moved_y) > abs(moved_x) / 2:
        return None

    if moved_x > SWIPE_DISTANCE:
        return "Next track"
    if moved_x < -SWIPE_DISTANCE:
        return "Previous track"
    return None
