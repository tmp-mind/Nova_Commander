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
import keyboard  # Importation de keyboard au lieu de pyautogui
import pyautogui  # Importation de pyautogui

# Chemin vers le modèle Vosk
MODEL_PATH = "vosk-model-fr-0.22"
STOP_COMMANDS = ["stop", "curseur stop"]

# Commandes spécifiques pour le contrôle du jeu
COMMANDS = {
    "clic gauche": "mouse_click_left",
    "maintenir le clic": "mouse_hold_left",
    "relâche le clic": "mouse_release_left",
    "clic droit": "mouse_click_right",
    "double clic": "double_click",
    "molette haut": "scroll_up",
    "molette bas": "scroll_down",
    "flèche haut": "press_arrow_up",
    "flèche bas": "press_arrow_down",
    "flèche gauche": "press_arrow_left",
    "flèche droite": "press_arrow_right",
    "lance le combat": "start_fight",
    "passe mon tour": "start_fight",
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
    "attaque dix neuf": "attack_nineteen",
    "attaque vingt": "attack_twenty",
    "ouvre l'inventaire": "open_inventory",
    "ferme l'inventaire": "open_inventory",  # Fonctionnement toggle
    "curseur au centre": "move_cursor_center",
    "curseur à droite": "move_cursor_right",
    "curseur à gauche": "move_cursor_left",
    "curseur en haut": "move_cursor_up",
    "curseur en bas": "move_cursor_down",
    "ouvre les sorts": "open_spells",
    "ferme les sorts": "open_spells",  # Fonctionnement toggle
    "ouvre la carte": "open_map",
    "ferme la carte": "open_map",  # Fonctionnement toggle
    "ouvre les quêtes": "open_quest_book",
    "ferme les quêtes": "open_quest_book",
    "ouvre les métiers": "open_professions",
    "ferme les métiers": "open_professions",  # Fonctionnement toggle
    "ouvre le menu": "open_menu",
    "ferme le menu": "open_menu",  # Fonctionnement toggle
    "envoyer le message": "send_message",
    "barre d'action un": "open_page_one",
    "barre d'action deux": "open_page_two",
    "barre d'action trois": "open_page_three",
    "barre d'action quatre": "open_page_four",
    "barre d'action cinq": "open_page_five",
    "ouvre la feuille de personnage": "open_character_sheet",


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

# Initialisation des variables globales
move_direction = None
move_thread = None
cap = None
stop_threads = False
move_speed_x = 0
move_speed_y = 0

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

    # Appuyer sur 'Espace' pour ouvrir la boîte de dialogue du chat
    keyboard.press_and_release("space")
    
    # Extraire le texte à écrire après "envoyer le message"
    message_to_send = command_text.replace("envoyer le message", "").strip()
    
    if not message_to_send:
        print("Erreur : aucun message à envoyer.")
        return
    
    # Écrire le message dans la boîte de dialogue
    keyboard.write(message_to_send)
    print(f"Message écrit: {message_to_send}")
    
    # Attendre 2 secondes pour s'assurer que le message est bien écrit
    time.sleep(2)
    
    # Appuyer sur 'Entrée' pour envoyer le message
    keyboard.press_and_release("enter")
    
    # Attendre 0.5 secondes
    time.sleep(0.5)
    
    # Appuyer sur 'Échappe' pour fermer la boîte de dialogue
    keyboard.press_and_release("esc")
    
    print("Message envoyé.")

# Fonction pour arrêter le déplacement du curseur et fermer le script
def stop_cursor_move(command_text=None):
    global cursor_move_active
    cursor_move_active = False
    print("Mode de déplacement du curseur désactivé.")
    release_resources()
    sys.exit(0)  # Fermer le script proprement

# Fonction pour ouvrir/fermer le menu
def open_menu(command_text=None):
    keyboard.press_and_release('esc')
    print("Menu ouvert/fermé (touche Échappe pressée).")

# Fonction pour ouvrir/fermer le livre de quêtes
def open_quest_book(command_text=None):
    keyboard.press_and_release('q')
    print("Livre de quêtes ouvert/fermé (touche Q pressée).")

# Fonction pour ouvrir/fermer la feuille de personnage
def open_character_sheet(command_text=None):
    keyboard.press_and_release('c')
    print("Feuille de personnage ouverte/fermée (touche C pressée).")

# Fonction pour ouvrir la page 1 des raccourcis rapides
def open_page_one(command_text=None):
    keyboard.press_and_release('alt+&')
    print("Page 1 des raccourcis rapides ouverte (Alt + &).")

# Fonction pour ouvrir la page 2 des raccourcis rapides
def open_page_two(command_text=None):
    keyboard.press_and_release('alt+é')
    print("Page 2 des raccourcis rapides ouverte (Alt + é).")

# Fonction pour ouvrir la page 3 des raccourcis rapides
def open_page_three(command_text=None):
    keyboard.press_and_release('alt+"')
    print('Page 3 des raccourcis rapides ouverte (Alt + ").')

# Fonction pour ouvrir la page 4 des raccourcis rapides
def open_page_four(command_text=None):
    keyboard.press_and_release("alt+'")
    print("Page 4 des raccourcis rapides ouverte (Alt + ').")

# Fonction pour ouvrir la page 5 des raccourcis rapides
def open_page_five(command_text=None):
    keyboard.press_and_release('alt+(')
    print("Page 5 des raccourcis rapides ouverte (Alt + ().")


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

# Double clic gauche
def double_click(command_text=None):
    pyautogui.doubleClick()
    print("Double clic gauche effectué.")

# Fonction pour faire défiler vers le haut
def scroll_up(command_text=None):
    pyautogui.scroll(5)  # Défiler vers le haut
    print("Molette haut.")

# Fonction pour faire défiler vers le bas
def scroll_down(command_text=None):
    pyautogui.scroll(-5)  # Défiler vers le bas
    print("Molette bas.")

# Fonction pour appuyer sur la flèche haut
def press_arrow_up(command_text=None):
    keyboard.press_and_release('up')
    print("Flèche haut pressée.")

# Fonction pour appuyer sur la flèche bas
def press_arrow_down(command_text=None):
    keyboard.press_and_release('down')
    print("Flèche bas pressée.")

# Fonction pour appuyer sur la flèche gauche
def press_arrow_left(command_text=None):
    keyboard.press_and_release('left')
    print("Flèche gauche pressée.")

# Fonction pour appuyer sur la flèche droite
def press_arrow_right(command_text=None):
    keyboard.press_and_release('right')
    print("Flèche droite pressée.")

# Fonction pour ouvrir/fermer l'inventaire
def open_inventory(command_text=None):
    keyboard.press_and_release('i')
    print("Inventaire ouvert/fermé (touche I pressée).")

# Fonction pour ouvrir/fermer la carte
def open_map(command_text=None):
    keyboard.press_and_release('m')
    print("Carte ouverte/fermée (touche M pressée).")

# Fonction pour ouvrir/fermer les sorts
def open_spells(command_text=None):
    keyboard.press_and_release('s')
    print("Sorts ouverts/fermés (touche S pressée).")

# Fonction pour lancer le combat avec la touche F1
def start_fight(command_text=None):
    keyboard.press_and_release('F1')
    print("Combat lancé (touche F1 pressée).")

# Fonctions pour les attaques (Barre 1 avec les touches principales)
def attack_one(command_text=None):
    keyboard.press_and_release('&')
    print("Attaque 1 exécutée (Touche &).")

def attack_two(command_text=None):
    keyboard.press_and_release('é')
    print("Attaque 2 exécutée (Touche é).")

def attack_three(command_text=None):
    keyboard.press_and_release('"')
    print("Attaque 3 exécutée (Touche \").")

def attack_four(command_text=None):
    keyboard.press_and_release("'")
    print("Attaque 4 exécutée (Touche ').")

def attack_five(command_text=None):
    keyboard.press_and_release('(')
    print("Attaque 5 exécutée (Touche ().")

def attack_six(command_text=None):
    keyboard.press_and_release('-')
    print("Attaque 6 exécutée (Touche -).")

# Fonctions pour les attaques (Barre 2 avec Ctrl et les touches principales)
def attack_seven(command_text=None):
    keyboard.press_and_release('ctrl+&')
    print("Attaque 7 exécutée (Ctrl + Touche &).")

def attack_eight(command_text=None):
    keyboard.press_and_release('ctrl+é')
    print("Attaque 8 exécutée (Ctrl + Touche é).")

def attack_nine(command_text=None):
    keyboard.press_and_release('ctrl+"')
    print("Attaque 9 exécutée (Ctrl + Touche \").")

def attack_ten(command_text=None):
    keyboard.press_and_release("ctrl+'")
    print("Attaque 10 exécutée (Ctrl + Touche ').")

def attack_eleven(command_text=None):
    keyboard.press_and_release('ctrl+(')
    print("Attaque 11 exécutée (Ctrl + Touche ().")

def attack_twelve(command_text=None):
    keyboard.press_and_release('ctrl+-')
    print("Attaque 12 exécutée (Ctrl + Touche -).")

# Fonctions pour les attaques (Barre 3 avec Alt et les touches principales)
def attack_thirteen(command_text=None):
    keyboard.press_and_release('ctrl+&')
    print("Attaque 13 exécutée (Ctrl + Touche &).")

def attack_fourteen(command_text=None):
    keyboard.press_and_release('ctrl+é')
    print("Attaque 14 exécutée (Ctrl + Touche é).")

def attack_fifteen(command_text=None):
    keyboard.press_and_release('ctrl+"')
    print("Attaque 15 exécutée (Ctrl + Touche \").")

def attack_sixteen(command_text=None):
    keyboard.press_and_release("ctrl+'")
    print("Attaque 16 exécutée (Ctrl + Touche ').")

def attack_seventeen(command_text=None):
    keyboard.press_and_release('ctrl+(')
    print("Attaque 17 exécutée (Ctrl + Touche ().")

def attack_eighteen(command_text=None):
    keyboard.press_and_release('ctrl+-')
    print("Attaque 18 exécutée (Ctrl + Touche -).")

# Fonction pour attaque 19
def attack_nineteen(command_text=None):
    keyboard.press_and_release('ctrl+è')
    print("Attaque 19 exécutée (Ctrl + Touche è).")

# Fonction pour attaque 20
def attack_twenty(command_text=None):
    keyboard.press_and_release('ctrl+_')
    print("Attaque 20 exécutée (Ctrl + Touche _).")

# Fonction pour ouvrir/fermer les professions
def open_professions(command_text=None):
    keyboard.press_and_release('j')
    print("Métiers ouverts/fermés (touche J pressée).")

# Fonction pour déplacer le curseur au centre
def move_cursor_center(command_text=None):
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(screen_width // 2, screen_height // 2)
    print("Curseur déplacé au centre.")

# Fonction pour déplacer le curseur à droite
def move_cursor_right(command_text=None):
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(screen_width * 3 // 4, screen_height // 2)
    print("Curseur déplacé à droite.")

# Fonction pour déplacer le curseur à gauche
def move_cursor_left(command_text=None):
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(screen_width // 4, screen_height // 2)
    print("Curseur déplacé à gauche.")

# Fonction pour déplacer le curseur en haut
def move_cursor_up(command_text=None):
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(screen_width // 2, screen_height // 4)
    print("Curseur déplacé en haut.")

# Fonction pour déplacer le curseur en bas
def move_cursor_down(command_text=None):
    screen_width, screen_height = pyautogui.size()
    pyautogui.moveTo(screen_width // 2, screen_height * 3 // 4)
    print("Curseur déplacé en bas.")

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

def detect_head_direction(face_landmarks):
    global calibrated_center

    # Détection des mouvements de la tête
    left_eye_indices = [33, 160, 158, 133, 153, 144]
    right_eye_indices = [362, 385, 387, 263, 373, 380]

    # Calcul de la position des yeux
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

    speed_x = abs(delta_x) * 400  # Vitesse du curseur
    speed_y = abs(delta_y) * 400  # Vitesse du curseur

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

# Accéder à la webcam pour l'eye tracking avec l'API backend DirectShow
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

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

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

release_resources()
