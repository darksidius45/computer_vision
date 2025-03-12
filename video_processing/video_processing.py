import cv2
import numpy as np
import time
import queue
import threading
import psutil  

from .config import get_camera_settings
from .machine import machine_trajectory
from .weights import weights_detection


video_queue = queue.Queue()  # Очередь для видео
processing_thread = None 
stop_processing = False

# Инициализация системы
def init_system(callback, camera_type="rasberry", core_num=3):
    """
    Initialize the system and set processing thread to run on a specific CPU core.
    
    Args:
        camera_type (str): Type of camera to use
        core_num (int): CPU core number (0-based index) to run the thread on
        callback (callable): Function to call with results after processing completes
    """
    global processing_thread
    
    # Запускаем поток обработки видео с передачей callback функции
    processing_thread = threading.Thread(
        target=process_video, 
        args=(callback, camera_type)
    )
    processing_thread.start()
    
    # Get thread ID and set CPU affinity
    thread_id = processing_thread.native_id
    if thread_id:
        try:
            # Create a process handle
            p = psutil.Process()
            
            # Get the number of CPU cores
            available_cores = psutil.cpu_count()
            
            # Make sure the requested core exists
            if core_num < 0 or core_num >= available_cores:
                print(f"Warning: Core {core_num} not available. Using default core assignment.")
            else:
                # Set affinity to only use the specified core
                p.cpu_affinity([core_num])
                print(f"Video processing thread assigned to CPU core {core_num}")
        except Exception as e:
            print(f"Failed to set CPU core affinity: {e}")


# Завершение системы
def stop_system():
    global stop_processing
    stop_processing = True
    if processing_thread:
        processing_thread.join()
    print("Система завершена.")


def process_video(callback, camera_type="rasberry"):
    while not stop_processing:
        try:
            # Берем видео из очереди (с таймаутом, чтобы не блокировать поток навсегда)
            video_filename = video_queue.get(timeout=1)
            if video_filename:
                print(f"Начало обработки видео: {video_filename}")
                result = video_handling(video_filename, camera_type)
                # Extract user_id from the filename (format: user_id_counter.mp4)
                user_id = video_filename.split('_')[0]
                # Pass both result and user_id to the callback
                callback(result, user_id)
                print(f"Обработка завершена: {video_filename}")
        except queue.Empty:
            print("no interesting video")
            time.sleep(5)
            continue


