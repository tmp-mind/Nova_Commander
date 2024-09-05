import os
import subprocess
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import queue
import sys
import threading
import pyautogui
import ctypes

# Chemin vers le modèle Vosk
MODEL_PATH = "vosk-model-fr-0.22"

# Commandes spécifiques pour le contrôle du système d'exploitation
COMMANDS = {
    "ouvre les documents": "open_documents",
    "ouvre les musique": "open_music",
    "ouvre les images": "open_pictures",
    "ouvre le bureau": "open_desktop",
    "ouvre les vidéos": "open_videos",
    "ouvre les téléchargements": "open_downloads_folder",
    "crée un dossier": "create_folder",
    "augmente le volume": "increase_volume",
    "baisse le volume": "decrease_volume",
    "augmente la luminosité": "increase_brightness",
    "baisse la luminosité": "decrease_brightness",
    "verrouille l'ordinateur": "lock_computer",
    "éteins l'ordinateur": "shutdown_computer",
    "redémarre l'ordinateur": "restart_computer",
    "ferme la fenêtre": "close_window",
    "change de fenêtre": "switch_window",
    "ferme le module système": "close_system_module"
}

# Queue pour gérer les données audio
audio_queue = queue.Queue()

# Initialisation du modèle de reconnaissance vocale
if not os.path.exists(MODEL_PATH):
    print(f"Le modèle Vosk est introuvable dans {MODEL_PATH}. Veuillez vérifier le chemin.")
    sys.exit(1)

model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, 16000)

# Fonction de callback pour la reconnaissance vocale
def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

# Fonctions pour ouvrir les dossiers standards

def open_documents(command_text=None):
    """Ouvre le dossier Documents"""
    user_home = os.path.expanduser("~")
    documents_path = os.path.join(user_home, "Documents")
    print("Ouverture du dossier Documents...")
    subprocess.Popen(["explorer", documents_path])

def open_music(command_text=None):
    """Ouvre le dossier Musique"""
    user_home = os.path.expanduser("~")
    music_path = os.path.join(user_home, "Music")
    print("Ouverture du dossier Musique...")
    subprocess.Popen(["explorer", music_path])

def open_pictures(command_text=None):
    """Ouvre le dossier Images"""
    user_home = os.path.expanduser("~")
    pictures_path = os.path.join(user_home, "Pictures")
    print("Ouverture du dossier Images...")
    subprocess.Popen(["explorer", pictures_path])

def open_desktop(command_text=None):
    """Ouvre le dossier Bureau"""
    user_home = os.path.expanduser("~")
    desktop_path = os.path.join(user_home, "Desktop")
    print("Ouverture du dossier Bureau...")
    subprocess.Popen(["explorer", desktop_path])

def open_videos(command_text=None):
    """Ouvre le dossier Vidéos"""
    user_home = os.path.expanduser("~")
    videos_path = os.path.join(user_home, "Videos")
    print("Ouverture du dossier Vidéos...")
    subprocess.Popen(["explorer", videos_path])

def open_downloads_folder(command_text=None):
    """Ouvre le dossier Téléchargements"""
    user_home = os.path.expanduser("~")
    downloads_path = os.path.join(user_home, "Downloads")
    print("Ouverture du dossier Téléchargements...")
    subprocess.Popen(["explorer", downloads_path])

# Fonction pour créer un dossier dans Documents
def create_folder(command_text):
    """Crée un nouveau dossier dans le dossier Documents"""
    user_documents = os.path.join(os.path.expanduser("~"), "Documents")
    folder_name = command_text.replace("crée un dossier", "").strip()
    folder_path = os.path.join(user_documents, folder_name.capitalize())

    if not os.path.exists(folder_path):
        print(f"Création du dossier {folder_name} dans Documents...")
        os.makedirs(folder_path)
    else:
        print(f"Le dossier {folder_name} existe déjà dans Documents.")

# Fonction pour augmenter le volume
def increase_volume(command_text=None):
    """Augmente le volume sonore du système"""
    print("Augmentation du volume...")
    for _ in range(10):
        pyautogui.press("volumeup")

# Fonction pour diminuer le volume
def decrease_volume(command_text=None):
    """Diminue le volume sonore du système"""
    print("Diminution du volume...")
    for _ in range(10):
        pyautogui.press("volumedown")

# Fonction pour augmenter la luminosité
def increase_brightness(command_text=None):
    """Augmente la luminosité de l'écran"""
    print("Augmentation de la luminosité...")
    for _ in range(10):
        pyautogui.hotkey('fn', 'f3')

# Fonction pour diminuer la luminosité
def decrease_brightness(command_text=None):
    """Diminue la luminosité de l'écran"""
    print("Diminution de la luminosité...")
    for _ in range(10):
        pyautogui.hotkey('fn', 'f2')

# Fonction pour verrouiller l'ordinateur
def lock_computer(command_text=None):
    """Verrouille l'ordinateur"""
    print("Verrouillage de l'ordinateur...")
    ctypes.windll.user32.LockWorkStation()

# Fonction pour éteindre l'ordinateur
def shutdown_computer(command_text=None):
    """Éteint l'ordinateur"""
    print("Extinction de l'ordinateur...")
    subprocess.run(["shutdown", "/s", "/t", "0"])

# Fonction pour redémarrer l'ordinateur
def restart_computer(command_text=None):
    """Redémarre l'ordinateur"""
    print("Redémarrage de l'ordinateur...")
    subprocess.run(["shutdown", "/r", "/t", "0"])

# Fonction pour fermer la fenêtre active
def close_window(command_text=None):
    """Ferme la fenêtre active"""
    print("Fermeture de la fenêtre active...")
    pyautogui.hotkey('alt', 'f4')

# Fonction pour changer de fenêtre
def switch_window(command_text=None):
    """Change de fenêtre en utilisant Alt + Tab"""
    print("Changement de fenêtre...")
    pyautogui.hotkey('alt', 'tab')

# Fonction pour fermer le module système
def close_system_module(command_text=None):
    """Ferme le module de contrôle système"""
    print("Fermeture du module système...")
    os._exit(0)

# Fonction pour écouter les commandes vocales
def listen_for_commands():
    """Écoute les commandes vocales et les exécute"""
    print("En mode contrôle système...")
    with sd.RawInputStream(samplerate=16000, blocksize=8000, dtype='int16', channels=1, callback=callback):
        while True:
            try:
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
            except Exception as e:
                print(f"Erreur lors de l'écoute des commandes: {e}")
                continue

if __name__ == "__main__":
    listen_for_commands()
