import cv2
from video_processing.config import get_camera_settings
from video_processing.camera import process_frame
from video_processing.video_processing import video_queue
from picamera2 import Picamera2
import time

def record_video(camera_type="rasberry", file_name="output.mp4",):
    """
    Records video from camera until specific conditions are met.
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

    # Устанавливаем более низкую частоту кадров для стабильной записи
    target_fps = 20  # Снижаем до 20 fps для более устойчивой записи
    frame_delay = 1.0 / target_fps

    # Инициализация камеры
    if camera_type == "rasberry":
        try:
            camera = Picamera2()
            print("# Initialize PiCamera2")
            
            # Важно: устанавливаем частоту кадров ниже требуемой,
            # чтобы избежать переполнения буфера
            camera_config = camera.create_video_configuration(
                main={"size": (1920, 1080), "format": "RGB888"}, 
                controls={"FrameRate": target_fps, "AwbEnable": True}
            )
            camera.configure(camera_config)
            
            camera.start(show_preview=False)
            print("camera start")
            
            class PiCameraCapture:
                def read(self):
                    frame = camera.capture_array()
                    return (True, frame)
                
                def release(self):
                    camera.stop()
                    print("Camera stopped")
                
                def isOpened(self):
                    return True
                
                def set(self, *args, **kwargs):
                    return True
            
            cap = PiCameraCapture()
            
        except ImportError:
            print("Error: PiCamera2 module not available")
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
            cap.set(cv2.CAP_PROP_FPS, target_fps)
    else:
        cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("Ошибка: Не удалось открыть камеру.")
        return False
        
    # Используем H.264 кодек вместо mp4v для лучшего контроля времени
    # Для Raspberry Pi часто лучше работает h264
    fourcc = cv2.VideoWriter_fourcc(*'H264') if cv2.__version__ >= '4.0.0' else cv2.VideoWriter_fourcc(*'X264')
    out = cv2.VideoWriter(file_name, fourcc, target_fps, (1920, 1080))
    
    recording = False
    if hasattr(process_frame, "break_time"):
        process_frame.break_time = 0
    
    frame_count = 0
    start_time = time.time()
    
    try:
        last_frame_time = time.time()
        
        while True:
            # Строгий контроль времени
            current_time = time.time()
            elapsed = current_time - last_frame_time
            
            # Если не прошло достаточно времени - ждем
            if elapsed < frame_delay:
                wait_time = frame_delay - elapsed
                time.sleep(wait_time)
            
            frame_count += 1
            last_frame_time = time.time()
            
            # Получаем кадр
            ret, frame = cap.read()
            if not ret or frame is None:
                print("Ошибка: Не удалось получить кадр.")
                break

            if not recording:
                recording = True
                print(f"Начало записи в файл {file_name}...")

            # Запись кадра
            out.write(frame)
            
            # Отладочная информация о частоте кадров
            if frame_count % 30 == 0:
                current = time.time()
                actual_fps = frame_count / (current - start_time)
                print(f"Текущая частота кадров: {actual_fps:.2f} fps")
            
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
            
            frame_display = cv2.resize(frame, (1280, 720))
            cv2.imshow("Frame", frame_display)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Освобождение ресурсов
        cap.release()
        out.release()
        cv2.destroyWindow("Frame")

        # Финальная информация о записи
        elapsed_time = time.time() - start_time
        actual_fps = frame_count / elapsed_time
        print(f"Запись завершена. Сохранено {frame_count} кадров за {elapsed_time:.2f} секунд.")
        print(f"Средняя частота кадров: {actual_fps:.2f} fps")
        print(f"Файл сохранен: {file_name}")
        
        video_queue.put(file_name)
        return True
        
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
        cap.release()
        out.release()
        return False
