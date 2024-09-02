import cv2
import mediapipe as mp
import numpy as np
import pyautogui
import threading
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import queue
import json
import os
import sys
import time
import subprocess

# Chemin vers le modèle Vosk
MODEL_PATH = "vosk-model-fr-0.22"
STOP_COMMANDS = ["stop", "curseur stop"]

# Commandes possibles sans avoir besoin de dire le mot-clé "nova"
COMMANDS = {
    "clic gauche": "mouse_click_left",
    "maintient clic gauche": "mouse_hold_left",
    "relâche clic gauche": "mouse_release_left",
    "clic droit": "mouse_click_right",
    "molette haut": "scroll_up",
    "molette bas": "scroll_down",
    "fleche haut": "press_arrow_up",
    "fleche bas": "press_arrow_down",
    "fleche gauche": "press_arrow_left",
    "fleche droite": "press_arrow_right"
}

# Queue pour gérer les données audio
audio_queue = queue.Queue()

# Initialisation de MediaPipe pour la détection des visages et des yeux
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Variables pour le contrôle du curseur
cursor_move_active = True  # Le contrôle du curseur démarre automatiquement
calibrated_center = None
calibration_mode = True
move_direction = None
move_thread = None
cap = None

# Fonction de callback pour la reconnaissance vocale
def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

# Fonction pour arrêter le déplacement du curseur et fermer le script
def stop_cursor_move(command_text=None):
    global cursor_move_active
    cursor_move_active = False
    print("Mode de déplacement du curseur désactivé.")
    release_resources()
    print("Fermeture du terminal du module de contrôle du curseur...")
    close_terminal()
    sys.exit(0)  # Fermer le script proprement

# Fonction pour fermer uniquement le terminal du module de contrôle du curseur
def close_terminal():
    terminal_pid = os.getppid()
    print(f"Fermeture du terminal du module avec PID: {terminal_pid}")
    subprocess.run(["xdotool", "search", "--pid", str(terminal_pid), "windowclose"])

# Fonction pour effectuer un clic gauche
def mouse_click_left(command_text=None):
    pyautogui.click()
    print("Clic gauche effectué.")

# Fonction pour maintenir le clic gauche
def mouse_hold_left(command_text=None):
    pyautogui.mouseDown()
    print("Maintien du clic gauche.")

# Fonction pour relâcher le clic gauche
def mouse_release_left(command_text=None):
    pyautogui.mouseUp()
    print("Clic gauche relâché.")

# Fonction pour effectuer un clic droit
def mouse_click_right(command_text=None):
    pyautogui.click(button='right')
    print("Clic droit effectué.")

# Fonction pour faire défiler vers le haut
def scroll_up(command_text=None):
    pyautogui.scroll(50)
    print("Molette haut.")

# Fonction pour faire défiler vers le bas
def scroll_down(command_text=None):
    pyautogui.scroll(-50)
    print("Molette bas.")

# Fonction pour appuyer sur la flèche haut
def press_arrow_up(command_text=None):
    pyautogui.press('up')
    print("Flèche haut pressée.")

# Fonction pour appuyer sur la flèche bas
def press_arrow_down(command_text=None):
    pyautogui.press('down')
    print("Flèche bas pressée.")

# Fonction pour appuyer sur la flèche gauche
def press_arrow_left(command_text=None):
    pyautogui.press('left')
    print("Flèche gauche pressée.")

# Fonction pour appuyer sur la flèche droite
def press_arrow_right(command_text=None):
    pyautogui.press('right')
    print("Flèche droite pressée.")

# Fonction pour calibrer la position centrale
def calibrate_center_position(face_landmarks):
    left_eye_indices = [33, 160, 158, 133, 153, 144]
    right_eye_indices = [362, 385, 387, 263, 373, 380]

    left_eye_landmarks = [face_landmarks.landmark[idx] for idx in left_eye_indices]
    right_eye_landmarks = [face_landmarks.landmark[idx] for idx in right_eye_indices]

    left_eye_center = np.mean([(lm.x, lm.y) for lm in left_eye_landmarks], axis=0)
    right_eye_center = np.mean([(lm.x, lm.y) for lm in right_eye_landmarks], axis=0)

    return np.array([(left_eye_center[0] + right_eye_center[0]) / 2, 
                     (left_eye_center[1] + right_eye_center[1]) / 2])

