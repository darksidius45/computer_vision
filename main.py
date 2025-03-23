import requests
import json
import time
import io
import base64
from PIL import Image, ImageTk
import tkinter as tk
import threading
import queue

from video_processing.video_processing import init_system, stop_system
from record_video import record_video

camera_type = "rasberry"
counter = 0

id_camera = 3
id_user = "-1"
token = ""

host = "http://104.238.29.249:8080"
camera_file = "camera.py"
cv_file = "cv.py"

root = None
tk_image = None
gui_queue = queue.Queue()  # Queue for GUI operations

def auth_cam(user_id):
    print("")
    url = host + '/api/auth_for_camera/' + str(user_id)
    print(url)
    try:
        response = requests.post(url)
        print(f'Status Code: {response.status_code}')
        
        # Проверяем заголовок Content-Type (необязательно, но рекомендуется)
        content_type = response.headers.get('Content-Type', '')
        
        if 'application/json' not in content_type:
            print(f'Неожиданный Content-Type: {content_type}. Ответ не в JSON формате')
        
        # Пытаемся распарсить JSON
        try:
            json_data = response.json()
            print('Успешно распарсен JSON ответ55:')
            print(json.dumps(json_data, indent=4, ensure_ascii=False))
            if(json_data["token"] != "-1"):
                print("666")
                token = json_data["token"]
                return token
            print("777")
            
        except json.decoder.JSONDecodeError:
            print(f'Ошибка декодирования JSON. Ответ сервера: {response.text}')
            
    except Exception as e:
        print(f'Непредвиденная ошибка324: {e}')
    print("token")
    print(token)
    return "ERRROROR ERROR "


def show_image(base64_data):
    global root, tk_image

    # Decode Base64 to binary data
    image_data = base64.b64decode(base64_data)

    # Create image from binary data
    image = Image.open(io.BytesIO(image_data))

    # Get screen dimensions
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Calculate size for square QR code (use the smaller dimension)
    qr_size = min(screen_width, screen_height) * 0.7  # 70% of smaller dimension
    
    # Resize image to be square
    image = image.resize((int(qr_size), int(qr_size)), Image.Resampling.LANCZOS)

    # Convert image to Tkinter format
    tk_image = ImageTk.PhotoImage(image)

    # Clear existing widgets
    for widget in root.winfo_children():
        widget.destroy()
    
    # Center the QR code in the window
    frame = tk.Frame(root, width=screen_width, height=screen_height)
    frame.pack(fill="both", expand=True)
    
    label = tk.Label(frame, image=tk_image)
    label.place(relx=0.5, rely=0.5, anchor="center")

def close_image_window():
    pass  # This is now handled differently

def create_new_window_with_qr():
    qr_code = getQR()
    if qr_code:
        show_image(qr_code)

def handle_gui_requests():
    """Process GUI requests from the queue."""
    try:
        while True:
            # Get a request from the queue without blocking
            request, args = gui_queue.get_nowait()
            
            if request == "show_qr":
                create_new_window_with_qr()
            elif request == "close":
                # Just clear the window, don't destroy it
                for widget in root.winfo_children():
                    widget.destroy()
                
            gui_queue.task_done()
    except queue.Empty:
        # Queue is empty, schedule next check
        if root:
            root.after(100, handle_gui_requests)

def getQR():
    url = host + '/api/generate_qr/' + str(id_camera)
    try:
        response = requests.get(url)
        print(f'Status Code: {response.status_code}')
            
        # Проверяем заголовок Content-Type (необязательно, но рекомендуется)
        content_type = response.headers.get('Content-Type', '')
            
        if 'application/json' not in content_type:
            print(f'Неожиданный Content-Type: {content_type}. Ответ не в JSON формате')
            
        # Пытаемся распарсить JSON
        try:
            json_data = response.json()
            print('Успешно распарсен JSON ответ:')
            print(json.dumps(json_data, indent=4, ensure_ascii=False))

            image_data = base64.b64decode(json_data["qr_code"])
            image = Image.open(io.BytesIO(image_data))
            return json_data["qr_code"]
        except Exception as e:
            print(f'Непредвиденная ошибка2: {e}')
    except Exception as e:
        print(f'Непредвиденная ошибка1: {e}')



