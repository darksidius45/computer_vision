import cv2
from video_processing.config import get_camera_settings

# from video_processing.video_processing import process_video
from camera import process_frame

# load all settings
camera_type = "rasberry"
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


cap = cv2.VideoCapture(camera_settings["video"])

# Проверка, успешно ли открыт видеозахват
if not cap.isOpened():
    print("Ошибка: Не удалось открыть камеру.")
    exit()
    # Настройка кодек и создание объекта VideoWriter
fourcc = cv2.VideoWriter_fourcc(*"mp4v")  # MP4 codec
out = cv2.VideoWriter("output.mp4", fourcc, 30.0, (1920, 1080))
recording = False


while True:
    ret, frame = cap.read()
    if not ret:
        print("Ошибка: Не удалось получить кадр.")
        break

    if not recording:
        # Начать запись, если еще не начали
        recording = True
        print("Начало записи...")

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

    cv2.rectangle(
        frame,
        (roi_x_machine, roi_y_machine),
        (roi_x_machine + roi_width_machine, roi_y_machine + roi_height_machine),
        (255, 255, 255),
        2,
    )
    # Отображение кадра (опционально)

    # Выход по нажатию 'q'
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

# Освобождение ресурсов
cap.release()
out.release()
cv2.destroyAllWindows()

print("Запись завершена и сохранена в 'output.mp4'.")
