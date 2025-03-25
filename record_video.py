import cv2
from video_processing.config import get_camera_settings
from video_processing.camera import process_frame
from video_processing.video_processing import video_queue
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput

import time

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

    # Параметры конфигурации
    lower_hsv_machine = camera_settings["lower_hsv_machine"]
    upper_hsv_machine = camera_settings["upper_hsv_machine"]
    roi_x_machine = camera_settings["roi_x_movement"]
    roi_y_machine = camera_settings["roi_y_movement"]
    roi_width_machine = camera_settings["roi_width_movement"]
    roi_height_machine = camera_settings["roi_height_movement"]
    stop_timer = camera_settings["stop_timer"]

    # Устанавливаем одинаковую частоту кадров для захвата и записи
    target_fps = 60  # Используем 30 fps для стабильной работы
    frame_delay = 1.0 / target_fps  # Задержка между кадрами

    # Initialize video capture with test video
    if camera_type == "rasberry2":
        try:
            
            # Initialize PiCamera2
            camera = Picamera2()
            print("# Initialize PiCamera2")
            # Configure the camera with the target fps
            camera_config = camera.create_video_configuration(
                main={"size": (1920, 1080), "format": "RGB888"}, 
                controls={"FrameRate": target_fps}
            )
            camera.configure(camera_config)
            
            # Start the camera
            camera.start(show_preview=False)
            print("camera start")
            
            # Use a custom capture class to provide a compatible interface
            class PiCameraCapture:
                def read(self):
                    frame = camera.capture_array()
                    return (True, frame)
                
                def release(self):
                    camera.stop()
                    camera.close()
                
                def isOpened(self):
                    return True
                
                def set(self, *args, **kwargs):
                    # This is a no-op since settings are configured above
                    return True
            
            cap = PiCameraCapture() 
            
        except ImportError:
            print("Error: PiCamera2 module not available, falling back to OpenCV capture")
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            cap.set(cv2.CAP_PROP_FPS, target_fps)
    else:
        # Fallback to default camera
        cap = cv2.VideoCapture(0)
    
    # Проверка, успешно ли открыт видеозахват
    if not cap.isOpened():
        print("Ошибка: Не удалось открыть камеру.")
        return False
        
    # Настройка кодека и создание объекта VideoWriter с тем же fps
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # MP4 codec
    #out = cv2.VideoWriter(file_name, fourcc, target_fps, (1920, 1080))
    recording = False
    encoder = H264Encoder(10000000)
    output = FfmpegOutput(file_name)
    if  hasattr(process_frame, "break_time"):
        process_frame.break_time = 0
    try:
        last_frame_time = time.time()
        while True:
            # Контролируем время между кадрами
            current_time = time.time()
            elapsed = current_time - last_frame_time
            
            # Если прошло меньше времени, чем нужно между кадрами - ждем
            if elapsed < frame_delay:
                time.sleep(frame_delay - elapsed)
            
            # Обновляем время последнего кадра
            last_frame_time = time.time()
            
            # Получаем кадр
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Ошибка: Не удалось получить кадр.")
                break

            if not recording:
                # Начать запись, если еще не начали
                recording = True
                camera.start_recording(encoder, output)
                print(f"Начало записи в файл {file_name}...")

            # Запись кадра
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
                camera.stop_recording()
                break
            
            # Отображение кадра
            frame_display = cv2.resize(frame, (1280, 720))
            cv2.imshow("Frame", frame_display)
            cv2.moveWindow("Frame", 0, 0)
            

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
                camera.stop_recording()

                break

        # Освобождение ресурсов
        cap.release()
        #out.release()
        cv2.destroyWindow("Frame")

        print(f"Запись завершена и сохранена в '{file_name}'.")
        video_queue.put(file_name)
        return True
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        # Освобождение ресурсов при ошибке
        cap.release()
        #out.release()
        # cv2.destroyAllWindows()

        return False
