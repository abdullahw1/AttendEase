# SerializeEncodings.py

import os
import face_recognition
import pickle
import psycopg2
import requests

# Function to fetch student records from the database
def fetch_students():
    try:
        conn = psycopg2.connect(
            host="monorail.proxy.rlwy.net",
            port="28291",
            dbname="railway",
            user="postgres",
            password="16ae*c2cbg4Dc*eGEfGCg33g11Fb4gDB"
        )
        cur = conn.cursor()
        cur.execute("SELECT studentid, photo_url FROM students")
        return cur.fetchall()
    except Exception as e:
        print(f'Error: {e}')
    finally:
        cur.close()
        conn.close()

# Function to download and save images
def download_images(students, save_path):
    for student_id, photo_url in students:
        try:
            # Get the filename from the student ID
            filename = f"{student_id}.jpg"  # You can change the file extension if needed

            # Download the image
            response = requests.get(photo_url)
            if response.status_code == 200:
                # Save the image to the specified path
                with open(os.path.join(save_path, filename), 'wb') as f:
                    f.write(response.content)
                print(f"Image downloaded and saved: {filename}")
            else:
                print(f"Failed to download image for student ID {student_id}")
        except Exception as e:
            print(f'Error downloading image for student ID {student_id}: {e}')

# Path to the folder where images will be saved
images_folder = 'aws_student_pics'

# Fetch student records from the database
students = fetch_students()

# Download and save images
if students:
    os.makedirs(images_folder, exist_ok=True)
    download_images(students, images_folder)
else:
    print("No student records found in the database.")

# Initialize a dictionary to store encodings and corresponding labels
encoding_data = {'encodings': [], 'labels': []}

# Iterate over each image file in the folder
for student_id, _ in students:
    # Load the image
    image_path = os.path.join(images_folder, f"{student_id}.jpg")
    image = face_recognition.load_image_file(image_path)

    # Encode faces in the image
    face_encodings = face_recognition.face_encodings(image)

    # Assuming there's only one face per image, add encoding and label to the dictionary
    if face_encodings:
        encoding_data['encodings'].append(face_encodings[0])
        encoding_data['labels'].append(student_id)  # Use the student ID as the label

# Serialize the encoding data into the 'encodings.pkl' file
with open('encodings.pkl', 'wb') as f:
    pickle.dump(encoding_data, f)


