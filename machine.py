import cv2
import numpy as np


def machine_trajectory(frame, current_centers, trajectories, next_id, max_distance):
    if current_centers:
        if not trajectories:
            # Initialize new trajectories with KCF trackers for each center
            for center in current_centers:
                tracker = cv2.TrackerKCF_create()
                # Create bounding box around center point
                x, y = center
                bbox = (x-20, y-20, 40, 40) # 40x40 box centered on point
                tracker.init(frame, bbox)
                
                trajectories[next_id] = {
                    'points': [center],
                    'tracker': tracker
                }
                next_id += 1
        else:
            # Update existing trajectories using KCF trackers
            matched_centers = set()
            matched_trajectories = set()

            for track_id, track_data in trajectories.items():
                if not track_data['points']:
                    continue
                    
                # Update tracker
                success, bbox = track_data['tracker'].update(frame)
                if success:
                    # Get center point from bbox
                    x = int(bbox[0] + bbox[2]/2)
                    y = int(bbox[1] + bbox[3]/2) 
                    new_center = (x, y)
                    
                    # Find closest detected center to tracked point
                    min_dist = float("inf")
                    closest_center = None

                    for center in current_centers:
                        if center in matched_centers:
                            continue
                        dist = np.sqrt(
                            (center[0] - new_center[0]) ** 2 
                            + (center[1] - new_center[1]) ** 2
                        )
                        if dist < min_dist and dist < max_distance:
                            min_dist = dist
                            closest_center = center

                    if closest_center:
                        # Update trajectory with detected center
                        trajectories[track_id]['points'].append(closest_center)
                        # Reinitialize tracker at new position
                        x, y = closest_center
                        bbox = (x-20, y-20, 40, 40)
                        track_data['tracker'] = cv2.TrackerKCF_create()
                        track_data['tracker'].init(frame, bbox)
                        matched_centers.add(closest_center)
                        matched_trajectories.add(track_id)
                    else:
                        # Use tracker prediction if no matching detection
                        trajectories[track_id]['points'].append(new_center)

            # Create new trajectories for unmatched centers
            for center in current_centers:
                if center not in matched_centers:
                    tracker = cv2.TrackerKCF_create()
                    x, y = center
                    bbox = (x-20, y-20, 40, 40)
                    tracker.init(frame, bbox)
                    
                    trajectories[next_id] = {
                        'points': [center],
                        'tracker': tracker
                    }
                    next_id += 1

            # Remove old trajectories
            trajectories = {k: v for k, v in trajectories.items() if len(v['points']) > 0}

    # Draw trajectories
    colors = [
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (255, 0, 255),
    ]  # Different colors for different trajectories
    for track_id, track_data in trajectories.items():
        points = track_data['points']
        if len(points) > 1:
            color = colors[track_id % len(colors)]
            for i in range(1, len(points)):
                cv2.line(frame, points[i - 1], points[i], color, 2)

        # Limit trajectory length
        if len(points) > 50:
            trajectories[track_id]['points'] = points[-50:]
