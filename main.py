import cv2
import numpy as np
from config import get_camera_settings


# load all settings
camera_type = "pixel"
camera_settings = get_camera_settings(camera_type)


lower_hsv_green = camera_settings["lower_hsv_green"]
upper_hsv_green = camera_settings["upper_hsv_green"]

lower_hsv_red1 = camera_settings["lower_hsv_red1"]
upper_hsv_red1 = camera_settings["upper_hsv_red1"]

lower_hsv_red2 = camera_settings["lower_hsv_red2"]
upper_hsv_red2 = camera_settings["upper_hsv_red2"]

roi_x_green = camera_settings["roi_x_green"]
roi_y_green = camera_settings["roi_y_green"]
roi_width_green = camera_settings["roi_width_green"]

roi_height_green = camera_settings["roi_height_green"]


roi_x_red = camera_settings["roi_x_red"]
roi_y_red = camera_settings["roi_y_red"]
roi_width_red = camera_settings["roi_width_red"]
roi_height_red = camera_settings["roi_height_red"]

video = camera_settings["video"]




# Загрузка видеофайла
cap = cv2.VideoCapture(video)
cap.set(cv2.CAP_PROP_POS_MSEC, 3000)  # включи видео с 3 секунды


if not cap.isOpened():
    print("Ошибка: видео не загружено.")
    exit()


trajectories = {}  # Словарь для хранения траекторий {id: points}
next_id = 0  # Счетчик для назначения ID объектам
max_distance = 120  # Максимальное расстояние для связывания точек


