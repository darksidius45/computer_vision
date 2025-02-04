import numpy as np

pixel_video = r"C:\Users\prive\Desktop\prog\computer_vision\test_videos\PXL_20250203_111501037.mp4"
vivo_video = (
    r"C:\Users\prive\Desktop\prog\computer_vision\test_videos\video_20250203_141227.mp4"
)


# HSV диапазоны для pixel
pixel_lower_hsv = np.array([70, 90, 100])
pixel_upper_hsv = np.array([85, 170, 180])

# HSV диапазоны для vivo
vivo_lower_hsv = np.array([60, 30, 120])
vivo_upper_hsv = np.array([75, 150, 200])
