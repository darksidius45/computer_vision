import cv2
import numpy as np
import time

def machine_trajectory(frame, current_centers, trajectories, next_id, max_distance, tracker, tracked):
    # Константы для определения повторения и подхода
    MIN_VERTICAL_DISTANCE = 50  # Минимальное вертикальное расстояние для засчитывания повторения
    REST_TIME_THRESHOLD = 10  # Время отдыха в секундах для нового подхода
    
    # Статические переменные для подсчета
    if not hasattr(machine_trajectory, "reps"):
        machine_trajectory.reps = 0
        machine_trajectory.sets = 1
        machine_trajectory.last_rep_time = time.time()
        machine_trajectory.prev_y = None
        machine_trajectory.moving_up = False

    if not tracked:
        if current_centers:
            for center in current_centers:
                x = center[0] - 50
                y = center[1] - 50
                bbox = (x, y, 100, 100)
                tracker.init(frame, bbox)
                tracked = True
        else:
            return False

    ok, bbox = tracker.update(frame)           
    if ok:
        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
        x = int(bbox[0] + bbox[2]/2)
        y = int(bbox[1] + bbox[3]/2) 
        new_center = (x, y)
        trajectories.append(new_center)
        cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)
        
        # Подсчет повторений
        if machine_trajectory.prev_y is not None:
            if y < machine_trajectory.prev_y - MIN_VERTICAL_DISTANCE and not machine_trajectory.moving_up:
                machine_trajectory.moving_up = True
            elif y > machine_trajectory.prev_y + MIN_VERTICAL_DISTANCE and machine_trajectory.moving_up:
                machine_trajectory.moving_up = False
                machine_trajectory.reps += 1
                current_time = time.time()
                
                # Проверка на новый подход
                if current_time - machine_trajectory.last_rep_time > REST_TIME_THRESHOLD:
                    machine_trajectory.sets += 1
                    machine_trajectory.reps = 1
                
                machine_trajectory.last_rep_time = current_time
                
        machine_trajectory.prev_y = y
        tracked = True
    else:
        cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
        tracked = False
        print("Tracking failure detected")

    # Отображение информации о подходах и повторениях
    cv2.putText(frame, f"Set: {machine_trajectory.sets}", (50,50), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
    cv2.putText(frame, f"Reps: {machine_trajectory.reps}", (50,100), 
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)

    # Отрисовка траектории
    if len(trajectories) > 1:
        for i in range(1, len(trajectories)):
            pt1 = tuple(map(int, trajectories[i-1]))
            pt2 = tuple(map(int, trajectories[i]))
            cv2.line(frame, pt1, pt2, (0,0,255), 2)

    # Ограничение длины траектории
    if len(trajectories) > 50:
        trajectories = trajectories[-50:]

    return tracked
