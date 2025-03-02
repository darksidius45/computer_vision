import cv2
import numpy as np


coords = []
color = None
scale = 1.0
zoom_pt = None

video_path = r"test_videos\vivo_not_stable.mp4"


def zoom(img, center, scale):
    height, width = img.shape[:2]
    center_x, center_y = center
    src_pts = np.float32(
        [
            [center_x - width / 2, center_y - height / 2],
            [center_x + width / 2, center_y - height / 2],
            [center_x - width / 2, center_y + height / 2],
        ]
    )
    dst_pts = np.float32(
        [
            [(center_x - width / 2) * scale, (center_y - height / 2) * scale],
            [(center_x + width / 2) * scale, (center_y - height / 2) * scale],
            [(center_x - width / 2) * scale, (center_y + height / 2) * scale],
        ]
    )
    M = cv2.getAffineTransform(src_pts, dst_pts)
    return cv2.warpAffine(img, M, (width, height))


def get_color_from_video(video_path):
    cap = cv2.VideoCapture(video_path)
    paused = False
    roi_points = []
    drawing = False
    lower_hsv = np.array([0, 0, 0])
    upper_hsv = np.array([179, 255, 255])

    if not cap.isOpened():
        print("Ошибка: видео не загружено.")
        return

    def mouse_callback(event, x, y, flags, param):
        nonlocal drawing, roi_points, lower_hsv, upper_hsv
        frame = param

        if event == cv2.EVENT_LBUTTONDOWN and paused:
            color = frame[y, x]
            print(f"Координаты: ({x}, {y}), Цвет в формате BGR: {color}")

            rgb_color = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2RGB)[0][0]
            hsv_color = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2HSV)[0][0]
            print(f"Цвет в формате RGB: {rgb_color}")
            print(f"Цвет в формате HSV: {hsv_color}")

            color_image = np.zeros((100, 100, 3), dtype=np.uint8)
            color_image[:, :] = color
            cv2.namedWindow("Selected Color", cv2.WINDOW_NORMAL)
            cv2.imshow("Selected Color", color_image)
            cv2.resizeWindow("Selected Color", 200, 200)

        elif event == cv2.EVENT_RBUTTONDOWN:
            roi_points.clear()  # Clear previous points
            roi_points.append((x, y))  # Add first point
            drawing = True

        elif event == cv2.EVENT_RBUTTONUP:
            drawing = False
            if len(roi_points) > 0:
                roi_points.append((x, y))  # Add final point

                # Calculate rectangle dimensions
                roi_x = roi_points[0][0]
                roi_y = roi_points[0][1]
                roi_width = x - roi_x
                roi_height = y - roi_y

                print("ROI Coordinates:")
                print(f"Top-left: ({roi_x}, {roi_y})")
                print(f"Width: {roi_width}, Height: {roi_height}")

        elif event == cv2.EVENT_MOUSEMOVE and drawing:
            temp_frame = frame.copy()
            if len(roi_points) > 0:
                # Draw line from last point to current mouse position
                cv2.rectangle(temp_frame, roi_points[0], (x, y), (0, 255, 0), 2)
                cv2.imshow("Video", temp_frame)

    def on_trackbar(val):
        nonlocal lower_hsv, upper_hsv
        lower_hsv[0] = cv2.getTrackbarPos("Lower H", "Mask")
        lower_hsv[1] = cv2.getTrackbarPos("Lower S", "Mask")
        lower_hsv[2] = cv2.getTrackbarPos("Lower V", "Mask")
        upper_hsv[0] = cv2.getTrackbarPos("Upper H", "Mask")
        upper_hsv[1] = cv2.getTrackbarPos("Upper S", "Mask")
        upper_hsv[2] = cv2.getTrackbarPos("Upper V", "Mask")

    cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
    cv2.namedWindow("Mask", cv2.WINDOW_NORMAL)

    # Get screen resolution
    screen_width = 1920  # Default HD width
    screen_height = 1080  # Default HD height

    # Set window sizes to fit screen
    cv2.resizeWindow("Video", screen_width // 2, screen_height // 2)
    cv2.resizeWindow("Mask", screen_width // 3, screen_height // 3)

    # Position windows
    cv2.moveWindow("Video", 0, 0)
    cv2.moveWindow("Mask", screen_width // 2, 0)

    cv2.createTrackbar("Lower H", "Mask", 0, 179, on_trackbar)
    cv2.createTrackbar("Lower S", "Mask", 0, 255, on_trackbar)
    cv2.createTrackbar("Lower V", "Mask", 0, 255, on_trackbar)
    cv2.createTrackbar("Upper H", "Mask", 179, 179, on_trackbar)
    cv2.createTrackbar("Upper S", "Mask", 255, 255, on_trackbar)
    cv2.createTrackbar("Upper V", "Mask", 255, 255, on_trackbar)

    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break

        temp_frame = frame.copy()
        if len(roi_points) > 1:
            for i in range(len(roi_points) - 1):
                cv2.line(temp_frame, roi_points[i], roi_points[i + 1], (0, 255, 0), 2)

        cv2.setMouseCallback("Video", mouse_callback, frame)
        cv2.imshow("Video", temp_frame)

        if paused:
            hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv_frame, lower_hsv, upper_hsv)
            cv2.imshow("Mask", mask)

        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):
            break
        elif key == ord(" "):
            paused = not paused

    cap.release()
    cv2.destroyAllWindows()
    return roi_points[:-1] if roi_points else None


# Get color and ROI from video

roi_points = get_color_from_video(video_path)
