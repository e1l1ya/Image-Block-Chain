import cv2 # Pardazesh tasvir
import os # Ertebat ba system
import time # Vaghfe ijad kardan
import argparse # fahmidan arguman
import urllib.parse # fahmidan address dorbin
from datetime import datetime # sakht aks ba zaman
from Lib.Installer import Installer
from Lib.Database import Database
from Lib.ImageBlock import ImageBlock

def capture_camera(url, previous_hash):
    imagesFolder = "Frame/"
    cap = cv2.VideoCapture(url)

    if not cap.isOpened():
        print("Error: Unable to open camera.")
        exit()

    ret, frame = cap.read()

    if ret:

        filename = "image_" + str(datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%p")) + ".jpg"
        full_path = imagesFolder + "/" + filename
        cv2.imwrite(full_path, frame)

        with open(full_path, "rb") as file:
            file_data = file.read()

        new_block = ImageBlock(file_data, previous_hash)
        print("Image captured and hashed:", new_block.hash)

        db = Database()
        db.insert(filename, previous_hash, new_block.hash)
    else:
        print("Error: Unable to capture frame.")
        exit()

    cap.release()
    return new_block


if __name__ == "__main__":
    current_script_directory = os.path.dirname(os.path.abspath(__file__))
    directory_path = current_script_directory + '/Frame/'
    db = Database()

    if not os.path.exists(directory_path):
        inst = Installer()
        inst.exec()
        previous_hash = "Abolfazl"  # Initial hash for the first block
        print("Avalin bar ast ke ejra mishavad")
    else:
        previous_hash = db.get_last_hash()
        print("Edame dafe ghabl")

    parser = argparse.ArgumentParser(description="Capture frames from an RTSP camera and create a simple image blockchain.")
    parser.add_argument("--url", required=True, help="RTSP URL of the camera")
    parser.add_argument("--port", required=True, help="Port number of the camera")
    parser.add_argument("--username", help="Username for RTSP authentication")
    parser.add_argument("--password", help="Password for RTSP authentication")
    parser.add_argument("--path", help="path for RTSP authentication")

    args = parser.parse_args()

    if args.username and args.password:
        encoded_username = urllib.parse.quote(args.username)
        encoded_password = urllib.parse.quote(args.password)
        full_url = f"rtsp://{encoded_username}:{encoded_password}@{args.url}:{args.port}{args.path}"
    else:
        full_url = f"rtsp://{args.url}:{args.port}{args.path}"

    new_block = capture_camera(full_url, previous_hash)

    while True:
        try:
            time.sleep(3)  # Pause for 3 seconds
            previous_hash = new_block.hash
            new_block = capture_camera(full_url, previous_hash)

        except KeyboardInterrupt:
            os.system("cls")
            all_data = db.select_all()
            for row in all_data:
                print(row)
            exit()