import cv2
import os
import time
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


def capture_face(face_path, window_title, instruction):
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 4)

        cv2.putText(frame, instruction,
                    (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)

        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.imshow(window_title, frame)
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



def update_face(username):
    user_dir = os.path.join(DATASET_DIR, username)
    face_path = os.path.join(user_dir, "face.jpg")

    if not os.path.exists(user_dir):
        return False
    return capture_face(
        face_path,
        "Face Capture",
        "Press ENTER to capture face (Q to cancel)"
    )


def add_member(account_username, member_name):
    account_dir = os.path.join(DATASET_DIR, account_username)
    if not os.path.exists(account_dir):
        return False

    members_dir = os.path.join(account_dir, "members")
    os.makedirs(members_dir, exist_ok=True)

    member_dir = os.path.join(members_dir, member_name)
    if os.path.exists(member_dir):
        return False

    os.makedirs(member_dir, exist_ok=True)
    face_path = os.path.join(member_dir, "face.jpg")

    return capture_face(
        face_path,
        "Add Member Face",
        "Press ENTER to capture member face (Q to cancel)"
    )



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

    for account_name in os.listdir(DATASET_DIR):
        account_dir = os.path.join(DATASET_DIR, account_name)
        if not os.path.isdir(account_dir):
            continue

        img_path = os.path.join(account_dir, "face.jpg")
        if os.path.exists(img_path):
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is not None:
                faces.append(img)
                labels.append(label)
                label_map[label] = account_name
                label += 1

        members_dir = os.path.join(account_dir, "members")
        if not os.path.isdir(members_dir):
            continue

        for member_name in os.listdir(members_dir):
            member_dir = os.path.join(members_dir, member_name)
            if not os.path.isdir(member_dir):
                continue

            member_face = os.path.join(member_dir, "face.jpg")
            if not os.path.exists(member_face):
                continue

            img = cv2.imread(member_face, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            faces.append(img)
            labels.append(label)
            label_map[label] = account_name
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
        saved_hash = f.read().strip()

    return verify_password(password, saved_hash)



def verify_face(username):
    label_map = train_model()
    if not label_map:
        return False

    target_labels = {
        label for label, account_name in label_map.items()
        if account_name == username
    }

    if not target_labels:
        return False

    decision = None
    decision_time = None
    start_time = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.2, 4)

        matched = False
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            face = gray[y:y+h, x:x+w]
            label, confidence = recognizer.predict(face)

            if label in target_labels and confidence < 70:
                matched = True

        cv2.putText(frame, "Press Q to Close",
                    (1650, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8, (0, 255, 0), 2)

        if decision is None and matched:
            decision = "granted"
            decision_time = time.time()
            unlock_door()
        elif decision is None and (time.time() - start_time) >= 5:
            decision = "denied"
            decision_time = time.time()

        if decision == "granted":
            cv2.putText(frame, "Face verified - door unlocked", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
        elif decision == "denied":
            cv2.putText(frame, "Face not recognized", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("Verify Face to Unlock", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

        if decision is not None and (time.time() - decision_time) >= 5:
            cv2.destroyAllWindows()
            return decision == "granted"

    cv2.destroyAllWindows()
    return False

def get_full_name(username):
    info_file = os.path.join(DATASET_DIR, username, "info.txt")
    if os.path.exists(info_file):
        with open(info_file, "r") as f:
            return f.read()
    return username
