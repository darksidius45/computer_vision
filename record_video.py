import cv2
from video_processing.config import get_camera_settings
from video_processing.camera import process_frame
from video_processing.video_processing import video_queue

def record_video(camera_type="rasberry", file_name="output.mp4",):
    """
    Records video from camera until specific conditions are met.
    
    Args:
        camera_type (str): Type of camera configuration to use ("rasberry", etc.)
        file_name (str): Name of the output video file
        
    Returns:
        bool: True if recording completed successfully, False otherwise
    """
    # load all settings
    camera_settings = get_camera_settings(camera_type)

    # цветовые диапазоны для метки на тренажере
    lower_hsv_machine = camera_settings["lower_hsv_machine"]
    upper_hsv_machine = camera_settings["upper_hsv_machine"]

    # диапазон для метки на тренажёре
    roi_x_machine = camera_settings["roi_x_movement"]
    roi_y_machine = camera_settings["roi_y_movement"]
    roi_width_machine = camera_settings["roi_width_movement"]
    roi_height_machine = camera_settings["roi_height_movement"]

    # настройки под тренажёр
    stop_timer = camera_settings["stop_timer"]

    # Initialize video capture with test video
    cap = cv2.VideoCapture(r"C:\Users\prive\Desktop\prog\HSMG_CV\test_videos\rasberry1.mp4")
    # Set starting position to 30 seconds (30000 milliseconds)
    # cap.set(cv2.CAP_PROP_POS_MSEC, 15000)

    # Проверка, успешно ли открыт видеозахват
    if not cap.isOpened():
        print("Ошибка: Не удалось открыть камеру.")
        return False
        
    # Настройка кодек и создание объекта VideoWriter
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # MP4 codec
    out = cv2.VideoWriter(file_name, fourcc, 30.0, (1920, 1080))
    recording = False
    if  hasattr(process_frame, "break_time"):
        process_frame.break_time = 0
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Ошибка: Не удалось получить кадр.")
                break

            if not recording:
                # Начать запись, если еще не начали
                recording = True
                print(f"Начало записи в файл {file_name}...")

            # Запись кадра
            out.write(frame)

            # Анализ кадра
            if process_frame(
                frame,
                roi_x_machine,
                roi_y_machine,
                roi_width_machine,
                roi_height_machine,
                lower_hsv_machine,
                upper_hsv_machine,
                stop_timer,
            ):
                print("Условие для остановки записи выполнено.")
                break

            # Отображение кадра

            frame = cv2.resize(frame, (1280, 720))

            cv2.imshow("Frame", frame)
            

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
                break

        # Освобождение ресурсов
        cap.release()
        out.release()
        cv2.destroyWindow("Frame")

        print(f"Запись завершена и сохранена в '{file_name}'.")
        video_queue.put(file_name)
        return True
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        # Освобождение ресурсов при ошибке
        cap.release()
        out.release()
        # cv2.destroyAllWindows()

        return False

