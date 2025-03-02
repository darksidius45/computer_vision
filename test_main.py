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
