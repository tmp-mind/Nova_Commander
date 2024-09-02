import cv2
import mediapipe as mp
import numpy as np
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

# Commandes spécifiques pour le contrôle du jeu wakfu
COMMANDS = {
    "clic gauche": "mouse_click_left",
    "maintenir le clic": "mouse_hold_left",
    "relâche le clic ": "mouse_release_left",
    "clic droit": "mouse_click_right",
    "double clic": "double_click",
    "molette haut": "scroll_up",
    "molette bas": "scroll_down",
    "flèche haut": "press_arrow_up",
    "flèche bas": "press_arrow_down",
    "flèche gauche": "press_arrow_left",
    "flèche droite": "press_arrow_right",
    "lance le combat": "start_fight",
    "attaque un": "attack_one",
    "attaque deux": "attack_two",
    "attaque trois": "attack_three",
    "attaque quatre": "attack_four",
    "attaque cinq": "attack_five",
    "attaque six": "attack_six",
    "attaque sept": "attack_seven",
    "attaque huit": "attack_eight",
    "attaque neuf": "attack_nine",
    "attaque dix": "attack_ten",
    "attaque onze": "attack_eleven",
    "attaque douze": "attack_twelve",
    "attaque treize": "attack_thirteen",
    "attaque quatorze": "attack_fourteen",
    "attaque quinze": "attack_fifteen",
    "attaque seize": "attack_sixteen",
    "attaque dix sept": "attack_seventeen",
    "attaque dix huit": "attack_eighteen",
    "ouvre l'inventaire": "open_inventory",
    "ferme l'inventaire": "open_inventory",
    "curseur au centre": "move_cursor_center",
    "curseur à droite": "move_cursor_right",
    "curseur à gauche": "move_cursor_left",
    "curseur en haut": "move_cursor_up",
    "curseur en bas": "move_cursor_down",
    "ouvrir le sac": "toggle_haven_bag",
    "fermez le sac": "toggle_haven_bag",
    "ouvre les aptitudes": "open_aptitudes",
    "ferme les aptitudes": "open_aptitudes",
    "ouvre les sorts": "open_spells",
    "ferme les sorts": "open_spells",
    "ouvre les héros": "open_heroes",
    "ferme les héros": "open_heroes",
    "ouvre les métiers": "open_professions",
    "ferme les métiers": "open_professions",
    "ouvre la carte": "open_map",
    "ferme la carte": "open_map",
    "ouvre le menu": "open_menu",
    "ferme le menu": "open_menu",
    "ouvre la page des builds": "open_build_manager",
    "ferme la page des builds": "open_build_manager",
    "envoyer le message": "send_message",
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

# Fonction pour envoyer un message
def send_message(command_text=None):
    if not command_text:
        print("Erreur : aucun texte de commande n'a été fourni à la fonction send_message.")
        return

    # Appuyer sur 'Entrée' pour ouvrir la boîte de dialogue du chat
    subprocess.run(["xdotool", "key", "Return"])
    
    # Extraire le texte à écrire après "envoyer le message"
    message_to_send = command_text.replace("envoyer le message", "").strip()
    
    if not message_to_send:
        print("Erreur : aucun message à envoyer.")
        return
    
    # Écrire le message dans la boîte de dialogue
    subprocess.run(["xdotool", "type", message_to_send])
    print(f"Message écrit: {message_to_send}")
    
    # Attendre 2 secondes pour s'assurer que le message est bien écrit
    time.sleep(2)
    
    # Appuyer sur 'Entrée' pour envoyer le message
    subprocess.run(["xdotool", "key", "Return"])
    
    # Attendre 0.5 secondes
    time.sleep(0.5)
    
    # Appuyer à nouveau sur 'Entrée' pour confirmer l'envoi ou fermer la boîte de dialogue
    subprocess.run(["xdotool", "key", "Return"])
    
    print("Message envoyé.")

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
    subprocess.run(["xdotool", "click", "1"])
    print("Clic gauche effectué.")

# Fonction pour maintenir le clic gauche
def mouse_hold_left(command_text=None):
    subprocess.run(["xdotool", "mousedown", "1"])
    print("Maintien du clic gauche.")

# Fonction pour relâcher le clic gauche
def mouse_release_left(command_text=None):
    subprocess.run(["xdotool", "mouseup", "1"])
    print("Clic gauche relâché.")

# Fonction pour effectuer un clic droit
def mouse_click_right(command_text=None):
    subprocess.run(["xdotool", "click", "3"])
    print("Clic droit effectué.")

# Double clic gauche
def double_click(command_text=None):
    subprocess.run(["xdotool", "click", "--repeat", "2", "1"])
    print("Double clic gauche effectué.")

# Fonction pour faire défiler vers le haut
def scroll_up(command_text=None):
    subprocess.run(["xdotool", "click", "4"])
    print("Molette haut.")

# Fonction pour faire défiler vers le bas
def scroll_down(command_text=None):
    subprocess.run(["xdotool", "click", "5"])
    print("Molette bas.")

# Fonction pour appuyer sur la flèche haut
def press_arrow_up(command_text=None):
    subprocess.run(["xdotool", "key", "Up"])
    print("Flèche haut pressée.")

# Fonction pour appuyer sur la flèche bas
def press_arrow_down(command_text=None):
    subprocess.run(["xdotool", "key", "Down"])
    print("Flèche bas pressée.")

# Fonction pour appuyer sur la flèche gauche
def press_arrow_left(command_text=None):
    subprocess.run(["xdotool", "key", "Left"])
    print("Flèche gauche pressée.")

# Fonction pour appuyer sur la flèche droite
def press_arrow_right(command_text=None):
    subprocess.run(["xdotool", "key", "Right"])
    print("Flèche droite pressée.")

# Fonction pour entrer ou sortir du Havre-Sac
def toggle_haven_bag(command_text=None):
    subprocess.run(["xdotool", "key", "Shift+h"])
    print("Entrer/Sortir du Havre-Sac (Shift + H).")

def start_fight(command_text=None):
    subprocess.run(["xdotool", "key", "space"])
    print("Combat lancé (espace pressé).")

# Fonction pour ouvrir le menu
def open_menu(command_text=None):
    subprocess.run(["xdotool", "key", "Escape"])
    print("Menu ouvert (touche Échappe pressée).")

# Fonction pour ouvrir les aptitudes
def open_aptitudes(command_text=None):
    subprocess.run(["xdotool", "key", "p"])
    print("Aptitudes ouvertes (touche P pressée).")

# Fonction pour ouvrir les sorts
def open_spells(command_text=None):
    subprocess.run(["xdotool", "key", "s"])
    print("Sorts ouverts (touche S pressée).")

# Fonction pour ouvrir le gestionnaire de build
def open_build_manager(command_text=None):
    subprocess.run(["xdotool", "key", "o"])
    print("Gestionnaire de build ouvert (touche O pressée).")

# Ouvrir l'inventaire
def open_inventory(command_text=None):
    subprocess.run(["xdotool", "key", "i"])
    print("Inventaire ouvert (touche i pressée).")

# Fonction pour ouvrir la carte
def open_map(command_text=None):
    subprocess.run(["xdotool", "key", "m"])
    print("Carte ouverte (touche M pressée).")

# Fonction pour ouvrir les héros
def open_heroes(command_text=None):
    subprocess.run(["xdotool", "key", "k"])
    print("Héros ouverts (touche K pressée).")

# Fonction pour ouvrir les métiers
def open_professions(command_text=None):
    subprocess.run(["xdotool", "key", "j"])
    print("Métiers ouverts (touche J pressée).")

# Fonctions pour les attaques (Barre 1 avec le pavé numérique)
def attack_one(command_text=None):
    subprocess.run(["xdotool", "key", "KP_End"])  # NumPad 1
    print("Attaque 1 exécutée (NumPad 1).")

def attack_two(command_text=None):
    subprocess.run(["xdotool", "key", "KP_Down"])  # NumPad 2
    print("Attaque 2 exécutée (NumPad 2).")

def attack_three(command_text=None):
    subprocess.run(["xdotool", "key", "KP_Next"])  # NumPad 3
    print("Attaque 3 exécutée (NumPad 3).")

def attack_four(command_text=None):
    subprocess.run(["xdotool", "key", "KP_Left"])  # NumPad 4
    print("Attaque 4 exécutée (NumPad 4).")

def attack_five(command_text=None):
    subprocess.run(["xdotool", "key", "KP_Begin"])  # NumPad 5
    print("Attaque 5 exécutée (NumPad 5).")

def attack_six(command_text=None):
    subprocess.run(["xdotool", "key", "KP_Right"])  # NumPad 6
    print("Attaque 6 exécutée (NumPad 6).")

# Fonctions pour les attaques (Barre 2 avec le pavé numérique et Shift)
def attack_seven(command_text=None):
    subprocess.run(["xdotool", "key", "Shift+KP_End"])  # Shift + NumPad 1
    print("Attaque 7 exécutée (Shift + NumPad 1).")

def attack_eight(command_text=None):
    subprocess.run(["xdotool", "key", "Shift+KP_Down"])  # Shift + NumPad 2
    print("Attaque 8 exécutée (Shift + NumPad 2).")

def attack_nine(command_text=None):
    subprocess.run(["xdotool", "key", "Shift+KP_Next"])  # Shift + NumPad 3
    print("Attaque 9 exécutée (Shift + NumPad 3).")

def attack_ten(command_text=None):
    subprocess.run(["xdotool", "key", "Shift+KP_Left"])  # Shift + NumPad 4
    print("Attaque 10 exécutée (Shift + NumPad 4).")

def attack_eleven(command_text=None):
    subprocess.run(["xdotool", "key", "Shift+KP_Begin"])  # Shift + NumPad 5
    print("Attaque 11 exécutée (Shift + NumPad 5).")

def attack_twelve(command_text=None):
    subprocess.run(["xdotool", "key", "Shift+KP_Right"])  # Shift + NumPad 6
    print("Attaque 12 exécutée (Shift + NumPad 6).")


# Fonction pour obtenir la taille de l'écran principal
def get_primary_screen_size():
    screen_width, screen_height = subprocess.check_output(["xdotool", "getdisplaygeometry"]).decode().strip().split()
    return int(screen_width), int(screen_height)

# Fonction pour déplacer le curseur au centre de l'écran
def move_cursor_center(command_text=None):
    screen_width, screen_height = get_primary_screen_size()
    subprocess.run(["xdotool", "mousemove", str(screen_width // 2), str(screen_height // 2)])
    print("Curseur déplacé au centre de l'écran principal.")

# Fonction pour déplacer le curseur à droite du centre
def move_cursor_right(command_text=None):
    screen_width, screen_height = get_primary_screen_size()
    subprocess.run(["xdotool", "mousemove", str(screen_width * 3 // 4), str(screen_height // 2)])
    print("Curseur déplacé à droite du centre sur l'écran principal.")

# Fonction pour déplacer le curseur à gauche du centre
def move_cursor_left(command_text=None):
    screen_width, screen_height = get_primary_screen_size()
    subprocess.run(["xdotool", "mousemove", str(screen_width // 4), str(screen_height // 2)])
    print("Curseur déplacé à gauche du centre sur l'écran principal.")

# Fonction pour déplacer le curseur en haut du centre
def move_cursor_up(command_text=None):
    screen_width, screen_height = get_primary_screen_size()
    subprocess.run(["xdotool", "mousemove", str(screen_width // 2), str(screen_height // 4)])
    print("Curseur déplacé en haut du centre sur l'écran principal.")

# Fonction pour déplacer le curseur en bas du centre
def move_cursor_down(command_text=None):
    screen_width, screen_height = get_primary_screen_size()
    subprocess.run(["xdotool", "mousemove", str(screen_width // 2), str(screen_height * 3 // 4)])
    print("Curseur déplacé en bas du centre sur l'écran principal.")

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

    # Augmenter ce facteur pour accélérer le curseur
    speed_x = abs(delta_x) * 400  # Au lieu de 300
    speed_y = abs(delta_y) * 400  # Au lieu de 300

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
            subprocess.run(["xdotool", "mousemove_relative", "--", str(-move_speed), "0"])
        elif move_direction == "right":
            subprocess.run(["xdotool", "mousemove_relative", "--", str(move_speed), "0"])
        elif move_direction == "up":
            subprocess.run(["xdotool", "mousemove_relative", "--", "0", str(-move_speed)])
        elif move_direction == "down":
            subprocess.run(["xdotool", "mousemove_relative", "--", "0", str(move_speed)])
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
                    
                    # Chercher des mots clés dans la commande reconnue
                    matched = False
                    for command, action in COMMANDS.items():
                        if all(word in recognized_text for word in command.split()):
                            # Démarrer un thread avec la commande reconnue
                            threading.Thread(target=globals()[action], args=(recognized_text,)).start()
                            matched = True
                            break

                    if not matched:
                        print("Commande non reconnue.")

                    if recognized_text in STOP_COMMANDS:
                        print("Commande de fin détectée : Arrêt du script...")
                        stop_cursor_move()

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

    # cv2.imshow('Eye Tracker', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

release_resources()
