def classify_gesture(hand):
    # determine which fingers open
    fingers = [
        hand[tip].y < hand[joint].y
        for tip, joint in [(8, 6), (12, 10), (16, 14), (20, 18)]
    ]

    if fingers == [False, False, False, True]:
        return "Toggle controls"
    elif all(fingers):
        return "Open hand"
    elif not any(fingers):
        return "Closed hand"
    elif fingers == [True, False, False, False]:
        return "Volume up"
    elif fingers == [True, True, False, False]:
        return "Volume down"
    elif fingers == [True, True, True, False]:
        return "Next track"
    elif fingers == [True, False, False, True]:
        return "Previous track"
    else:
        return "Other gesture"