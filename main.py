import requests
import json
import time
import subprocess
import io
import base64
from PIL import Image, ImageTk
import tkinter as tk
import threading

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
image_thread = None
is_running = True 

def auth_cam():
    global token
    print("")
    url = host + '/api/auth_for_camera/' + str(id_user)
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
            print('Успешно распарсен JSON ответ:')
            print(json.dumps(json_data, indent=4, ensure_ascii=False))
            if(json_data["token"] != "-1"):
                token = json_data["token"]
                return
            
        except json.decoder.JSONDecodeError:
            print(f'Ошибка декодирования JSON. Ответ сервера: {response.text}')
            
    except Exception as e:
        print(f'Непредвиденная ошибка324: {e}')
    print(token)


def show_image(base64_data):
    global root, tk_image

    # Декодируем Base64 в бинарные данные
    image_data = base64.b64decode(base64_data)

    # Создаем изображение из бинарных данных
    image = Image.open(io.BytesIO(image_data))

    # Получаем размеры экрана
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()

    # Масштабируем изображение под размер экрана
    image = image.resize((screen_width, screen_height), Image.Resampling.LANCZOS)

    # Преобразуем изображение в формат, подходящий для Tkinter
    tk_image = ImageTk.PhotoImage(image)

    # Создаем метку с изображением и размещаем ее в окне
    label = tk.Label(root, image=tk_image)
    label.pack(fill="both", expand=True)

    

def close_image_window():
    global root
    if root:
        root.destroy()  # Закрываем окно
        root = None

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

def main():
    i = 0
    global id_user
    global token
    while(i < 300):
        
        url = host + '/api/get_info_about_camera/' + str(id_camera)

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
                if(json_data["id_user"] != "-1"):
                    id_user = json_data["id_user"]
                    print("????")
                    if root:
                        root.after(0, close_image_window) 
                    print("!!!")
                    print(json_data["id_user"])
                    auth_cam()
                    #python_file = "path/to/your_script.py"

                    # Запуск Python-файла
                    record_video(camera_type, f"output{counter}.mp4")
                    
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
                      "weight_done": 90,
                      "count_done": 40,
                    }
                    
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
                        token = ""
                        break
                    except requests.exceptions.HTTPError as http_err:
                        print(f"HTTP error occurred: {http_err}")
                    except Exception as err:
                        print(f"An error occurred: {err}")
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

        

root = tk.Tk()
root.title("Изображение")

# Запускаем отображение изображения в главном потоке
show_image(getQR())

# Запускаем основной код в отдельном потоке
main_thread = threading.Thread(target=main)
main_thread.start()
init_system("rasberry", 3)
# Запускаем главный цикл Tkinter
root.mainloop()
stop_system()
# Ожидание завершения потока с основным кодом
main_thread.join()







