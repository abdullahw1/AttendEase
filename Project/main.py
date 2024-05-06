import cv2
import face_recognition
import numpy as np
import os
import pickle
from datetime import datetime
import psycopg2
import random
import requests

# Load the saved encodings
with open('encodings.pkl', 'rb') as f:
    data = pickle.load(f)
encodeListKnownFaces = data['encodings']
# classNames = data['labels']

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
        cur.execute("SELECT studentid, first_name, last_name FROM students")  # Selecting first_name and last_name columns
        return cur.fetchall()
    except Exception as e:
        print(f'Error: {e}')
    finally:
        cur.close()
        conn.close()

# Fetch student records from the database
students = fetch_students()
# Get the names of the students from the fetched records
classNames = [f"{student[1]} {student[2]}" for student in students]  # Combining first and last names

# # Get the names of the students from the fetched records
# classNames = [student[1] for student in students]  # Assuming the name is stored in the second column of the fetched records

# Get current timestamp in the correct format
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# Function to mark attendance in CSV file
def markAttendanceInCSV(attendance_id, class_id, student_id, entry_timestamp):
    with open('attendance.csv', 'a') as f:
        f.write(f'{attendance_id},{class_id},{student_id},{entry_timestamp}\n')

# Prompt the user to enter the class ID
class_id = input("Enter the class ID: ")

# Initialize the camera
cap = cv2.VideoCapture(0)

# Initialize matches before the loop
matches = []
matchIndex = None

# Initialize attendance ID counter
attendance_id_counter = 0
attendance_id_counter = random.randint(10, 20)

# Loop to capture frames from the webcam
while True:
    success, img = cap.read()
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)  # Reduce image size to improve efficiency
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)

    # Find face locations and encodings in the current frame
    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    # Iterate over each face found in the current frame
    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        # Increment attendance ID counter
        attendance_id_counter += 1

        # Compare the current face encoding with the known encodings
        matches = face_recognition.compare_faces(encodeListKnownFaces, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnownFaces, encodeFace)
        matchIndex = np.argmin(faceDis)

        # If a match is found, mark attendance and display the name on the frame
        if matches and matchIndex is not None and matches[matchIndex]:
            student_id = students[matchIndex][0]  # Get the student ID from the database query result
            name = classNames[matchIndex].upper()
            y1, x2, y2, x1 = faceLoc
            y1, x2, y2, x1 = y1 * 4, x2 * 4, y2 * 4, x1 * 4
            cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.rectangle(img, (x1, y1 - 35), (x2, y2), (0, 255, 0))
            cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_ITALIC, 1, (255, 255, 255), 2)

            # Call function to mark attendance in the CSV file
            markAttendanceInCSV(attendance_id_counter, class_id, student_id, timestamp)

            # Send HTTP POST request to the endpoint
            url = f'http://localhost:8000/attendance_record?attendanceid={attendance_id_counter}&student_id={student_id}&class_id={class_id}&timestamp={timestamp}'
            response = requests.post(url)
            if response.status_code == 200:
                print("Attendance recorded successfully.")

    # Display the webcam feed with recognized faces
    cv2.imshow('webcam', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    # Add this condition to break out of the main loop when a person is recognized
    if matches and matchIndex is not None and matches[matchIndex]:
        break

# Release the webcam and close all windows
cap.release()
cv2.destroyAllWindows()
