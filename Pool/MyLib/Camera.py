import cv2
from datetime import datetime


class Camera:
    def __init__(self, url):
        self.url = url
        self.images_folder = "Images/"
        self.last_image = ""

    def capture_camera(self):
        cap = cv2.VideoCapture(self.url)

        if not cap.isOpened():
            print("Error: Unable to open camera.")
            exit()

        ret, frame = cap.read()

        if ret:
            filename = "image_" + str(datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%p")) + ".jpg"
            full_path = self.images_folder + "/" + filename
            cv2.imwrite(full_path, frame)
            self.last_image = filename

        return ret

    def get_last_image(self):
        return self.last_image
