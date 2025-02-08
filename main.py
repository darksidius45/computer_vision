import cv2
import numpy as np
from config import get_camera_settings


# load all settings
camera_type = "pixel_stable"
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


# Загрузка видеофайла

cap = cv2.VideoCapture(video)
cap.set(cv2.CAP_PROP_POS_MSEC, start_time)  # включаем видео с 3 секунды


if not cap.isOpened():
    print("Ошибка: видео не загружено.")
    exit()


trajectories = {}  # Словарь для хранения траекторий {id: points}
next_id = 0  # Счетчик для назначения ID объектам
max_distance = 120
ob_info = {}  # Максимальное расстояние для связывания точек


while True:
    ret, frame = cap.read()
    if not ret:
        break  # Выход, если видео закончилось

    # Extract ROI from frame
    roi = frame[
        roi_y_machine : roi_y_machine + roi_height_machine,
        roi_x_machine : roi_x_machine + roi_width_machine,
    ]

    roi_weight = frame[
        roi_y_weight : roi_y_weight + roi_height_weight, roi_x_weight : roi_x_weight + roi_width_weight
    ]
    # Конвертируем ROI в HSV


    hsv_frame_machine = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    hsv_frame_weight = cv2.cvtColor(roi_weight, cv2.COLOR_BGR2HSV)



    # маски для диапазона цветов в HSV
    mask_machine = cv2.inRange(hsv_frame_machine, lower_hsv_machine, upper_hsv_machine)




    # создаем 2 маски для красного цвета в разных диапазонах из-за особенностей hsv формата потом объединяем их в 1
    mask_weight1 = cv2.inRange(hsv_frame_weight, lower_hsv_weight1, upper_hsv_weight1)
    mask_weight2 = cv2.inRange(hsv_frame_weight, lower_hsv_weight2, upper_hsv_weight2)
    mask_weight = cv2.bitwise_or(mask_weight1, mask_weight2)


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
        if area < 300:
            continue

        # Получаем прямоугольник, описывающий контур
        (x, y, w, h) = cv2.boundingRect(contour)

        # Проверяем соотношение сторон и площадь для фильтрации ложных срабатываний
        aspect_ratio = float(w) / h
        if aspect_ratio < 0.5 or aspect_ratio > 2.0:
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

    # Track objects across frames
    for obj_id, prev_center in ob_info.items():
        # Находим ближайший центр в текущем кадре
        min_distance = float('inf')
        closest_center = None

        for center in current_weight_centers:
            distance = np.linalg.norm(np.array(prev_center[0]) - np.array(center))
            if distance < min_distance:
                min_distance = distance
                closest_center = center

        if closest_center is not None and min_distance < 50:  # Увеличил порог расстояния
            updated_objects[obj_id] = [closest_center, prev_center[1] + 1]
            current_weight_centers.remove(closest_center)
        else:
            # Если объект не обнаружен в течение 5 кадров, удаляем его
            if prev_center[1] < 5:
                updated_objects[obj_id] = [prev_center[0], 0]

    # Add new objects only if they persist for a few frames
    if len(ob_info) == 0:
        next_object_id = 0
    else:
        # Очищаем неактивные ID перед добавлением новых
        active_ids = [id for id, info in updated_objects.items() if info[1] > 0]
        next_object_id = max(active_ids) + 1 if active_ids else 0

    # Добавляем новые объекты только если есть свободное место (максимум 10 объектов)
    for center in current_weight_centers:
        if len(updated_objects) < 10:
            updated_objects[next_object_id] = [center, 0]
            next_object_id += 1

    ob_info = updated_objects




    cv2.rectangle(frame, (abs_x, abs_y), (abs_x + w, abs_y + h), (0, 0, 255), 2)



    for obj_id, center in ob_info.items():
        cv2.putText(frame, f"ID: {obj_id}", (center[0][0] - 20, center[0][1] - 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

    not_in = 0
    for obj_id, center in ob_info.items():
        if center[1] > 3:
            not_in += 1
    print(len(ob_info) - not_in)




    data.append(weight_markers_count)




    # Find the most frequent count
    most_frequent_count = max(set(data), key=lambda x: data.count(x))

    # Display the average count of moving red markers on the frame
    cv2.putText(
        frame,
        f"Avg weight Markers: {most_frequent_count}",
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
    # Set window sizes
    frame_width = 800
    frame_height = 600
    mask_width = 400
    mask_height = 300

    # Resize images
    frame_resized = cv2.resize(frame, (frame_width, frame_height))
    mask_machine_resized = cv2.resize(mask_machine, (mask_width, mask_height))
    mask_weight_resized = cv2.resize(mask_weight, (mask_width, mask_height))

    # Show resized windows
    cv2.imshow("Frame", frame_resized)
    cv2.imshow("Mask_machine", mask_machine_resized)
    cv2.imshow("Mask_weight", mask_weight_resized)

    # Position windows
    cv2.moveWindow("Frame", 0, 0)
    cv2.moveWindow("Mask_machine", frame_width, 0)
    cv2.moveWindow("Mask_weight", frame_width + mask_width, 0)


    # Выход по нажатию клавиши q
    if cv2.waitKey(30) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
