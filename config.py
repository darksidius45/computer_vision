import numpy as np



# Function to return meanings for given camera type
def get_camera_settings(camera_type):
    settings = {
        "vivo": {
            "lower_hsv_green": np.array([60, 30, 120]),
            "upper_hsv_green": np.array([75, 150, 200]),
            "lower_hsv_red": np.array([0, 50, 50]),
            "upper_hsv_red": np.array([10, 255, 255]),
            "roi_x_green": 1117,
            "roi_y_green": 258,
            "roi_width_green": 785,
            "roi_height_green": 713,
            "roi_x_red": 320,
            "roi_y_red": 437,
            "roi_width_red": 475,
            "roi_height_red": 523,
            "video": r"C:\Users\prive\Desktop\prog\computer_vision\test_videos\video_20250203_141227.mp4"
        },
        "pixel": {
            "lower_hsv_green": np.array([70, 90, 100]),
            "upper_hsv_green": np.array([85, 170, 180]),
            "lower_hsv_red": np.array([170, 50, 50]),
            "upper_hsv_red": np.array([180, 255, 255]),
            "roi_x_green": 1068,
            "roi_y_green": 277,
            "roi_width_green": 400,
            "roi_height_green": 573,
            "roi_x_red": 460,
            "roi_y_red": 404,
            "roi_width_red": 341,
            "roi_height_red": 479,
            "video": r"C:\Users\prive\Desktop\prog\computer_vision\test_videos\PXL_20250203_111501037.mp4"
        },
    }
    return settings.get(camera_type, "Camera type not found")