def second_part(result, user_id):
    print("second")
    token = auth_cam(user_id)
    print(token)
    # Calculate the average weight from the first set (approach)
    weights = 0
    count_done = 0
    if result:  # Check if first set exists
        approach_data = result["1"]
        count_done = len(approach_data)  # Get data for the first approach
        weights_in_approach = [rep_data[0] for rep_data in approach_data if rep_data]  # Extract weights
        
        if weights_in_approach:
            weights = sum(weights_in_approach) / len(weights_in_approach)  # Calculate average
    
    url = host + '/api/done_exercise_by_user'
                    
    data = {
        "id": 1,
        "sequence_number": 2,
        "id_exercise": 3,
        "name": "Bench press",
        "example_exercise": "",
        "weight": 100.0,
        "count": 12,
        "rest_time": "3 seconds",
        "is_it_done": True,
        "weight_done": weights,
        "count_done": count_done,
    }
    print("lKJKJDLSKFJLSKDJFLKSDJFLKDJFLKSDJFLKDSJFLKDSJFLKSDJFLKSJD")
    
                    
                    # Bearer Token
                
                    # Заголовки запроса, включая Bearer Token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    print(headers)
    try:
        # Отправка POST-запроса 
        response = requests.post(url, json=data, headers=headers)
        response.raise_for_status()  # Проверка на ошибки HTTP
                        
        print("Status Code:", response.status_code)
        print("Response Body:", response.json())
        print(data)
        token = ""
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
    except Exception as err:
        print(f"An error occurred: {err}")
        

def main():
    global counter
    i = 0
    while(i < 300):  # Можно сделать бесконечный цикл while True:
        url = host + '/api/get_info_about_camera/' + str(id_camera)

        try:
            response = requests.get(url)
            print(f'Status Code: {response.status_code}')
            
            # Process JSON response
            try:
                json_data = response.json()
                print('Успешно распарсен JSON ответ:')
                print(json.dumps(json_data, indent=4, ensure_ascii=False))
                
                if json_data["id_user"] != "-1":
                    id_user = json_data["id_user"]
                    print("????")
                    
                    # Close QR code window (thread-safe)
                    gui_queue.put(("close", None))
                    
                    print("!!!")
                    print(json_data["id_user"])
                    
                    token = auth_cam(id_user)
                    
                    # Записываем видео
                    filename = f"{id_user}_{counter}.mp4"
                    record_video(camera_type, filename)
                    counter += 1  # Увеличиваем счетчик для следующего файла
                    print(f"FUCKING TOKEN {token}")
                    
                    # Show QR code again (thread-safe)
                    id_user = "-1"
                    gui_queue.put(("show_qr", None))
                    
                    # Продолжаем цикл вместо выхода
                    main()
                    break
                    #continue
                    
            except json.decoder.JSONDecodeError:
                print(f'Ошибка декодирования JSON. Ответ сервера: {response.text}')

        except requests.exceptions.ConnectionError:
            print(f'Ошибка подключения к {url}. Убедитесь, что сервер запущен.')
        except requests.exceptions.RequestException as e:
            print(f'Ошибка запроса: {e}')
        except Exception as e:
            print(f'Непредвиденная ошибка: {e}')
        
        time.sleep(5)
        i+=1

# Начальная настройка программы
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Изображение")

    # Показываем первый QR-код
    create_new_window_with_qr()

    
    # Start GUI request handler
    root.after(100, handle_gui_requests)

    # Запускаем основной код в отдельном потоке
    main_thread = threading.Thread(target=main)
    main_thread.start()
    
    # Инициализируем систему обработки видео
    init_system(second_part, camera_type, 3)
    
    # Запускаем главный цикл Tkinter
    root.mainloop()

    # Ожидание завершения потока с основным кодом
    main_thread.join()

    stop_system()
