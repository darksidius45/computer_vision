import cv2
import numpy as np
import time


from config import get_camera_settings
from machine import machine_trajectory
from weights import weights_detection





def video_handling(video_path, camera_type="rasberry2"):
    """
    Process video for exercise tracking and weight detection

    Parameters:
        video_path (str): Path to the video file
        camera_type (str): Type of camera to load appropriate settings

    Returns:
        dict: Dictionary containing exercise data
    """
    # load settings based on camera_type
    camera_settings = get_camera_settings(camera_type)

    # Ñ†Ð²ÐµÑ‚Ð¾Ð²Ñ‹Ðµ Ð´Ð¸Ð°Ð¿Ð°Ð·Ð¾Ð½Ñ‹ Ð´Ð»Ñ Ð¼ÐµÑ‚ÐºÐ¸ Ð½Ð° Ñ‚Ñ€ÐµÐ½Ð°Ð¶ÐµÑ€Ðµ
    lower_hsv_machine = camera_settings["lower_hsv_machine"]
    upper_hsv_machine = camera_settings["upper_hsv_machine"]

    # Ñ†Ð²ÐµÑ‚Ð¾Ð²Ñ‹Ðµ Ð´Ð¸Ð°Ð¿Ð°Ð·Ð¾Ð½Ñ‹ Ð´Ð»Ñ Ð¼ÐµÑ‚Ð¾Ðº Ð²ÐµÑÐ¾Ð²
    lower_hsv_weight1 = camera_settings["lower_hsv_weight1"]
    upper_hsv_weight1 = camera_settings["upper_hsv_weight1"]
    lower_hsv_weight2 = camera_settings["lower_hsv_weight2"]
    upper_hsv_weight2 = camera_settings["upper_hsv_weight2"]

    # Ð´Ð¸Ð°Ð¿Ð°Ð·Ð¾Ð½ Ð´Ð»Ñ Ð¼ÐµÑ‚ÐºÐ¸ Ð½Ð° Ñ‚Ñ€ÐµÐ½Ð°Ð¶Ñ‘Ñ€Ðµ
    roi_x_machine = camera_settings["roi_x_machine"]
    roi_y_machine = camera_settings["roi_y_machine"]
    roi_width_machine = camera_settings["roi_width_machine"]
    roi_height_machine = camera_settings["roi_height_machine"]

    # Ð´Ð¸Ð°Ð¿Ð°Ð·Ð¾Ð½ Ð´Ð»Ñ Ð¼ÐµÑ‚Ð¾Ðº Ð½Ð° Ð²ÐµÑÐ°Ñ…
    roi_x_weight = camera_settings["roi_x_weight"]
    roi_y_weight = camera_settings["roi_y_weight"]
    roi_width_weight = camera_settings["roi_width_weight"]
    roi_height_weight = camera_settings["roi_height_weight"]

    # Ð½Ð°ÑÑ‚Ñ€Ð¾Ð¹ÐºÐ¸ Ð¿Ð¾Ð´ Ñ‚Ñ€ÐµÐ½Ð°Ð¶Ñ‘Ñ€

    max_hight = camera_settings["max_hight"]
    min_hight = camera_settings["min_hight"]
    set_timer = camera_settings["set_timer"]
    rep_dist = camera_settings["rep_dist"]

    # Ð—Ð°Ð³Ñ€ÑƒÐ·ÐºÐ°
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, 1000)  # Ð²ÐºÐ»ÑŽÑ‡Ð°ÐµÐ¼ Ð²Ð¸Ð´ÐµÐ¾ Ñ Ð¾Ð¿Ñ€ÐµÐ´ÐµÐ»Ñ‘Ð½Ð½Ð¾Ð¹ ÑÐµÐºÑƒÐ½Ð´Ñ‹

    if not cap.isOpened():
        print("Error: Could not open video.")
        return None

    # Create custom parameters for the CSRT tracker
    params = cv2.TrackerCSRT_Params()
    params.padding = 3.0
    params.template_size = 200
    params.gsl_sigma = 1.0
    params.hog_orientations = 5
    params.num_hog_channels_used = 5
    params.hog_clip = 0.2
    params.filter_lr = 0.02
    params.weights_lr = 0.02
    params.admm_iterations = 3
    params.number_of_scales = 100
    params.scale_sigma_factor = 0.25
    params.scale_model_max_area = 300
    params.scale_lr = 0.05
    params.scale_step = 1.02
    params.histogram_bins = 16
    params.background_ratio = 4
    params.histogram_lr = 0.04

    # Create tracker with custom parameters
    tracker = cv2.TrackerCSRT_create(params)

    tracked = False
    trajectories = []  # Ð¡Ð»Ð¾Ð²Ð°Ñ€ÑŒ Ð´Ð»Ñ Ñ…Ñ€Ð°Ð½ÐµÐ½Ð¸Ñ Ñ‚Ñ€Ð°ÐµÐºÑ‚Ð¾Ñ€Ð¸Ð¹ {id: points}
    next_id = 0  # Ð¡Ñ‡ÐµÑ‚Ñ‡Ð¸Ðº Ð´Ð»Ñ Ð½Ð°Ð·Ð½Ð°Ñ‡ÐµÐ½Ð¸Ñ ID Ð¾Ð±ÑŠÐµÐºÑ‚Ð°Ð¼
    max_distance = 120
    ob_info = {}  # ÐœÐ°ÐºÑÐ¸Ð¼Ð°Ð»ÑŒÐ½Ð¾Ðµ Ñ€Ð°ÑÑÑ‚Ð¾ÑÐ½Ð¸Ðµ Ð´Ð»Ñ ÑÐ²ÑÐ·Ñ‹Ð²Ð°Ð½Ð¸Ñ Ñ‚Ð¾Ñ‡ÐµÐº
    exercises = {"1": []}

    start_time = time.time()
    prev_frame_time = start_time

    while True:
        print("testic")
        ret, frame = cap.read()
        if not ret:
            break

        elapsed_time = time.time() - start_time

        # Extract ROI from frame
        roi = frame[
            roi_y_machine : roi_y_machine + roi_height_machine,
            roi_x_machine : roi_x_machine + roi_width_machine,
        ]

        roi_weight = frame[
            roi_y_weight : roi_y_weight + roi_height_weight,
            roi_x_weight : roi_x_weight + roi_width_weight,
        ]
        # ÐšÐ¾Ð½Ð²ÐµÑ€Ñ‚Ð¸Ñ€ÑƒÐµÐ¼ ROI Ð² HSV

        hsv_frame_machine = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        hsv_frame_weight = cv2.cvtColor(roi_weight, cv2.COLOR_BGR2HSV)

        # Ð¼Ð°ÑÐºÐ¸ Ð´Ð»Ñ Ð´Ð¸Ð°Ð¿Ð°Ð·Ð¾Ð½Ð° Ñ†Ð²ÐµÑ‚Ð¾Ð² Ð² HSV
        mask_machine = cv2.inRange(
            hsv_frame_machine, lower_hsv_machine, upper_hsv_machine
        )

        # ÑÐ¾Ð·Ð´Ð°ÐµÐ¼ 2 Ð¼Ð°ÑÐºÐ¸ Ð´Ð»Ñ ÐºÑ€Ð°ÑÐ½Ð¾Ð³Ð¾ Ñ†Ð²ÐµÑ‚Ð° Ð² Ñ€Ð°Ð·Ð½Ñ‹Ñ… Ð´Ð¸Ð°Ð¿Ð°Ð·Ð¾Ð½Ð°Ñ… Ð¸Ð·-Ð·Ð° Ð¾ÑÐ¾Ð±ÐµÐ½Ð½Ð¾ÑÑ‚ÐµÐ¹ hsv Ñ„Ð¾Ñ€Ð¼Ð°Ñ‚Ð° Ð¿Ð¾Ñ‚Ð¾Ð¼ Ð¾Ð±ÑŠÐµÐ´Ð¸Ð½ÑÐµÐ¼ Ð¸Ñ… Ð² 1
        mask_weight1 = cv2.inRange(
            hsv_frame_weight, lower_hsv_weight1, upper_hsv_weight1
        )
        mask_weight2 = cv2.inRange(hsv_frame_weight, lower_hsv_weight2, upper_hsv_weight2)
        mask_weight = cv2.bitwise_or(mask_weight1, mask_weight2)

        # ÑƒÐ¼ÐµÐ½ÑŒÑˆÐµÐ½Ð¸Ñ ÑˆÑƒÐ¼Ð°
        kernel = np.ones((5, 5), np.uint8)
        mask_machine = cv2.erode(mask_machine, kernel, iterations=1)
        mask_machine = cv2.dilate(mask_machine, kernel, iterations=2)
        mask_weight = cv2.erode(mask_weight, kernel, iterations=1)
        mask_weight = cv2.dilate(mask_weight, kernel, iterations=2)

        current_centers = []

        # ÐšÐžÐÐ¢Ð£Ð Ð«Ð«Ð«Ð«Ð«Ð«Ð«Ð«
        contours_machine, _ = cv2.findContours(
            mask_machine, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        contours_weight, _ = cv2.findContours(
            mask_weight, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # ÐžÑ‚Ñ€Ð¸ÑÐ¾Ð²Ñ‹Ð²Ð°ÐµÐ¼ ROI
        cv2.rectangle(
            frame,
            (roi_x_machine, roi_y_machine),
            (roi_x_machine + roi_width_machine, roi_y_machine + roi_height_machine),
            (255, 255, 255),
            2,
        )
        cv2.rectangle(
            frame,
            (roi_x_weight, roi_y_weight),
            (roi_x_weight + roi_width_weight, roi_y_weight + roi_height_weight),
            (255, 255, 255),
            2,
        )

        # Ð Ð¸ÑÑƒÐµÐ¼ ÐºÐ¾Ð½Ñ‚ÑƒÑ€Ñ‹ Ð¸ Ñ†ÐµÐ½Ñ‚Ñ€Ñ‹ Ð¾Ð±ÑŠÐµÐºÑ‚Ð¾Ð²
        for contour in contours_machine:
            # Ð˜Ð³Ð½Ð¾Ñ€ ÑˆÑƒÐ¼Ð°
            area = cv2.contourArea(contour)
            if area < 75:
                continue

            # Ð¿Ñ€ÑÐ¼Ð¾ÑƒÐ³Ð¾Ð»ÑŒÐ½Ð¸Ðº, Ð¾Ð¿Ð¸ÑÑ‹Ð²Ð°ÑŽÑ‰Ð¸Ð¹ ÐºÐ¾Ð½Ñ‚ÑƒÑ€
            (x, y, w, h) = cv2.boundingRect(contour)

            aspect_ratio = float(w) / h
            if aspect_ratio < 0.2 or aspect_ratio > 5:
                continue

            # Convert coordinates
            abs_x = x + roi_x_machine
            abs_y = y + roi_y_machine

            # Ð’Ñ‹Ñ‡Ð¸ÑÐ»ÑÐµÐ¼ Ñ†ÐµÐ½Ñ‚Ñ€ Ð¾Ð±ÑŠÐµÐºÑ‚Ð°
            center = ((abs_x + w // 2), (abs_y + h // 2))
            current_centers.append(center)

            # Ð Ð¸ÑÑƒÐµÐ¼ Ð¿Ñ€ÑÐ¼Ð¾ÑƒÐ³Ð¾Ð»ÑŒÐ½Ð¸Ðº Ð²Ð¾ÐºÑ€ÑƒÐ³ Ð¾Ð±ÑŠÐµÐºÑ‚Ð°
            cv2.circle(frame, center, 5, (0, 255, 0), -1)

            current_centers.append(center)
            # Ð’Ñ‹Ð²Ð¾Ð´Ð¸Ð¼ ÐºÐ¾Ð¾Ñ€Ð´Ð¸Ð½Ð°Ñ‚Ñ‹ Ñ†ÐµÐ½Ñ‚Ñ€Ð°
            cv2.putText(
                frame,
                f"({center[0]}, {center[1]})",
                (abs_x, abs_y - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2,
            )

        weight_markers_count = 0
        data = []

        # Store centers from previous frame if not already defined
        if not hasattr(cv2, "prev_weight_centers"):
            cv2.prev_weight_centers = []

        # Get current centers
        current_weight_centers = []
        updated_objects = {}

        for contour in contours_weight:
            # Ð˜Ð³Ð½Ð¾Ñ€ ÑˆÑƒÐ¼Ð°
            area = cv2.contourArea(contour)
            if area < 150:
                continue

            # ÐŸÐ¾Ð»ÑƒÑ‡Ð°ÐµÐ¼ Ð¿Ñ€ÑÐ¼Ð¾ÑƒÐ³Ð¾Ð»ÑŒÐ½Ð¸Ðº, Ð¾Ð¿Ð¸ÑÑ‹Ð²Ð°ÑŽÑ‰Ð¸Ð¹ ÐºÐ¾Ð½Ñ‚ÑƒÑ€
            (x, y, w, h) = cv2.boundingRect(contour)

            # ÐŸÑ€Ð¾Ð²ÐµÑ€ÑÐµÐ¼ ÑÐ¾Ð¾Ñ‚Ð½Ð¾ÑˆÐµÐ½Ð¸Ðµ ÑÑ‚Ð¾Ñ€Ð¾Ð½ Ð¸ Ð¿Ð»Ð¾Ñ‰Ð°Ð´ÑŒ Ð´Ð»Ñ Ñ„Ð¸Ð»ÑŒÑ‚Ñ€Ð°Ñ†Ð¸Ð¸ Ð»Ð¾Ð¶Ð½Ñ‹Ñ… ÑÑ€Ð°Ð±Ð°Ñ‚Ñ‹Ð²Ð°Ð½Ð¸Ð¹
            aspect_ratio = float(w) / h
            if aspect_ratio < 3.0:
                continue

            # Convert coordinates to original frame coordinates
            abs_x = x + roi_x_weight
            abs_y = y + roi_y_weight

            # Ð’Ñ‹Ñ‡Ð¸ÑÐ»ÑÐµÐ¼ Ñ†ÐµÐ½Ñ‚Ñ€ Ð¾Ð±ÑŠÐµÐºÑ‚Ð°
            center = (abs_x + w // 2, abs_y + h // 2)

            # Ð”Ð¾Ð¿Ð¾Ð»Ð½Ð¸Ñ‚ÐµÐ»ÑŒÐ½Ð°Ñ Ð¿Ñ€Ð¾Ð²ÐµÑ€ÐºÐ° Ð½Ð° Ð¿Ð¾Ð»Ð¾Ð¶ÐµÐ½Ð¸Ðµ Ñ†ÐµÐ½Ñ‚Ñ€Ð°
            if (
                roi_x_weight <= center[0] <= roi_x_weight + roi_width_weight
                and roi_y_weight <= center[1] <= roi_y_weight + roi_height_weight
            ):
                current_weight_centers.append(center)

            cv2.rectangle(frame, (abs_x, abs_y), (abs_x + w, abs_y + h), (0, 255, 0), 2)
            cv2.circle(frame, center, 5, (0, 0, 255), -1)

        # Track objects across frames
        ob_info, next_id, weight = weights_detection(
            frame,
            current_weight_centers,
            ob_info,
            updated_objects,
            next_id,
            max_distance,
        )

        # Resize ROI for optimization
        roi = cv2.resize(roi, (roi.shape[1] // 2, roi.shape[0] // 2))
        # ÐžÐ±Ð½Ð¾Ð²Ð»ÑÐµÐ¼ Ñ‚Ñ€Ð°ÐµÐºÑ‚Ð¾Ñ€Ð¸Ð¸
        tracked, exercises = machine_trajectory(
            roi,
            current_centers,
            trajectories,
            min_hight,
            max_hight,
            rep_dist,
            set_timer,
            tracker,
            tracked,
            exercises,
            frame,
            weight,
        )
        
        screen_height = 720
        screen_width = 1280
        # # Calculate frame size to fit screen while maintaining aspect ratio
        frame_height = int(screen_height * 0.8)  # Use 80% of screen height
        frame_width = int(frame.shape[1] * frame_height / frame.shape[0])

        # # Ensure frame width doesn't exceed screen width
        if frame_width > screen_width * 0.8:
            frame_width = int(screen_width * 0.8)
            frame_height = int(frame.shape[0] * frame_width / frame.shape[1])

        # # Resize frame only
        frame_resized = cv2.resize(frame, (frame_width, frame_height))

        # # Resize masks to half size
        mask_machine_resized = cv2.resize(
           mask_machine, (mask_machine.shape[1] // 2, mask_machine.shape[0] // 2)
        )

        mask_weight_resized = cv2.resize(
            mask_weight, (mask_weight.shape[1] // 2, mask_weight.shape[0] // 2)
            )

        # # Calculate FPS
        new_frame_time = time.time()
        fps = 1 / (new_frame_time - prev_frame_time)
        prev_frame_time = new_frame_time

        #Display FPS on frame
        cv2.putText(
            frame_resized,
            f"FPS: {int(fps)}",
            (10, 400),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 0, 0),
            2,
            cv2.LINE_AA,
        )

        # Show windows
        cv2.imshow("Frame", frame_resized)
        #cv2.imshow("Mask_machine", mask_machine_resized)
        cv2.imshow("Mask_weight", mask_weight_resized)

        # # Position windows
        cv2.moveWindow("Frame", 0, 0)
        # cv2.moveWindow("Mask_machine", frame_width + 10, 0)
        #cv2.moveWindow(
            #"Mask_weight", frame_width + mask_machine_resized.shape[1] + 20, 0
        #)

        # Ð’Ñ‹Ñ…Ð¾Ð´ Ð¿Ð¾ Ð½Ð°Ð¶Ð°Ñ‚Ð¸ÑŽ ÐºÐ»Ð°Ð²Ð¸ÑˆÐ¸ q
        if cv2.waitKey(30) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    print(exercises)
    return exercises


print("start")
video_handling(r"/home/mercury/computer_vision1/131_0.mp4", "rasberry2")
    
