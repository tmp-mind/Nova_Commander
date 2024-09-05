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
import signal
import time

# Chemin vers le modèle Vosk
MODEL_PATH = "vosk-model-small-fr-0.22"

# Commandes spécifiques pour le contrôle du curseur
COMMANDS = {
    "clique gauche": "mouse_click_left",
    "maintient le clique gauche": "mouse_hold_left",
    "relâche clique gauche": "mouse_release_left",
    "clic droit": "mouse_click_right",
    "molette vers le haut": "scroll_up",
    "molette vers le bas": "scroll_down",
    "fleche vers le haut": "press_arrow_up",
    "fleche vers le bas": "press_arrow_down",
    "fleche vers la gauche": "press_arrow_left",
    "fleche vers la droite": "press_arrow_right",
    "ferme le module du curseur": "close_cursor_module"
}

# Queue pour gérer les données audio
audio_queue = queue.Queue()

# Initialisation de MediaPipe pour la détection des visages et des yeux
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Variables pour le contrôle du curseur
cursor_move_active = True
calibrated_center = None
calibration_mode = True
move_direction = None
move_thread = None
cap = None
stop_threads = False

# Fonction de callback pour la reconnaissance vocale
def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

# Fonction pour arrêter le déplacement du curseur et fermer le script
def stop_cursor_move(command_text=None):
    global cursor_move_active, stop_threads
    cursor_move_active = False
    stop_threads = True
    print("Mode de déplacement du curseur désactivé.")
    release_resources()
    close_cursor_module()

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

# Fonction pour fermer le module de contrôle du curseur
def close_cursor_module(command_text=None):
    print("Fermeture du module de contrôle du curseur.")
    release_resources()  # Libère les ressources avant de fermer
    os.kill(os.getpid(), signal.SIGTERM)  # Terminer le processus actuel du script pour fermer le terminal

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

    # Inversion des mouvements horizontaux (gauche et droite inversés)
    if delta_x > 0.02 and delta_y < -0.02:
        return "up_left", speed_x, speed_y
    elif delta_x < -0.02 and delta_y < -0.02:
        return "up_right", speed_x, speed_y
    elif delta_x > 0.02 and delta_y > 0.02:
        return "down_left", speed_x, speed_y
    elif delta_x < -0.02 and delta_y > 0.02:
        return "down_right", speed_x, speed_y
    elif delta_x > 0.02:
        return "left", speed_x, speed_y
    elif delta_x < -0.02:
        return "right", speed_x, speed_y
    elif delta_y > 0.02:
        return "down", speed_x, speed_y
    elif delta_y < -0.02:
        return "up", speed_x, speed_y
    else:
        return "center", 0, 0



# Fonction pour déplacer le curseur en continu
def move_cursor_continuously():
    global move_direction, move_speed_x, move_speed_y

    while cursor_move_active and not stop_threads:
        if move_direction == "left":
            pyautogui.moveRel(-move_speed_x, 0)
        elif move_direction == "right":
            pyautogui.moveRel(move_speed_x, 0)
        elif move_direction == "up":
            pyautogui.moveRel(0, -move_speed_y)
        elif move_direction == "down":
            pyautogui.moveRel(0, move_speed_y)
        elif move_direction == "up_left":
            pyautogui.moveRel(-move_speed_x, -move_speed_y)
        elif move_direction == "up_right":
            pyautogui.moveRel(move_speed_x, -move_speed_y)
        elif move_direction == "down_left":
            pyautogui.moveRel(-move_speed_x, move_speed_y)
        elif move_direction == "down_right":
            pyautogui.moveRel(move_speed_x, move_speed_y)
        time.sleep(0.05)


# Fonction pour traiter les cadres de la vidéo
def process_frame(face_landmarks, frame):
    global move_direction, move_speed_x, move_speed_y, move_thread

    direction, speed_x, speed_y = detect_head_direction(face_landmarks)

    if direction != move_direction or speed_x != move_speed_x or speed_y != move_speed_y:
        move_direction = direction
        move_speed_x = max(10, speed_x)
        move_speed_y = max(10, speed_y)
        if move_direction == "center":
            move_direction = None
        else:
            if move_thread is None or not move_thread.is_alive():
                move_thread = threading.Thread(target=move_cursor_continuously)
                move_thread.start()


# Fonction pour écouter les commandes vocales
def listen_for_commands():
    print("En attente des commandes...")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16',
                           channels=1, callback=callback):
        while True:
            data = audio_queue.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
                result_dict = json.loads(result)
                if 'text' in result_dict:
                    command_text = result_dict['text'].lower().strip()
                    print(f"Reconnu: {command_text}")

                    matched = False
                    for command, action in COMMANDS.items():
                        if command in command_text:
                            threading.Thread(target=globals()[action], args=(command_text,)).start()
                            matched = True
                            break

                    if not matched:
                        print("Commande non reconnue.")

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

# Démarrage du thread de reconnaissance vocale
threading.Thread(target=listen_for_commands, daemon=True).start()

# Accéder à la webcam pour l'eye tracking avec l'API backend DirectShow
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

while cap.isOpened() and not stop_threads:
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

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

release_resources()
