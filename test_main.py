import cv2
import threading
import queue
import time
from datetime import datetime
from video_processing.video_processing import init_system, stop_system
from record_video import record_video


camera_type = "rasberry"
counter = 0

if __name__ == "__main__":
    # Инициализация системы
    init_system("rasberry")
    print("Система инициализирована. Нажмите 'r' для начала записи видео, 'q' для выхода.")
    
    # Create a window to capture key events
    cv2.namedWindow("Key Press Window", cv2.WINDOW_NORMAL)
    

    
    while True:
        # Read frame to show in window
        
        # Check for key press
        key = cv2.waitKey(1) & 0xFF
        
        # 'r' key to start recording
        if key == ord('r'):
            if record_video("rasberry", f"output{counter}.mp4"):
                counter += 1
                print(f"Video output{counter}.mp4 recorded successfully.")
        
        # 'q' key to quit the program
        elif key == ord('q'):
            print("Quitting program...")
            break

    stop_system()
# # Глобальные переменные
# video_queue = queue.Queue()  # Очередь для видео
# processing_thread = None     # Поток для обработки видео
# stop_processing = False      # Флаг для остановки потока обработки

# # Функция для анализа кадра (заглушка)
# def analyze_frame(frame):
#     # Здесь должен быть ваш код для анализа кадра
#     # Например, проверка на наличие определенного объекта или условия
#     # Возвращает True, если запись нужно остановить
#     return False

# Функция для записи видео
# def record_video(output_filename):
#     cap = cv2.VideoCapture(0)
#     if not cap.isOpened():
#         print("Ошибка: Не удалось открыть камеру.")
#         return

#     fourcc = cv2.VideoWriter_fourcc(*'XVID')
#     out = cv2.VideoWriter(output_filename, fourcc, 20.0, (640, 480))

#     print(f"Начало записи видео: {output_filename}")
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             print("Ошибка: Не удалось получить кадр.")
#             break

#         out.write(frame)

#         if analyze_frame(frame):
#             print(f"Условие для остановки записи выполнено: {output_filename}")
#             break

#     out.release()
#     cap.release()
#     print(f"Запись завершена: {output_filename}")

#     # Помещаем видео в очередь для обработки
#     video_queue.put(output_filename)

# # Функция для обработки видео
# def process_video():
#     while not stop_processing:
#         try:
#             # Берем видео из очереди (с таймаутом, чтобы не блокировать поток навсегда)
#             video_filename = video_queue.get(timeout=1)
#             if video_filename:
#                 print(f"Начало обработки видео: {video_filename}")
#                 # Здесь должен быть ваш код для обработки видео
#                 time.sleep(10)  # Имитация обработки (10 секунд)
#                 print(f"Обработка завершена: {video_filename}")
#         except queue.Empty:
#             # Если очередь пуста, продолжаем цикл
#             continue

# # Функция для запуска записи видео
# def start_recording():
#     # Генерируем уникальное имя файла на основе текущего времени
#     timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#     output_filename = f"output_{timestamp}.avi"

#     # Запускаем запись видео в отдельном потоке
#     recording_thread = threading.Thread(target=record_video, args=(output_filename,))
#     recording_thread.start()

# # Инициализация системы
# def init_system():
#     global processing_thread
#     # Запускаем поток обработки видео
#     processing_thread = threading.Thread(target=process_video)
#     processing_thread.start()

# # Завершение системы
# def stop_system():
#     global stop_processing
#     stop_processing = True
#     if processing_thread:
#         processing_thread.join()
#     print("Система завершена.")

# Пример использования
