import cv2
import os
import time
import numpy as np


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
            print(f"[LOCK STATUS] {'UNLOCKED' if value else 'LOCKED'}")
        def cleanup(): pass

LOCK_PIN = 18
GPIO.setmode(GPIO.BCM)
GPIO.setup(LOCK_PIN, GPIO.OUT)
GPIO.output(LOCK_PIN, GPIO.LOW)


door_unlocked = False

def unlock_door():
    global door_unlocked
    if door_unlocked:
        return
    GPIO.output(LOCK_PIN, GPIO.HIGH)
    door_unlocked = True
    print("🔓 Door unlocked (stays unlocked)")

def lock_door():
    global door_unlocked
    if not door_unlocked:
        return
    GPIO.output(LOCK_PIN, GPIO.LOW)
    door_unlocked = False
    print("🔒 Door locked")


DATASET_DIR = "faces"
os.makedirs(DATASET_DIR, exist_ok=True)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

recognizer = cv2.face.LBPHFaceRecognizer_create()

cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
if not cap.isOpened():
    print("❌ Camera not accessible")
    exit()


def create_account():
    name = input("Enter username: ").strip()
    user_dir = os.path.join(DATASET_DIR, name)

    if os.path.exists(user_dir):
        print("❌ User already exists")
        return

    os.makedirs(user_dir)
    print("📸 Look at the camera. Press SPACE to capture.")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        cv2.imshow("Create Account", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            if len(faces) == 1:
                cv2.imwrite(f"{user_dir}/face.jpg", face_img)
                print("✅ Face saved")
                break
            else:
                print("⚠️ Make sure only ONE face is visible")

    cv2.destroyWindow("Create Account")


def train_model():
    faces = []
    labels = []
    label_map = {}
    current_label = 0

    for name in os.listdir(DATASET_DIR):
        user_dir = os.path.join(DATASET_DIR, name)
        if not os.path.isdir(user_dir):
            continue

        img_path = os.path.join(user_dir, "face.jpg")
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue

        faces.append(img)
        labels.append(current_label)
        label_map[current_label] = name
        current_label += 1

    if len(faces) == 0:
        return None, None

    recognizer.train(faces, np.array(labels))
    return recognizer, label_map


def login():
    model, label_map = train_model()
    if model is None:
        print("❌ No users registered")
        return

    print("👀 Looking for authorized face... (press Q to cancel)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            label, confidence = model.predict(face_img)

            if confidence < 70:
                name = label_map[label]
                color = (0, 255, 0)
                unlock_door()
                cv2.putText(frame, f"Welcome {name}", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
                cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
                cv2.imshow("Login", frame)
                cv2.waitKey(1500)
                cv2.destroyAllWindows()
                return
            else:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
                cv2.putText(frame, "Unknown", (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

        cv2.imshow("Login", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

while True:
    print("\n===== SMART DOOR SYSTEM =====")
    print("1. Create Account")
    print("2. Login")
    print("3. Exit")
    print(f"Door Status: {'UNLOCKED' if door_unlocked else 'LOCKED'}")

    choice = input("Choose option: ")

    if choice == "1":
        create_account()
    elif choice == "2":
        login()
    elif choice == "3":
        print("Exiting system...")
        lock_door()
        break
    else:
        print("Invalid choice")

cap.release()
GPIO.cleanup()
