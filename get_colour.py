import cv2
import numpy as np

# Глобальные переменные для хранения координат, цвета и масштаба
coords = []
color = None
scale = 1.0
zoom_pt = None

def zoom(img, center, scale):
    height, width = img.shape[:2]
    # Вычисляем матрицу масштабирования с центром в текущей позиции мыши
    center_x, center_y = center
    src_pts = np.float32([
        [center_x - width/2, center_y - height/2],
        [center_x + width/2, center_y - height/2],
        [center_x - width/2, center_y + height/2]
    ])
    dst_pts = np.float32([
        [(center_x - width/2)*scale, (center_y - height/2)*scale],
        [(center_x + width/2)*scale, (center_y - height/2)*scale],
        [(center_x - width/2)*scale, (center_y + height/2)*scale]
    ])
    M = cv2.getAffineTransform(src_pts, dst_pts)
    return cv2.warpAffine(img, M, (width, height))

def get_color_from_video():
    # Загрузка видеофайла
    video_path = r'C:\Users\prive\Desktop\prog\computer_vision\test_videos\PXL_20250203_111501037.mp4'  # Укажи путь к своему видеофайлу
    cap = cv2.VideoCapture(video_path)
    paused = False

    # Проверка, что видео загружено корректно
    if not cap.isOpened():
        print("Ошибка: видео не загружено.")
        return

    def mouse_callback(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN and paused:
            frame = param
            color = frame[y, x]
            
            # Выводим информацию о цвете
            print(f"Координаты: ({x}, {y}), Цвет в формате BGR: {color}")
            
            # Преобразуем цвет в RGB и HSV для удобства
            rgb_color = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2RGB)[0][0]
            hsv_color = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2HSV)[0][0]
            print(f"Цвет в формате RGB: {rgb_color}")
            print(f"Цвет в формате HSV: {hsv_color}")
            
            # Показываем цвет в отдельном окне
            color_image = np.zeros((100, 100, 3), dtype=np.uint8)
            color_image[:, :] = color
            cv2.imshow('Selected Color', color_image)

    cv2.namedWindow('Video')
    
    while True:
        if not paused:
            ret, frame = cap.read()
            if not ret:
                break

        cv2.setMouseCallback('Video', mouse_callback, frame)
        cv2.imshow('Video', frame)

        key = cv2.waitKey(30) & 0xFF
        if key == ord('q'):
            break
        elif key == ord(' '):  # Пробел для паузы
            paused = not paused

    cap.release()
    cv2.destroyAllWindows()

# Функция для обработки событий мыши
def get_pixel_color(event, x, y, flags, param):
    global color, scale, zoom_pt
    
    if event == cv2.EVENT_MOUSEWHEEL:
        if flags > 0:
            scale *= 1.1
        else:
            scale *= 0.9
        scale = max(1.0, min(5.0, scale))  # Ограничиваем масштаб от 1x до 5x
        
        if zoom_pt is None:
            zoom_pt = (x, y)
        
        # Создаем увеличенное изображение
        zoomed = zoom(image.copy(), zoom_pt, scale)
        cv2.imshow('Image', zoomed)
        
    elif event == cv2.EVENT_LBUTTONDOWN:
        zoom_pt = (x, y)
        coords.append((x, y))
        
        # Получаем цвет из оригинального изображения
        color = image[y, x]
        print(f"Координаты: ({x}, {y}), Цвет в формате BGR: {color}")

        # Преобразуем цвет в RGB и HSV для удобства
        rgb_color = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2RGB)[0][0]
        hsv_color = cv2.cvtColor(np.uint8([[color]]), cv2.COLOR_BGR2HSV)[0][0]
        print(f"Цвет в формате RGB: {rgb_color}")
        print(f"Цвет в формате HSV: {hsv_color}")

        # Показываем цвет в отдельном окне
        color_image = np.zeros((100, 100, 3), dtype=np.uint8)
        color_image[:, :] = color
        cv2.imshow('Color', color_image)

        # Рисуем круг на изображении
        zoomed = zoom(image.copy(), zoom_pt, scale)
        cv2.circle(zoomed, (x, y), 5, (0, 255, 0), 2)
        cv2.imshow('Image', zoomed)


image = cv2.imread('image.png')  # Замени 'image.jpg' на путь к своему изображению

# Загрузка видеофайла
get_color_from_video()
# Проверка, что видео загружено корректно
