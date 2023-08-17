from Lib.ImageBlock import ImageBlock
import argparse
from Lib.Database import Database

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Validate hash of image to check is image chenge or not")
    parser.add_argument("--img", required=True, help="Image file name")
    parser.add_argument("--last_hash", required=True, help="Last hash to validate")

    args = parser.parse_args()

    with open("Frame/" + args.img, "rb") as file:
        file_data = file.read()

    db = Database();
    res = db.valid_hash(args.img, ImageBlock(file_data, args.last_hash).hash)
    if res == True:
        print("its true")
    else:
        print("its false")
