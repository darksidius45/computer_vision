import cv2
import numpy as np


def weights_detection(
    frame,
    current_weight_centers,
    ob_info,
    updated_objects,
    next_object_id,
    max_distance,
):
    for obj_id, prev_center in ob_info.items():
        # Находим ближайший центр в текущем кадре
        min_distance = float("inf")
        closest_center = None

        for center in current_weight_centers:
            distance = np.linalg.norm(np.array(prev_center[0]) - np.array(center))
            if distance < min_distance:
                min_distance = distance
                closest_center = center

        if closest_center is not None and min_distance < max_distance:
            if min_distance < 10:
                updated_objects[obj_id] = [
                    closest_center,
                    prev_center[1] + 1,
                    prev_center[2] + 1,
                ]
            else:
                updated_objects[obj_id] = [closest_center, prev_center[1] + 1, 0]
            current_weight_centers.remove(closest_center)

        else:

            # Если объект не обнаружен в течение 5 кадров, удаляем его
            if prev_center[1] < 5:
                updated_objects[obj_id] = [prev_center[0], 0, 0]

    # Add new objects only if they persist for a few frames
    if len(ob_info) == 0:
        next_object_id = 0
    else:
        # Очищаем неактивные ID перед добавлением новых
        active_ids = [
            object_id
            for object_id, object_info in updated_objects.items()
            if object_info[1] > 0
        ]

        # Set next ID to be one more than highest active ID, or 0 if no active objects
        next_object_id = max(active_ids) + 1 if active_ids else 0

    # Добавляем новые объекты только если есть свободное место (максимум 10 объектов)
    for center in current_weight_centers:
        if len(updated_objects) < 10:
            updated_objects[next_object_id] = [center, 0, 0]
            next_object_id += 1

    ob_info = updated_objects

    num_of_stable_weight_markers = sum(
        1 for _, center in ob_info.items() if center[2] > 6
    )

    for obj_id, center in ob_info.items():
        cv2.putText(
            frame,
            f"ID: {obj_id}",
            (center[0][0] - 20, center[0][1] - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 0),
            2,
        )

    not_in = 0
    for obj_id, center in ob_info.items():
        if center[1] > 3:
            not_in += 1

    # Display the average count of moving red markers on the frame
    cv2.putText(
        frame,
        f"Moving weight: {(len(ob_info) - num_of_stable_weight_markers) * 5}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 0, 255),
        2,
    )
    return ob_info, next_object_id, (len(ob_info) - num_of_stable_weight_markers) * 5