def video_handling(video_path, camera_type="rasberry"):
    """
    Process video for exercise tracking and weight detection

    Parameters:
        video_path (str): Path to the video file
        camera_type (str): Type of camera to load appropriate settings

    Returns:
        dict: Dictionary containing exercise data
    """
    # load settings based on camera_type
    camera_settings = get_camera_settings(camera_type)

    # цветовые диапазоны для метки на тренажере
    lower_hsv_machine = camera_settings["lower_hsv_machine"]
    upper_hsv_machine = camera_settings["upper_hsv_machine"]

    # цветовые диапазоны для меток весов
    lower_hsv_weight1 = camera_settings["lower_hsv_weight1"]
    upper_hsv_weight1 = camera_settings["upper_hsv_weight1"]
    lower_hsv_weight2 = camera_settings["lower_hsv_weight2"]
    upper_hsv_weight2 = camera_settings["upper_hsv_weight2"]

    # диапазон для метки на тренажёре
    roi_x_machine = camera_settings["roi_x_machine"]
    roi_y_machine = camera_settings["roi_y_machine"]
    roi_width_machine = camera_settings["roi_width_machine"]
    roi_height_machine = camera_settings["roi_height_machine"]

    # диапазон для меток на весах
    roi_x_weight = camera_settings["roi_x_weight"]
    roi_y_weight = camera_settings["roi_y_weight"]
    roi_width_weight = camera_settings["roi_width_weight"]
    roi_height_weight = camera_settings["roi_height_weight"]

    # настройки под тренажёр

    max_hight = camera_settings["max_hight"]
    min_hight = camera_settings["min_hight"]
    set_timer = camera_settings["set_timer"]
    rep_dist = camera_settings["rep_dist"]

    # Загрузка
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, 10000)  # включаем видео с определённой секунды

    if not cap.isOpened():
        print("Error: Could not open video.")
        return None

    # Create custom parameters for the CSRT tracker
    params = cv2.TrackerCSRT_Params()
    params.padding = 3.0
    params.template_size = 150
    params.gsl_sigma = 1.0
    params.hog_orientations = 3
    params.num_hog_channels_used = 2
    params.hog_clip = 0.2
    params.filter_lr = 0.02
    params.weights_lr = 0.02
    params.admm_iterations = 3
    params.number_of_scales = 60
    params.scale_sigma_factor = 0.25
    params.scale_model_max_area = 300
    params.scale_lr = 0.05
    params.scale_step = 1.02
    params.histogram_bins = 16
    params.background_ratio = 4
    params.histogram_lr = 0.04

    # Create tracker with custom parameters
    tracker = cv2.TrackerCSRT_create(params)

    tracked = False
    trajectories = []  # Словарь для хранения траекторий {id: points}
    next_id = 0  # Счетчик для назначения ID объектам
    max_distance = 120
    ob_info = {}  # Максимальное расстояние для связывания точек
    exercises = {"1": []}

    start_time = time.time()
    prev_frame_time = start_time

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        elapsed_time = time.time() - start_time

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
        mask_machine = cv2.inRange(
            hsv_frame_machine, lower_hsv_machine, upper_hsv_machine
        )

        # создаем 2 маски для красного цвета в разных диапазонах из-за особенностей hsv формата потом объединяем их в 1
        mask_weight = cv2.inRange(
            hsv_frame_weight, lower_hsv_weight1, upper_hsv_weight1
        )
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
            center = ((abs_x + w // 2), (abs_y + h // 2))
            current_centers.append(center)

            # Рисуем прямоугольник вокруг объекта
            cv2.circle(frame, center, 5, (0, 255, 0), -1)

            current_centers.append(center)
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
        ob_info, next_id, weight = weights_detection(
            frame,
            current_weight_centers,
            ob_info,
            updated_objects,
            next_id,
            max_distance,
        )

        # Resize ROI for optimization
        roi = cv2.resize(roi, (roi.shape[1] // 2, roi.shape[0] // 2))
        # Обновляем траектории
        tracked, exercises = machine_trajectory(
            roi,
            current_centers,
            trajectories,
            min_hight,
            max_hight,
            rep_dist,
            set_timer,
            tracker,
            tracked,
            exercises,
            frame,
            weight,
        )
        

        # # Calculate frame size to fit screen while maintaining aspect ratio
        # frame_height = int(screen_height * 0.8)  # Use 80% of screen height
        # frame_width = int(frame.shape[1] * frame_height / frame.shape[0])

        # # Ensure frame width doesn't exceed screen width
        # if frame_width > screen_width * 0.8:
        #     frame_width = int(screen_width * 0.8)
        #     frame_height = int(frame.shape[0] * frame_width / frame.shape[1])

        # # Resize frame only
        # frame_resized = cv2.resize(frame, (frame_width, frame_height))

        # # Resize masks to half size
        # mask_machine_resized = cv2.resize(
        #     mask_machine, (mask_machine.shape[1] // 2, mask_machine.shape[0] // 2)
        # )

        # mask_weight_resized = cv2.resize(
        #     mask_weight, (mask_weight.shape[1] // 2, mask_weight.shape[0] // 2)
        # )

        # # Calculate FPS
        # new_frame_time = time.time()
        # fps = 1 / (new_frame_time - prev_frame_time)
        # prev_frame_time = new_frame_time

        # # Display FPS on frame
        # cv2.putText(
        #     frame_resized,
        #     f"FPS: {int(fps)}",
        #     (10, 400),
        #     cv2.FONT_HERSHEY_SIMPLEX,
        #     1,
        #     (255, 0, 0),
        #     2,
        #     cv2.LINE_AA,
        # )

        # Show windows
        # cv2.imshow("Frame", frame_resized)
        # cv2.imshow("Mask_machine", mask_machine_resized)
        # cv2.imshow("Mask_weight", mask_weight_resized)

        # # Position windows
        # cv2.moveWindow("Frame", 0, 0)
        # cv2.moveWindow("Mask_machine", frame_width + 10, 0)
        # cv2.moveWindow(
        #     "Mask_weight", frame_width + mask_machine_resized.shape[1] + 20, 0
        # )

        # Выход по нажатию клавиши q
        if cv2.waitKey(30) & 0xFF == ord("q"):
            break

    cap.release()
    # cv2.destroyAllWindows()
    print(exercises)
    return exercises



video_handling("test_videos/rassbery.mp4", "rasberry")
    