import cv2
import os
import numpy as np
import hashlib
import shutil


try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError:
    class GPIO:
        BCM = OUT = None
        HIGH = 1
        LOW = 0
        def setmode(x): pass
        def setup(pin, mode): pass
        def output(pin, value):
            print(f"[LOCK] {'UNLOCKED' if value else 'LOCKED'}")
        def cleanup(): pass

LOCK_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(LOCK_PIN, GPIO.OUT)
GPIO.output(LOCK_PIN, GPIO.LOW)

door_unlocked = False

def unlock_door():
    global door_unlocked
    if not door_unlocked:
        GPIO.output(LOCK_PIN, GPIO.HIGH)
        door_unlocked = True

def lock_door():
    global door_unlocked
    GPIO.output(LOCK_PIN, GPIO.LOW)
    door_unlocked = False



DATASET_DIR = "faces"
os.makedirs(DATASET_DIR, exist_ok=True)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

recognizer = cv2.face.LBPHFaceRecognizer_create()
cap = cv2.VideoCapture(0)



def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed



def create_account(username, password, first_name, last_name):
    user_dir = os.path.join(DATASET_DIR, username)
    os.makedirs(user_dir, exist_ok=True)

    with open(os.path.join(user_dir, "password.txt"), "w") as f:
        f.write(hash_password(password))

    with open(os.path.join(user_dir, "info.txt"), "w") as f:
        f.write(f"{first_name} {last_name}")

    return update_face(username)



def update_face(username):
    user_dir = os.path.join(DATASET_DIR, username)
    face_path = os.path.join(user_dir, "face.jpg")

    if not os.path.exists(user_dir):
        return False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 4)

        cv2.putText(frame, "Press ENTER to capture face (Q to cancel)",
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.imshow("Face Capture", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == 13 and len(faces) > 0:
            x, y, w, h = faces[0]
            face = gray[y:y+h, x:x+w]
            cv2.imwrite(face_path, face)
            cv2.destroyAllWindows()
            return True

        if key == ord("q"):
            break

    cv2.destroyAllWindows()
    return False



def delete_account(username):
    user_dir = os.path.join(DATASET_DIR, username)

    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
        return True

    return False



def train_model():
    faces, labels = [], []
    label_map = {}
    label = 0

    for name in os.listdir(DATASET_DIR):
        img_path = os.path.join(DATASET_DIR, name, "face.jpg")
        if not os.path.exists(img_path):
            continue

        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        faces.append(img)
        labels.append(label)
        label_map[label] = name
        label += 1

    if faces:
        recognizer.train(faces, np.array(labels))
        return label_map
    return None


def login(username, password):
    user_dir = os.path.join(DATASET_DIR, username)
    pwd_file = os.path.join(user_dir, "password.txt")

    if not os.path.exists(pwd_file):
        return False

    with open(pwd_file, "r") as f:
        saved_hash = f.read()

    return verify_password(password, saved_hash)



def verify_face(username):
    label_map = train_model()
    if not label_map:
        return False

    target_label = None
    for k, v in label_map.items():
        if v == username:
            target_label = k

    if target_label is None:
        return False

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 4)

        for (x, y, w, h) in faces:
            face = gray[y:y+h, x:x+w]
            label, confidence = recognizer.predict(face)

            if label == target_label and confidence < 70:
                unlock_door()
                cv2.destroyAllWindows()
                return True

        cv2.imshow("Verify Face to Unlock", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cv2.destroyAllWindows()
    return False

def get_full_name(username):
    info_file = os.path.join(DATASET_DIR, username, "info.txt")
    if os.path.exists(info_file):
        with open(info_file, "r") as f:
            return f.read()
    return username
