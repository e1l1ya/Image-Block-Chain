from flask import Flask, request, jsonify, send_file
import zipfile
import os
import shutil
import sqlite3
import hashlib
from MyLib.ImageBlock import ImageBlock

app = Flask(__name__)
database_path = 'hashes.db'


# Check if Database not exists create it
if not os.path.exists(database_path):
    # If the database file doesn't exist, create it and the table
    try:
        connection = sqlite3.connect(database_path)
        cursor = connection.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS blockchain (
            id INTEGER PRIMARY KEY,
            name TEXT,
            prev_hash TEXT,
            hash TEXT
        )"""

        cursor.execute(create_table_query)
        connection.commit()

        print("Database and table created successfully!")

    except sqlite3.Error as e:
        print("Error creating database and table:", e)

    finally:
        if connection:
            connection.close()
else:
    print("Database already exists.")


def calculate_hash(file_path):
    hash_algorithm = hashlib.sha256()
    with open(file_path, "rb") as file:
        while chunk := file.read(8192):
            hash_algorithm.update(chunk)
    return hash_algorithm.digest()


def calculate_folder_hash(folder_path):
    folder_hash_algorithm = hashlib.sha256()

    for root, _, files in os.walk(folder_path):
        for file_name in files:
            file_path = os.path.join(root, file_name)
            file_hash = calculate_hash(file_path)
            folder_hash_algorithm.update(file_hash)

    return folder_hash_algorithm.hexdigest()


def clear_folder(folder_path):
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Error deleting {file_path}: {e}")


@app.route('/zip', methods=['POST', 'GET'])
def upload_and_unzip():
    if request.method == "GET":
        images_folder = 'Images'
        zip_filename = 'images.zip'
        if os.path.exists(zip_filename):
            os.remove(zip_filename)

        # Create a ZIP file containing all image files in the Images folder
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            for root, dirs, files in os.walk(images_folder):
                for file in files:
                    if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                        file_path = os.path.join(root, file)
                        zipf.write(file_path, os.path.relpath(file_path, images_folder))

        # Send the ZIP file as a response
        return send_file(zip_filename, as_attachment=True)

    elif request.method == 'POST':
        if 'zip_file' not in request.files:
            return jsonify({'message': 'No zip_file part in the request'}), 400

        zip_file = request.files['zip_file']

        if zip_file.filename == '':
            return jsonify({'message': 'No selected file'}), 400

        if zip_file:
            unzip_folder = os.path.join("Images/")
            os.makedirs(unzip_folder, exist_ok=True)

            clear_folder(unzip_folder)

            zip_file_path = os.path.join("Images/", zip_file.filename)
            zip_file.save(zip_file_path)

            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                zip_ref.extractall(unzip_folder)

            os.remove(zip_file_path)

            return jsonify({'message': 'File uploaded, extracted, and zip removed successfully'}), 200

    else:
        return ""


@app.route('/database', methods=['POST', 'GET'])
def upload_and_download_database():
    if request.method == "GET":
        return send_file(database_path,as_attachment=True)

    elif request.method == "POST":
        if 'database' not in request.files:
            return "Wrong"

        database_file = request.files['database']

        if database_file.filename == '':
            return "no name found"

        database_file.save(database_file.filename)

        return "done"


@app.route('/hash', methods=['GET'])
def hash():
    folder_path = "Images/"
    return calculate_folder_hash(folder_path)


@app.route('/')
def get_hashes():
    try:
        connection = sqlite3.connect('hashes.db')
        cursor = connection.cursor()

        select_query = "SELECT * FROM blockchain"
        cursor.execute(select_query)

        data = cursor.fetchall()
        columns = [column[0] for column in cursor.description]

        result = []
        for row in data:
            result.append(dict(zip(columns, row)))

        return jsonify(result), 200

    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500

    finally:
        if connection:
            connection.close()

@app.route('/upload_image', methods=['POST'])
def upload_image():
    image_file = request.files['image']  # Get the image file from the POST data

    if image_file:
        # Store the image in the 'Images' folder
        image_folder = "Images/"
        image_filename = image_file.filename
        image_path = os.path.join(image_folder, image_filename)

        # Save the image using shutil
        with open(image_path, 'wb') as f:
            shutil.copyfileobj(image_file, f)

        with open(image_path, "rb") as file:
            file_data = file.read()


        print(request.form['hash'])
        print("\n\n")
        print(ImageBlock(file_data, request.form['prev_hash']))
        print("\n\n")
        print(request.form['prev_hash'])
        if request.form['hash'] == ImageBlock(file_data, request.form['prev_hash']).hash:
            try:
                insert_query = "INSERT INTO blockchain (name, prev_hash, hash) VALUES (?, ?, ?)"
                data_to_insert = (image_filename, request.form['prev_hash'], request.form['hash'])
                connection = sqlite3.connect(database_path)
                cursor = connection.cursor()
                cursor.execute(insert_query, data_to_insert)
                connection.commit()
            except sqlite3.Error as e:
                connection.rollback()
                print("Wrong")
            finally:
                connection.close()

            return "OK"
        else:
            return "Wrong"
    else:
        return "No image file provided."


if __name__ == '__main__':
    app.run(debug=True, port=8001)