import psycopg2
import os
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
            # Get the filename from the URL
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

# Path where you want to save the images
save_path = "/Users/abdullahwaheed/attendenceAI/Project/aws_student_pics"
# Fetch student records from the database
students = fetch_students()

# Download and save images
if students:
    os.makedirs(save_path, exist_ok=True)
    download_images(students, save_path)
else:
    print("No student records found in the database.")

