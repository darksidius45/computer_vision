import numpy as np


# Function to return meanings for given camera type
def get_camera_settings(camera_type):
    settings = {
        "vivo": {
            "lower_hsv_machine": np.array([60, 30, 120]),
            "upper_hsv_machine": np.array([75, 150, 200]),
            "lower_hsv_weight1": np.array([0, 50, 50]),
            "upper_hsv_weight1": np.array([10, 255, 255]),
            "lower_hsv_weight2": np.array([170, 50, 50]),
            "upper_hsv_weight2": np.array([180, 255, 255]),
            "roi_x_machine": 1117,
            "roi_y_machine": 258,
            "roi_width_machine": 785,
            "roi_height_machine": 713,
            "roi_x_weight": 310,
            "roi_y_weight": 437,
            "roi_width_weight": 475,
            "roi_height_weight": 523,
            "video": r"test_videos\vivo_not_stable.mp4",
            "start_time": 3000,
        },
        "pixel_not_stable": {
            "lower_hsv_machine": np.array([70, 90, 100]),
            "upper_hsv_machine": np.array([85, 170, 180]),
            "lower_hsv_weight1": np.array([170, 50, 50]),
            "upper_hsv_weight1": np.array([180, 255, 255]),
            "lower_hsv_weight2": np.array([0, 66, 44]),
            "upper_hsv_weight2": np.array([4, 255, 255]),
            "roi_x_machine": 1377,
            "roi_y_machine": 19,
            "roi_width_machine": 533,
            "roi_height_machine": 987,
            "roi_x_weight": 460,
            "roi_y_weight": 200,
            "roi_width_weight": 341,
            "roi_height_weight": 520,
            "video": r"test_videos\pixel_not_stable.mp4",
            "start_time": 3000,
        },
        "pixel_stable": {
            "lower_hsv_machine": np.array([170, 100, 100]),
            "upper_hsv_machine": np.array([180, 255, 255]),
            "lower_hsv_weight1": np.array([170, 100, 100]),
            "upper_hsv_weight1": np.array([180, 255, 255]),
            "lower_hsv_weight2": np.array([0, 100, 100]),
            "upper_hsv_weight2": np.array([4, 255, 255]),
            "roi_x_machine": 1172,
            "roi_y_machine": 74,
            "roi_width_machine": 713,
            "roi_height_machine": 940,
            "roi_x_weight": 58,
            "roi_y_weight": 2,
            "roi_width_weight": 657,
            "roi_height_weight": 1007,
            "video": r"test_videos\pixel_stable.mp4",
            "start_time": 0,
        },
        "rasberry": {
            "lower_hsv_machine": np.array([170, 124, 56]),
            "upper_hsv_machine": np.array([180, 255, 118]),

            "lower_hsv_weight1": np.array([170, 124, 56]),
            "upper_hsv_weight1": np.array([180, 255, 118]),
            "lower_hsv_weight2": np.array([170, 124, 56]),
            "upper_hsv_weight2": np.array([180, 255, 118]),

            "roi_x_machine": 1100,
            "roi_y_machine": 0,
            "roi_width_machine": 750,
            "roi_height_machine": 1100,

            "roi_x_weight": 49,
            "roi_y_weight": 5,
            "roi_width_weight": 597,
            "roi_height_weight": 1094,

            "roi_x_movement": 1194,
            "roi_y_movement": 958,
            "roi_width_movement": 348,
            "roi_height_movement": 116,

            "max_hight": 88,
            "min_hight": 1000,
            "set_timer": 20,
            "rep_dist": 200,
            "stop_timer": 8,

        },
        
        "rasberry2": {
            "lower_hsv_machine": np.array([118, 0, 20]),
            "upper_hsv_machine": np.array([180, 255, 118]),

            "lower_hsv_weight1": np.array([119, 0, 20]),
            "upper_hsv_weight1": np.array([180, 255, 255]),
            "lower_hsv_weight2": np.array([0, 124, 56]),
            "upper_hsv_weight2": np.array([20, 255, 255]),

            "roi_x_machine": 1100,
            "roi_y_machine": 0,
            "roi_width_machine": 750,
            "roi_height_machine": 1100,

            "roi_x_weight": 49,
            "roi_y_weight": 0,
            "roi_width_weight": 650,
            "roi_height_weight": 1094,

            "roi_x_movement": 1194,
            "roi_y_movement": 950,
            "roi_width_movement": 348,
            "roi_height_movement": 116,

            "max_hight": 88,
            "min_hight": 1000,
            "set_timer": 20,
            "rep_dist": 100,
            "stop_timer": 8,

        },
    }
    return settings.get(camera_type, "Camera type not found")
