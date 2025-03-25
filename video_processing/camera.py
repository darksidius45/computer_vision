import cv2
import numpy as np
import time


def process_frame(
    frame,
    roi_x_machine,
    roi_y_machine,
    roi_width_machine,
    roi_height_machine,
    lower_hsv_machine,
    upper_hsv_machine,
    set_timer,
):


    if not hasattr(process_frame, "break_time"):
        process_frame.break_time = 0
        process_frame.prev_center = ()
    # Extract ROI from frame

    roi = frame[
        roi_y_machine : roi_y_machine + roi_height_machine,
        roi_x_machine : roi_x_machine + roi_width_machine,
    ]
    # Конвертируем ROI в HSV
    hsv_frame_machine = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    # маски для диапазона цветов в HSV
    mask_machine = cv2.inRange(hsv_frame_machine, lower_hsv_machine, upper_hsv_machine)

    # уменьшения шума
    kernel = np.ones((5, 5), np.uint8)
    mask_machine = cv2.erode(mask_machine, kernel, iterations=1)
    mask_machine = cv2.dilate(mask_machine, kernel, iterations=2)

    current_centers = []

    # КОНТУРЫЫЫЫЫЫЫЫ
    contours_machine, _ = cv2.findContours(
        mask_machine, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Отрисовываем ROI
    cv2.rectangle(
        frame,
        (roi_x_machine, roi_y_machine),
        (roi_x_machine + roi_width_machine, roi_y_machine + roi_height_machine),
        (255, 255, 255),
        2,
    )
    center = ()
    print("test3")
    # Рисуем контуры и центры объектов
    for contour in contours_machine:
        # Игнор шума
        area = cv2.contourArea(contour)
        if area < 75:
            continue

        # прямоугольник, описывающий контур
        (x, y, w, h) = cv2.boundingRect(contour)

        aspect_ratio = float(w) / h
        if aspect_ratio < 0.2 or aspect_ratio > 5:
            continue

        # Convert coordinates
        abs_x = x + roi_x_machine
        abs_y = y + roi_y_machine

        # Вычисляем центр объекта
        center = (abs_x + w // 2, abs_y + h // 2)
        current_centers.append(center)

        # Рисуем прямоугольник вокруг объекта
        cv2.circle(frame, center, 5, (0, 255, 0), -1)

        # Выводим координаты центра
        cv2.putText(
            frame,
            f"({center[0]}, {center[1]})",
            (abs_x, abs_y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            2,
        )

    MOVEMENT_THRESHOLD = 5

    if center and process_frame.prev_center:
        vertical_movement = abs(center[1] - process_frame.prev_center[1])
        if vertical_movement < MOVEMENT_THRESHOLD:
            if process_frame.break_time == 0:
                process_frame.break_time = time.time()
            timer = time.time() - process_frame.break_time
            if timer > set_timer:
                return True
            cv2.putText(
                frame,
                f"Break timer: {timer:.2f}s",
                (frame.shape[1] - 300, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (255, 255, 255),
                2,
            )
    else:
        process_frame.break_time = 0

    process_frame.prev_center = center

    screen_width = 1920
    screen_height = 1080

    # Calculate frame size to fit screen while maintaining aspect ratio
    frame_height = int(screen_height * 0.8)  # Use 80% of screen height
    frame_width = int(frame.shape[1] * frame_height / frame.shape[0])

    # Ensure frame width doesn't exceed screen width
    if frame_width > screen_width * 0.8:
        frame_width = int(screen_width * 0.8)
        frame_height = int(frame.shape[0] * frame_width / frame.shape[1])

    # Resize frame only
    frame_resized = cv2.resize(frame, (frame_width, frame_height))

    # Resize masks to half size
    mask_machine_resized = cv2.resize(
        mask_machine, (mask_machine.shape[1] // 2, mask_machine.shape[0] // 2)
    )

    # Show windows
    # cv2.imshow("Frame", frame_resized)


    return False
