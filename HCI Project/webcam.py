import cv2

camera = cv2.VideoCapture(0)
window_name = "Gesture Music Controls - Webcam"

try:
    if not camera.isOpened():
        raise RuntimeError("Cannot open webcam.")

    while True:
        success, frame = camera.read()

        if not success:
            print("Cannot read webcam image.")
            break

        frame = cv2.flip(frame, 1)
        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
            break
finally:
    camera.release()
    cv2.destroyAllWindows()