import cv2
import numpy as np
from config import *


# load hsv
lower_hsv = vivo_lower_hsv
upper_hsv = vivo_upper_hsv

# Define ROI coordinates
roi_x, roi_y = 1117, 258
roi_width, roi_height = 785, 713

# Загрузка видеофайла
cap = cv2.VideoCapture(vivo_video)


# Проверка, что видео загружено корректно
if not cap.isOpened():
    print("Ошибка: видео не загружено.")
    exit()

# Список для хранения траекторий нескольких объектов
trajectories = {}  # Словарь для хранения траекторий {id: points}
next_id = 0  # Счетчик для назначения ID объектам
max_distance = 120  # Максимальное расстояние для связывания точек


while True:
    ret, frame = cap.read()
    if not ret:
        break  # Выход, если видео закончилось

    # Extract ROI from frame
    roi = frame[roi_y:roi_y+roi_height, roi_x:roi_x+roi_width]

    # Конвертируем ROI в HSV
    hsv_frame = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

    # Создаем маску для диапазона цветов в HSV
    mask = cv2.inRange(hsv_frame, lower_hsv, upper_hsv)

    # уменьшения шума
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)

    current_centers = []

    # Находим контуры объектов на маске
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Draw ROI rectangle on original frame
    cv2.rectangle(frame, (roi_x, roi_y), (roi_x + roi_width, roi_y + roi_height), (255, 255, 255), 2)

    # Рисуем контуры и центры объектов
    for contour in contours:
        # Игнорируем слишком маленькие контуры (шум)
        area = cv2.contourArea(contour)
        if area < 75:  # Уменьшаем минимальную площадь для более чувствительного обнаружения
            continue

        # Получаем прямоугольник, описывающий контур
        (x, y, w, h) = cv2.boundingRect(contour)
        
        # Проверяем соотношение сторон и площадь для фильтрации ложных срабатываний
        aspect_ratio = float(w) / h
        if aspect_ratio < 0.2 or aspect_ratio > 5:
            continue

        # Convert coordinates to original frame coordinates
        abs_x = x + roi_x
        abs_y = y + roi_y

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

    # Обновляем траектории
    if current_centers:
        # Если траектории пустые, создаем новые
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
                min_dist = float('inf')
                closest_center = None
                
                for center in current_centers:
                    if center in matched_centers:
                        continue
                    dist = np.sqrt((center[0] - last_point[0])**2 + (center[1] - last_point[1])**2)
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
    colors = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)]  # Разные цвета для разных траекторий
    for track_id, points in trajectories.items():
        if len(points) > 1:
            color = colors[track_id % len(colors)]
            for i in range(1, len(points)):
                cv2.line(frame, points[i-1], points[i], color, 2)

        # Ограничиваем длину траектории
        if len(points) > 50:
            trajectories[track_id] = points[-50:]

    # Показываем кадр и маску
    cv2.imshow("Frame", frame)
    cv2.imshow("Mask", mask)

    # Выход по нажатию клавиши 'q'
    if cv2.waitKey(30) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()