# Fonction pour détecter la direction de la tête
def detect_head_direction(face_landmarks):
    global calibrated_center

    left_eye_indices = [33, 160, 158, 133, 153, 144]
    right_eye_indices = [362, 385, 387, 263, 373, 380]

    left_eye_landmarks = [face_landmarks.landmark[idx] for idx in left_eye_indices]
    right_eye_landmarks = [face_landmarks.landmark[idx] for idx in right_eye_indices]

    left_eye_center = np.mean([(lm.x, lm.y) for lm in left_eye_landmarks], axis=0)
    right_eye_center = np.mean([(lm.x, lm.y) for lm in right_eye_landmarks], axis=0)

    eye_center = np.array([(left_eye_center[0] + right_eye_center[0]) / 2, 
                           (left_eye_center[1] + right_eye_center[1]) / 2])

    if calibrated_center is None:
        calibrated_center = eye_center

    delta_x = eye_center[0] - calibrated_center[0]
    delta_y = eye_center[1] - calibrated_center[1]

    speed_x = abs(delta_x) * 300
    speed_y = abs(delta_y) * 300

    if delta_x < -0.02:
        return "left", speed_x
    elif delta_x > 0.02:
        return "right", speed_x
    elif delta_y > 0.02:
        return "down", speed_y
    elif delta_y < -0.02:
        return "up", speed_y
    else:
        return "center", 0

# Fonction pour déplacer le curseur en continu
def move_cursor_continuously():
    global move_direction, move_speed

    while cursor_move_active:
        if move_direction == "left":
            pyautogui.moveRel(-move_speed, 0)
        elif move_direction == "right":
            pyautogui.moveRel(move_speed, 0)
        elif move_direction == "up":
            pyautogui.moveRel(0, -move_speed)
        elif move_direction == "down":
            pyautogui.moveRel(0, move_speed)
        time.sleep(0.05)

# Fonction pour traiter les cadres de la vidéo
def process_frame(face_landmarks, frame):
    global move_direction, move_speed, move_thread

    direction, speed = detect_head_direction(face_landmarks)

    if direction != move_direction or speed != move_speed:
        move_direction = direction
        move_speed = max(10, speed)
        if move_direction == "center":
            move_direction = None
        else:
            if move_thread is None or not move_thread.is_alive():
                move_thread = threading.Thread(target=move_cursor_continuously)
                move_thread.start()

    print(f"Direction de la tête: {direction}, Vitesse: {speed}")

# Fonction pour écouter les commandes vocales
def listen_for_keyword():
    print(f"En attente des commandes de fin...")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', 
                           channels=1, callback=callback):
        while True:
            data = audio_queue.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                result_dict = json.loads(result)
                if 'text' in result_dict:
                    recognized_text = result_dict['text'].lower().strip()
                    print(f"Reconnu: {recognized_text}")
                    if recognized_text in STOP_COMMANDS:
                        print("Commande de fin détectée : Arrêt du script...")
                        stop_cursor_move()
                    else:
                        for command, action in COMMANDS.items():
                            if command in recognized_text:
                                threading.Thread(target=globals()[action]).start()
                                break

# Fonction pour libérer les ressources
def release_resources():
    global cap
    if cap:
        cap.release()
    cv2.destroyAllWindows()
    print("Ressources libérées et script terminé.")

# Vérification du modèle Vosk
if not os.path.exists(MODEL_PATH):
    print(f"Le modèle Vosk est introuvable dans {MODEL_PATH}. Veuillez vérifier le chemin.")
    sys.exit(1)

model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, 16000)

def voice_control_thread():
    listen_for_keyword()

threading.Thread(target=voice_control_thread, daemon=True).start()

# Accéder à la webcam pour l'eye tracking
cap = cv2.VideoCapture(0)

while cap.isOpened():
    success, frame = cap.read()
    if not success:
        break

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_frame)

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            if calibration_mode:
                calibrated_center = calibrate_center_position(face_landmarks)
                print("Calibration terminée.")
                calibration_mode = False
            elif cursor_move_active:
                process_frame(face_landmarks, frame)

    #cv2.imshow('Eye Tracker', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

release_resources()
