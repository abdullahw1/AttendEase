import cv2
import face_recognition
import numpy as np
import os
import pickle
from datetime import datetime
import psycopg2
import requests
import random

# Load the saved encodings
with open('encodings.pkl', 'rb') as f:
    data = pickle.load(f)
encodeListKnownFaces = data['encodings']
classNames = data['labels']

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
        cur.execute("SELECT studentid, first_name, last_name FROM students")
        students = cur.fetchall()
        cur.close()
        conn.close()
        return students
    except Exception as e:
        print(f'Error: {e}')

# Fetch student records from the database
students = fetch_students()
classNames = [f"{student[1]} {student[2]}" for student in students]

# Initialize last attendance record dictionary
last_attendance = {}  # Make sure this is defined outside the loop

# Prompt the user to enter the class ID
class_id = input("Enter the class ID: ")

# Initialize the camera
cap = cv2.VideoCapture(0)

# Recognition threshold
RECOGNITION_THRESHOLD = 0.6  # This threshold might need tuning based on your dataset
# Initialize attendance ID counter
attendance_id_counter = random.randint(10, 20)

# Main processing loop
while True:
    success, img = cap.read()
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        attendance_id_counter += 1
        matches = face_recognition.compare_faces(encodeListKnownFaces, encodeFace)
        faceDis = face_recognition.face_distance(encodeListKnownFaces, encodeFace)
        matchIndex = np.argmin(faceDis)

        y1, x2, y2, x1 = [i * 4 for i in faceLoc]

        if matches[matchIndex] and faceDis[matchIndex] < RECOGNITION_THRESHOLD:
            student_id = students[matchIndex][0]
            name = classNames[matchIndex].upper()
        else:
            student_id = "Unrecognized"
            name = "Unrecognized Individual"

        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

        if student_id != "Unrecognized":
            current_time = datetime.now()
            if student_id not in last_attendance or (current_time - last_attendance[student_id]).total_seconds() > 180:
                last_attendance[student_id] = current_time
                timestamp = current_time.strftime("%Y-%m-%d %H:%M:%S")
                url = f'http://localhost:8000/attendance_record?attendanceid={attendance_id_counter}&student_id={student_id}&class_id={class_id}&timestamp={timestamp}'
                response = requests.post(url)
                if response.status_code == 200:
                    print(f"Attendance recorded successfully for attendance_id={attendance_id_counter}.")
                attendance_id_counter += 1

    cv2.imshow('webcam', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
