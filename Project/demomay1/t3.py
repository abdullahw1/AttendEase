import cv2
import face_recognition
import numpy as np
from datetime import datetime, timedelta
import psycopg2
import requests
import random
import pickle


# Load the saved encodings
with open('encodings.pkl', 'rb') as f:
    data = pickle.load(f)
encodeListKnownFaces = data['encodings']
classNames = data['labels']

def fetch_students():
    conn = psycopg2.connect(host="monorail.proxy.rlwy.net", port="28291", dbname="railway", user="postgres", password="16ae*c2cbg4Dc*eGEfGCg33g11Fb4gDB")
    cur = conn.cursor()
    cur.execute("SELECT studentid, first_name, last_name FROM students")
    students = cur.fetchall()
    cur.close()
    conn.close()
    return students

students = fetch_students()
student_info = {student[0]: f"{student[1]} {student[2]}" for student in students}

class_id = input("Enter the class ID: ")
cap = cv2.VideoCapture(0)
RECOGNITION_THRESHOLD = 0.6
ATTENDANCE_THRESHOLD = 0.7  # Threshold for accepting a recognition over multiple frames
frame_memory = {}
frame_window = 5  # Number of frames to consider for consistency check

while True:
    success, img = cap.read()
    imgS = cv2.resize(img, (0, 0), None, 0.25, 0.25)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    facesCurFrame = face_recognition.face_locations(imgS)
    encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)

    for encodeFace, faceLoc in zip(encodesCurFrame, facesCurFrame):
        faceDis = face_recognition.face_distance(encodeListKnownFaces, encodeFace)
        matchIndex = np.argmin(faceDis)
        min_distance = faceDis[matchIndex]

        y1, x2, y2, x1 = [i * 4 for i in faceLoc]
        if min_distance < RECOGNITION_THRESHOLD:
            student_id = students[matchIndex][0]
            matches = face_recognition.compare_faces(encodeListKnownFaces, encodeFace, tolerance=RECOGNITION_THRESHOLD)
            match_percentage = matches.count(True) / len(matches)

            if match_percentage > ATTENDANCE_THRESHOLD:
                frame_memory[student_id] = frame_memory.get(student_id, 0) + 1
                if frame_memory[student_id] >= frame_window * ATTENDANCE_THRESHOLD:
                    confirmed_student_id = student_id
                else:
                    confirmed_student_id = "Unconfirmed"
            else:
                confirmed_student_id = "Unrecognized"
        else:
            confirmed_student_id = "Unrecognized"

        name = student_info.get(confirmed_student_id, "Unrecognized Individual")
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)

        # Reset frame memory for old records
        old_keys = [key for key, val in frame_memory.items() if val < datetime.now() - timedelta(seconds=5)]
        for key in old_keys:
            del frame_memory[key]

    cv2.imshow('webcam', img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()

