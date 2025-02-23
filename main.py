import cv2
import numpy as np
from config import get_camera_settings
import win32api
from machine import machine_trajectory
from weights import weights_detection

# load all settings
camera_type = "rasberry"
camera_settings = get_camera_settings(camera_type)


lower_hsv_machine = camera_settings["lower_hsv_machine"]
upper_hsv_machine = camera_settings["upper_hsv_machine"]


lower_hsv_weight1 = camera_settings["lower_hsv_weight1"]
upper_hsv_weight1 = camera_settings["upper_hsv_weight1"]


lower_hsv_weight2 = camera_settings["lower_hsv_weight2"]
upper_hsv_weight2 = camera_settings["upper_hsv_weight2"]


roi_x_machine = camera_settings["roi_x_machine"]
roi_y_machine = camera_settings["roi_y_machine"]
roi_width_machine = camera_settings["roi_width_machine"]
roi_height_machine = camera_settings["roi_height_machine"]


roi_x_weight = camera_settings["roi_x_weight"]
roi_y_weight = camera_settings["roi_y_weight"]
roi_width_weight = camera_settings["roi_width_weight"]
roi_height_weight = camera_settings["roi_height_weight"]


start_time = camera_settings["start_time"]
video = camera_settings["video"]


# Загрузка
cap = cv2.VideoCapture(video)
cap.set(cv2.CAP_PROP_POS_MSEC, start_time)  # включаем видео с определённой секунды


if not cap.isOpened():
    print("Error: Could not open video.")
    exit()

tracker = cv2.TrackerCSRT_create() # создаем трекер
tracked = False
trajectories = []  # Словарь для хранения траекторий {id: points}
next_id = 0  # Счетчик для назначения ID объектам
max_distance = 120
ob_info = {}  # Максимальное расстояние для связывания точек


while True:
    ret, frame = cap.read()
    if not ret:
        break
    # Extract ROI from frame
    roi = frame[
        roi_y_machine : roi_y_machine + roi_height_machine,
        roi_x_machine : roi_x_machine + roi_width_machine,
    ]

    roi_weight = frame[
        roi_y_weight : roi_y_weight + roi_height_weight,
        roi_x_weight : roi_x_weight + roi_width_weight,
    ]
    # Конвертируем ROI в HSV

    hsv_frame_machine = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    hsv_frame_weight = cv2.cvtColor(roi_weight, cv2.COLOR_BGR2HSV)

    # маски для диапазона цветов в HSV
    mask_machine = cv2.inRange(hsv_frame_machine, lower_hsv_machine, upper_hsv_machine)

    # mask_allweights = cv2.inRange(hsv_frame_weight, lower_hsv_allweights, upper_hsv_allweights)# маска для определения области для поиска красеых меток

    # создаем 2 маски для красного цвета в разных диапазонах из-за особенностей hsv формата потом объединяем их в 1

    mask_weight = cv2.inRange(hsv_frame_weight, lower_hsv_weight1, upper_hsv_weight1)
    # mask_weight2 = cv2.inRange(hsv_frame_weight, lower_hsv_weight2, upper_hsv_weight2)
    # mask_weight = cv2.bitwise_or(mask_weight1, mask_weight2)

    # уменьшения шума
    kernel = np.ones((5, 5), np.uint8)
    mask_machine = cv2.erode(mask_machine, kernel, iterations=1)
    mask_machine = cv2.dilate(mask_machine, kernel, iterations=2)
    mask_weight = cv2.erode(mask_weight, kernel, iterations=1)
    mask_weight = cv2.dilate(mask_weight, kernel, iterations=2)

    current_centers = []

    # КОНТУРЫЫЫЫЫЫЫЫ
    contours_machine, _ = cv2.findContours(
        mask_machine, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    contours_weight, _ = cv2.findContours(
        mask_weight, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Отрисовываем ROI
    cv2.rectangle(
        frame,
        (roi_x_machine, roi_y_machine),
        (roi_x_machine + roi_width_machine, roi_y_machine + roi_height_machine),
        (255, 255, 255),
        2,
    )
    cv2.rectangle(
        frame,
        (roi_x_weight, roi_y_weight),
        (roi_x_weight + roi_width_weight, roi_y_weight + roi_height_weight),
        (255, 255, 255),
        2,
    )

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

    weight_markers_count = 0
    data = []

    # Store centers from previous frame if not already defined
    if not hasattr(cv2, "prev_weight_centers"):
        cv2.prev_weight_centers = []

    # Get current centers
    current_weight_centers = []
    updated_objects = {}

    for contour in contours_weight:
        # Игнор шума
        area = cv2.contourArea(contour)
        if area < 600:
            continue

        # Получаем прямоугольник, описывающий контур
        (x, y, w, h) = cv2.boundingRect(contour)

        # Проверяем соотношение сторон и площадь для фильтрации ложных срабатываний
        aspect_ratio = float(w) / h
        if aspect_ratio < 3.0:
            continue

        # Convert coordinates to original frame coordinates
        abs_x = x + roi_x_weight
        abs_y = y + roi_y_weight

        # Вычисляем центр объекта
        center = (abs_x + w // 2, abs_y + h // 2)

        # Дополнительная проверка на положение центра
        if (
            roi_x_weight <= center[0] <= roi_x_weight + roi_width_weight
            and roi_y_weight <= center[1] <= roi_y_weight + roi_height_weight
        ):
            current_weight_centers.append(center)

        cv2.rectangle(frame, (abs_x, abs_y), (abs_x + w, abs_y + h), (0, 255, 0), 2)
        cv2.circle(frame, center, 5, (0, 0, 255), -1)

    # Track objects across frames
    ob_info, next_id = weights_detection(
        frame, current_weight_centers, ob_info, updated_objects, next_id, max_distance
    )
    # Обновляем траектории
    tracked = machine_trajectory(frame, current_centers, trajectories, next_id, max_distance, tracker, tracked)

    # Показываем кадр и маску
    # Set window sizes
    # Get screen resolution using GetSystemMetrics

    screen_width = win32api.GetSystemMetrics(0)
    screen_height = win32api.GetSystemMetrics(1)

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
    mask_machine_resized = cv2.resize(mask_machine, (mask_machine.shape[1]//2, mask_machine.shape[0]//2))
    mask_weight_resized = cv2.resize(mask_weight, (mask_weight.shape[1]//2, mask_weight.shape[0]//2))

    # Show windows
    cv2.imshow("Frame", frame_resized)
    cv2.imshow("Mask_machine", mask_machine_resized)  # Show resized mask
    cv2.imshow("Mask_weight", mask_weight_resized)    # Show resized mask

    # Position windows
    cv2.moveWindow("Frame", 0, 0)
    cv2.moveWindow("Mask_machine", frame_width + 10, 0)  # Add 10px padding
    cv2.moveWindow("Mask_weight", frame_width + mask_machine_resized.shape[1] + 20, 0)  # Add 20px padding

    # Выход по нажатию клавиши q
    if cv2.waitKey(30) & 0xFF == ord("q"):
        break
        
cap.release()
cv2.destroyAllWindows()
