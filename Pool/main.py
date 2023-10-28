import argparse
import urllib.parse
import requests
import os
import sqlite3
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from MyLib.Camera import Camera
from MyLib.ImageBlock import ImageBlock

nodes = ['http://127.0.0.1:8001', 'http://127.0.0.1:8002', 'http://127.0.0.1:8003']
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


# Select Prev Hash
try:
    connection = sqlite3.connect(database_path)
    cursor = connection.cursor()

    select_query = "SELECT hash FROM blockchain ORDER BY id DESC LIMIT 1"
    cursor.execute(select_query)

    # Fetch the result
    result = cursor.fetchone()

    if result:
        prev_hash = result[0]
    else:
        prev_hash = "e1l1ya"

except sqlite3.Error as e:
    print("Error:", e)

finally:
    if connection:
        connection.close()


def upload_image_to_node(url, file_data, data, file_name, prev_hash):
    try:
        datafiles = {'image': (file_name, file_data, 'image/jpeg')}
        data['prev_hash'] = prev_hash
        res = requests.post(url + "/upload_image", timeout=5, files=datafiles, data=data)
        content = res.text.lower()
        is_ok = "ok" in content
        return is_ok
    except requests.RequestException:
        return False


def find_different_hashes(lst):
    hash_count = {}
    different_hashes = []

    for index, item in enumerate(lst):
        item_hash = hash(item)
        if item_hash in hash_count:
            hash_count[item_hash].append(index)
        else:
            hash_count[item_hash] = [index]

    for hash_value, indices in hash_count.items():
        if len(indices) == 1:
            different_hashes.append(indices[0])
    return different_hashes

def find_true_hashes(lst):
    hash_mapping = {}

    for value in lst:
        value_hash = hash(value)
        if value_hash in hash_mapping:
            hash_mapping[value_hash].append(value)
        else:
            hash_mapping[value_hash] = [value]

    same_hash_values = []

    for hash_value, values in hash_mapping.items():
        if len(values) > 1:
            same_hash_values.extend(values)

    return same_hash_values[0]


def download_all_images(url):
    response = requests.get(url + "/zip")

    if response.status_code == 200:
        with open("img.zip", 'wb') as output_file:
            output_file.write(response.content)
        print("Downloaded all images as ZIP")
    else:
        print("Failed to download the file")

def upload_zip(url):
    with open("img.zip", 'rb') as file:
        response = requests.post(url + "/zip", files={'zip_file': file})
    return response


def download_database(url):
    response = requests.get(url + "/database")

    if response.status_code == 200:
        with open(database_path, 'wb') as output_file:
            output_file.write(response.content)
        print("Downloaded hashes.db")
    else:
        print("Failed to download the file")


def upload_database(url):
    with open(database_path, 'rb') as file:
        response = requests.post(url + "/database", files={'database': file})
    return response

def get_hash(url):
    try:
        response = requests.get(url + "/hash")
        return response.text.strip()  # Use .strip() to remove leading/trailing whitespace
    except requests.RequestException:
        return None


if __name__ == "__main__":
    file_path = "Images/"

    # Parse ARGS
    parser = argparse.ArgumentParser(
        description="Capture frames from an RTSP camera and create a simple image blockchain.")
    parser.add_argument("--url", required=True, help="RTSP URL of the camera")
    parser.add_argument("--port", required=True, help="Port number of the camera")
    parser.add_argument("--username", help="Username for RTSP authentication")
    parser.add_argument("--password", help="Password for RTSP authentication")
    parser.add_argument("--path", help="path for RTSP authentication")

    args = parser.parse_args()

    # Connect to Camera
    if args.username and args.password:
        encoded_username = urllib.parse.quote(args.username)
        encoded_password = urllib.parse.quote(args.password)
        full_url = f"rtsp://{encoded_username}:{encoded_password}@{args.url}:{args.port}{args.path}"
    else:
        full_url = f"rtsp://{args.url}:{args.port}{args.path}"

    cam = Camera(full_url)

    while True:
        # Check is picture Taken
        has_picture = cam.capture_camera()
        if has_picture:
            print("Image taken")

            # Get image name
            file_name = cam.get_last_image()

            with open(file_path + file_name, "rb") as file:
                file_data = file.read()

            # Send to all nodes
            current_hash = ImageBlock(file_data, prev_hash).hash
            data = {'hash': current_hash}

            threshold = len(nodes) // 2 + 1  # Half or more

            with ProcessPoolExecutor() as executor:
                results = list(executor.map(upload_image_to_node, nodes, [file_data] * len(nodes), [data] * len(nodes), [file_name] * len(nodes), [prev_hash] * len(nodes)))

            result_counter = Counter(results)
            print(result_counter)
            if result_counter[True] >= threshold:
                # Replace Prev Hash
                prev_hash = current_hash
                try:
                    connection = sqlite3.connect(database_path)
                    cursor = connection.cursor()

                    delete_query = "DELETE FROM blockchain"
                    cursor.execute(delete_query)
                    connection.commit()

                    insert_query = "INSERT INTO blockchain (name, prev_hash, hash) VALUES (?, ?, ?)"
                    data_to_insert = (file_name, prev_hash, current_hash)
                    cursor.execute(insert_query, data_to_insert)
                    connection.commit()

                except sqlite3.Error as e:
                    print("Error:", e)

                finally:
                    if connection:
                        connection.close()
                print("Block Accepted")
            else:
                os.remove(file_path + file_name)
                print("Block Not Accepted")

            # Check every one has same hash
            with ProcessPoolExecutor() as executor:
                hash_list = list(executor.map(get_hash, nodes))

            # Find server with different hash
            different_hashes = find_different_hashes(hash_list)
            if len(different_hashes) != 0:
                selected_nodes = [node for index, node in enumerate(nodes) if index not in different_hashes]
                safe_node = selected_nodes[0]
                download_all_images(safe_node)
                download_database(safe_node)

                for index in different_hashes:
                    byzantine_node = nodes[index]
                    response1 = upload_zip(byzantine_node)
                    response2 = upload_database(byzantine_node)
                    if response1.status_code == 200 and response2.status_code == 200:
                        print(f"Byzantine node {byzantine_node} fixed")