while True:
    ret, frame = cap.read()
    if not ret:
        break  # Выход, если видео закончилось

    # Extract ROI from frame
    roi = frame[roi_y_green : roi_y_green + roi_height_green, roi_x_green : roi_x_green + roi_width_green]
    roi_red = frame[
        roi_y_red : roi_y_red + roi_height_red, roi_x_red : roi_x_red + roi_width_red
    ]
    # Конвертируем ROI в HSV
    hsv_frame_green = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    hsv_frame_red = cv2.cvtColor(roi_red, cv2.COLOR_BGR2HSV)

    # маски для диапазона цветов в HSV
    mask_green = cv2.inRange(hsv_frame_green, lower_hsv_green, upper_hsv_green)

    # создаем 2 маски для красного цвета в разных диапазонах из-за особенностей hsv формата потом объединяем их в 1
    mask_red1 = cv2.inRange(hsv_frame_red, lower_hsv_red1, upper_hsv_red1)
    mask_red2 = cv2.inRange(hsv_frame_red, lower_hsv_red2, upper_hsv_red2)
    mask_red = cv2.bitwise_or(mask_red1, mask_red2)


    # уменьшения шума
    kernel = np.ones((5, 5), np.uint8)
    mask_green = cv2.erode(mask_green, kernel, iterations=1)
    mask_green = cv2.dilate(mask_green, kernel, iterations=2)
    mask_red = cv2.erode(mask_red, kernel, iterations=1)
    mask_red = cv2.dilate(mask_red, kernel, iterations=2)

    current_centers = []

    # КОНТУРЫЫЫЫЫЫЫЫ
    contours_green, _ = cv2.findContours(
        mask_green, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    contours_red, _ = cv2.findContours(
        mask_red, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    # Отрисовываем ROI
    cv2.rectangle(
        frame,
        (roi_x_green, roi_y_green),
        (roi_x_green + roi_width_green, roi_y_green + roi_height_green),
        (255, 255, 255),
        2,

    )
    cv2.rectangle(
        frame,
        (roi_x_red, roi_y_red),
        (roi_x_red + roi_width_red, roi_y_red + roi_height_red),
        (255, 255, 255),
        2,
    )

    # Рисуем контуры и центры объектов
    for contour in contours_green:
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
        abs_x = x + roi_x_green
        abs_y = y + roi_y_green


        # Вычисляем центр объекта
        center = (abs_x + w // 2, abs_y + h // 2)
        current_centers.append(center)

        # Рисуем прямоугольник вокруг объекта
        cv2.rectangle(frame, (abs_x, abs_y), (abs_x + w, abs_y + h), (0, 255, 0), 2)
        cv2.circle(frame, center, 5, (0, 0, 255), -1)

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

    current_centerss = []
    red_markers_count = 0
    data = []
    
    # Store centers from previous frame if not already defined
    if not hasattr(cv2, 'prev_red_centers'):
        cv2.prev_red_centers = []

    # Get current centers
    current_red_centers = []

    for contour in contours_red:
        # Игнор шума
        area = cv2.contourArea(contour)
        if area < 80 or area > 500:
            continue

        # Получаем прямоугольник, описывающий контур
        (x, y, w, h) = cv2.boundingRect(contour)

        # Проверяем соотношение сторон и площадь для фильтрации ложных срабатываний
        aspect_ratio = float(w) / h
        if aspect_ratio < 0.5 or aspect_ratio > 2.0:
            continue

        # Convert coordinates to original frame coordinates
        abs_x = x + roi_x_red
        abs_y = y + roi_y_red

        # Вычисляем центр объекта
        center = (abs_x + w // 2, abs_y + h // 2)

        # Дополнительная проверка на положение центра
        if (
            roi_x_red <= center[0] <= roi_x_red + roi_width_red
            and roi_y_red <= center[1] <= roi_y_red + roi_height_red
        ):
            current_red_centers.append(center)
            
            # Check if this center has moved compared to previous frame
            is_moving = True
            if cv2.prev_red_centers:
                min_dist = float('inf')
                for prev_center in cv2.prev_red_centers:
                    dist = np.sqrt((center[0] - prev_center[0])**2 + (center[1] - prev_center[1])**2)
                    min_dist = min(dist, min_dist)
                # If center hasn't moved much, it's not considered moving
                if min_dist < 5:  # threshold for movement detection
                    is_moving = False
            
            if is_moving:
                red_markers_count += 1

            # Draw rectangle around the object
            cv2.rectangle(frame, (abs_x, abs_y), (abs_x + w, abs_y + h), (0, 0, 255), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)

    # Update previous centers for next frame
    cv2.prev_red_centers = current_red_centers.copy()
    print(red_markers_count)
    
    data.append(red_markers_count)

    # Find the most frequent count
    most_frequent_count = max(set(data), key=lambda x: data.count(x))

    # Display the average count of moving red markers on the frame
    cv2.putText(
        frame,
        f"Avg Red Markers: {most_frequent_count}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2,

    )

    # Обновляем траектории
    if current_centers:
        if not trajectories:
            for center in current_centers:
                trajectories[next_id] = [center]
                next_id += 1
                print(next_id)
        else:
            # Связываем текущие центры с существующими траекториями
            matched_centers = set()
            matched_trajectories = set()

            for track_id, track_points in trajectories.items():
                if not track_points:
                    continue
                last_point = track_points[-1]

                # Находим ближайший центр для текущей траектории
                min_dist = float("inf")
                closest_center = None

                for center in current_centers:
                    if center in matched_centers:
                        continue
                    dist = np.sqrt(
                        (center[0] - last_point[0]) ** 2
                        + (center[1] - last_point[1]) ** 2
                    )
                    if dist < min_dist and dist < max_distance:
                        min_dist = dist
                        closest_center = center

                if closest_center:
                    trajectories[track_id].append(closest_center)
                    matched_centers.add(closest_center)
                    matched_trajectories.add(track_id)

            # Создаем новые траектории для неcвязанных центров
            for center in current_centers:
                if center not in matched_centers:
                    trajectories[next_id] = [center]
                    next_id += 1

            # Удаляем старые траектории
            trajectories = {k: v for k, v in trajectories.items() if len(v) > 0}

    # Рисуем траектории
    colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
    ]  # Разные цвета для разных траекторий   ----- надо фиксить ошбки траекторий
    for track_id, points in trajectories.items():
        if len(points) > 1:
            color = colors[track_id % len(colors)]
            for i in range(1, len(points)):
                cv2.line(frame, points[i - 1], points[i], color, 2)

        # Ограничиваем длину траектории
        if len(points) > 50:
            trajectories[track_id] = points[-50:]

    # Показываем кадр и маску
    cv2.imshow("Frame", frame)
    cv2.imshow("Mask_green", mask_green)
    cv2.imshow("Mask_red", mask_red)

    # Выход по нажатию клавиши q
    if cv2.waitKey(30) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
