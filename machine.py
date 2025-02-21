import cv2
import numpy as np


def machine_trajectory(frame, current_centers, trajectories, next_id, max_distance, tracker, tracked):
    if not tracked:
        if current_centers:
         for center in current_centers:
            x = center[0] - 50  # 50 is half of 100 to center the box
            y = center[1] - 50
            bbox = (x, y, 100, 100)  # x, y, width, height
            tracker.init(frame, bbox)
            tracked = True

    ok, bbox = tracker.update(frame)           
    if ok:
        p1 = (int(bbox[0]), int(bbox[1]))
        p2 = (int(bbox[0] + bbox[2]), int(bbox[1] + bbox[3]))
        x = int(bbox[0] + bbox[2]/2)
        y = int(bbox[1] + bbox[3]/2) 
        new_center = (x, y)
        trajectories.append(new_center)
        cv2.rectangle(frame, p1, p2, (255,0,0), 2, 1)
        tracked = True
    else:
        cv2.putText(frame, "Tracking failure detected", (100,80), cv2.FONT_HERSHEY_SIMPLEX, 0.75,(0,0,255),2)
        tracked = False
        print("Tracking failure detected")

    colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
    ]  # Different colors for different trajectories

    # Draw trajectory lines
    if len(trajectories) > 1:
        color = colors[2]
        for i in range(1, len(trajectories)):
            pt1 = tuple(map(int, trajectories[i-1]))
            pt2 = tuple(map(int, trajectories[i]))
            cv2.line(frame, pt1, pt2, color, 2)

    # Limit trajectory length
    if len(trajectories) > 50:
        trajectories = trajectories[-50:]

    return tracked
