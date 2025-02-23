import cv2
import numpy as np
import time


def machine_trajectory(
    frame,
    current_centers,
    trajectories,
    min_hight,
    max_hight,
    MIN_VERTICAL_DISTANCE,
    REST_TIME_SET,
    tracker,
    tracked,
):
    # Статические переменные для подсчета
    if not hasattr(machine_trajectory, "reps"):
        machine_trajectory.reps = 0
        machine_trajectory.sets = 1
        machine_trajectory.last_rep_time = REST_TIME_SET
        machine_trajectory.prev_y = None
        machine_trajectory.moving_up = False
        machine_trajectory.lowest_point = min_hight
        machine_trajectory.highest_point = min_hight

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
        x = int(bbox[0] + bbox[2] / 2)
        y = int(bbox[1] + bbox[3] / 2)
        new_center = (x, y)
        trajectories.append(new_center)
        cv2.rectangle(frame, p1, p2, (255, 0, 0), 2, 1)

        # Подсчет повторений
        if machine_trajectory.prev_y is not None:
            # Calculate vertical movement
            vertical_movement = machine_trajectory.prev_y - y

            # Define a threshold for minimum movement to avoid noise
            MOVEMENT_THRESHOLD = 5

            if abs(vertical_movement) > MOVEMENT_THRESHOLD:
                if vertical_movement > 0:
                    # Moving up
                    if not machine_trajectory.moving_up:
                        machine_trajectory.moving_up = True
                        machine_trajectory.lowest_point = y
                        vertical_distance = abs(
                            machine_trajectory.highest_point
                            - machine_trajectory.lowest_point
                        )
                        if vertical_distance > MIN_VERTICAL_DISTANCE:
                            machine_trajectory.reps += 1

                    cv2.putText(
                        frame,
                        "Moving Up",
                        (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 255, 0),
                        2,
                    )
                else:
                    # Moving down
                    if machine_trajectory.moving_up:
                        machine_trajectory.moving_up = False
                        machine_trajectory.highest_point = y
                        vertical_distance = abs(
                            machine_trajectory.highest_point
                            - machine_trajectory.lowest_point
                        )
                        if vertical_distance > MIN_VERTICAL_DISTANCE:
                            machine_trajectory.reps += 1

                    cv2.putText(
                        frame,
                        "Moving Down",
                        (50, 150),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (0, 0, 255),
                        2,
                    )
            else:
                # Staying relatively still
                cv2.putText(
                    frame,
                    "Stationary",
                    (50, 150),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (255, 255, 255),
                    2,
                )

        machine_trajectory.prev_y = y
        tracked = True
    else:
        cv2.putText(
            frame,
            "Tracking failure detected",
            (100, 80),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            (0, 0, 255),
            2,
        )
        tracked = False
        print("Tracking failure detected")

    # Отображение информации о подходах и повторениях
    cv2.putText(
        frame,
        f"Set: {machine_trajectory.sets}",
        (50, 50),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )
    cv2.putText(
        frame,
        f"Reps: {machine_trajectory.reps // 2}",
        (50, 100),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (255, 255, 255),
        2,
    )

    # Отрисовка траектории
    if len(trajectories) > 1:
        for i in range(1, len(trajectories)):
            pt1 = tuple(map(int, trajectories[i - 1]))
            pt2 = tuple(map(int, trajectories[i]))
            cv2.line(frame, pt1, pt2, (0, 0, 255), 2)

    # Ограничение длины траектории
    if len(trajectories) > 50:
        trajectories = trajectories[-50:]

    return tracked
