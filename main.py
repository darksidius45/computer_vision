import cv2
import numpy as np

# Диапазоны HSV для маски, основанные на анализе цвета
lower_hsv = np.array([70, 90, 100])  # Минимальные значения H, S, V 
upper_hsv = np.array([85, 170, 180])  # Максимальные значения H, S, V

# Загрузка видеофайла
video_path = r'C:\Users\prive\Desktop\prog\computer_vision\test_videos\PXL_20250203_111501037.mp4'
cap = cv2.VideoCapture(video_path)

# Проверка, что видео загружено корректно
if not cap.isOpened():
    print("Ошибка: видео не загружено.")
    exit()

# Список для хранения точек траектории
trajectory_points = []

while True:
    ret, frame = cap.read()
    if not ret:
        break  # Выход, если видео закончилось

    # Конвертируем кадр в HSV
    hsv_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Создаем маску для диапазона цветов в HSV
    mask = cv2.inRange(hsv_frame, lower_hsv, upper_hsv)

    # Применяем морфологические операции для уменьшения шума
    kernel = np.ones((5,5), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    mask = cv2.dilate(mask, kernel, iterations=2)

    # Находим контуры объектов на маске
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Рисуем контуры и центры объектов
    for contour in contours:
        # Игнорируем слишком маленькие контуры (шум)
        area = cv2.contourArea(contour)
        if area < 75:  # Уменьшаем минимальную площадь для более чувствительного обнаружения
            continue

        # Получаем прямоугольник, описывающий контур
        (x, y, w, h) = cv2.boundingRect(contour)

        # Проверяем соотношение сторон и площадь для фильтрации ложных срабатываний
        aspect_ratio = float(w)/h
        if aspect_ratio < 0.2 or aspect_ratio > 5:
            continue

        # Рисуем прямоугольник вокруг объекта
        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Вычисляем и рисуем центр объекта
        center = (x + w // 2, y + h // 2)
        cv2.circle(frame, center, 5, (0, 0, 255), -1)
        
        # Добавляем точку в траекторию
        trajectory_points.append(center)
        
        # Выводим координаты центра
        cv2.putText(frame, f"({center[0]}, {center[1]})", (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
    
    # Рисуем траекторию
    if len(trajectory_points) > 1:
        for i in range(1, len(trajectory_points)):
            cv2.line(frame, trajectory_points[i-1], trajectory_points[i], (255, 0, 0), 2)
    
    # Ограничиваем длину траектории, чтобы не перегружать память
    if len(trajectory_points) > 50:
        trajectory_points.pop(0)

    # Показываем кадр и маску
    cv2.imshow('Frame', frame)
    cv2.imshow('Mask', mask)

    # Выход по нажатию клавиши 'q'
    if cv2.waitKey(30) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()