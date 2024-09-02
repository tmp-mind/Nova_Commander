import os
import subprocess
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import queue
import sys
import threading

# Chemin vers le modèle Vosk
MODEL_PATH = "vosk-model-fr-0.22"

# Commandes spécifiques pour le contrôle du système d'exploitation
COMMANDS = {
    "lance": "launch_application",
    "ferme l'application": "close_application",
    "change de fenêtre": "switch_window",
    "ferme la fenêtre": "close_window",
    "ouvre le dossier": "open_folder",
    "ouvre les téléchargement": "open_downloads_folder",
    "crée un dossier": "create_folder",
    "supprime le fichier": "delete_file",
    "augmente le volume": "increase_volume",
    "baisse le volume": "decrease_volume",
    "augmente la luminosité": "increase_brightness",
    "baisse la luminosité": "decrease_brightness",
    "verrouille l'ordinateur": "lock_computer",
    "éteins l'ordinateur": "shutdown_computer",
    "redémarre l'ordinateur": "restart_computer",
    "ouvre les paramètres réseau": "open_network_settings",
    "ouvre les paramètres d'affichage": "open_display_settings",
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

# Fonction pour lancer une application
def launch_application(command_text):
    app_name = command_text.replace("lance", "").strip()
    print(f"Lancement de l'application {app_name}...")
    subprocess.Popen([app_name])

# Fonction pour fermer une application
def close_application(command_text):
    app_name = command_text.replace("ferme l'application", "").strip()
    print(f"Fermeture de {app_name}...")
    subprocess.run(["pkill", app_name])

# Fonction pour changer de fenêtre
def switch_window(command_text):
    window_name = command_text.replace("change de fenêtre", "").strip()
    if window_name:
        print(f"Changement de fenêtre vers {window_name}...")
        subprocess.run(["xdotool", "search", "--name", window_name, "windowactivate"])
    else:
        print("Changement de fenêtre active...")
        subprocess.run(["xdotool", "key", "Alt+Tab"])

# Fonction pour fermer la fenêtre active
def close_window(command_text=None):
    print("Fermeture de la fenêtre active...")
    subprocess.run(["xdotool", "key", "Alt+F4"])

# Fonction pour ouvrir un dossier
def open_folder(command_text):
    user_home = os.path.expanduser("~")
    folder_name = command_text.replace("ouvre le dossier", "").strip().lower()
    folder_path = os.path.join(user_home, folder_name.capitalize())

    if os.path.exists(folder_path):
        print(f"Ouverture du dossier {folder_name}...")
        subprocess.Popen(["xdg-open", folder_path])
    else:
        print(f"Le dossier {folder_name} n'existe pas.")

# Fonction dédiée pour ouvrir le dossier Téléchargements
def open_downloads_folder(command_text=None):
    user_home = os.path.expanduser("~")
    downloads_folder_path = os.path.join(user_home, "Téléchargements")

    if os.path.exists(downloads_folder_path):
        print("Ouverture du dossier Téléchargements...")
        subprocess.Popen(["xdg-open", downloads_folder_path])
    else:
        print("Le dossier Téléchargements n'existe pas.")

# Fonction pour créer un dossier
def create_folder(command_text):
    user_home = os.path.expanduser("~")
    folder_name = command_text.replace("crée un dossier", "").strip()
    folder_path = os.path.join(user_home, folder_name.capitalize())

    if not os.path.exists(folder_path):
        print(f"Création du dossier {folder_name}...")
        os.makedirs(folder_path)
    else:
        print(f"Le dossier {folder_name} existe déjà.")

# Fonction pour supprimer un fichier ou dossier
def delete_file(command_text):
    user_home = os.path.expanduser("~")
    file_name = command_text.replace("supprime le fichier", "").strip()
    file_path = os.path.join(user_home, file_name)

    if os.path.exists(file_path):
        print(f"Suppression du fichier/dossier {file_name}...")
        os.remove(file_path)
    else:
        print(f"Le fichier/dossier {file_name} n'existe pas.")

# Fonction pour augmenter le volume
def increase_volume(command_text=None):
    print("Augmentation du volume...")
    subprocess.run(["amixer", "sset", "Master", "10%+"])

# Fonction pour diminuer le volume
def decrease_volume(command_text=None):
    print("Diminution du volume...")
    subprocess.run(["amixer", "sset", "Master", "10%-"])

# Fonction pour augmenter la luminosité
def increase_brightness(command_text=None):
    print("Augmentation de la luminosité...")
    subprocess.run(["xbacklight", "-inc", "10"])

# Fonction pour diminuer la luminosité
def decrease_brightness(command_text=None):
    print("Diminution de la luminosité...")
    subprocess.run(["xbacklight", "-dec", "10"])

# Fonction pour verrouiller l'ordinateur
def lock_computer(command_text=None):
    print("Verrouillage de l'ordinateur...")
    subprocess.run(["gnome-screensaver-command", "-l"])

# Fonction pour éteindre l'ordinateur
def shutdown_computer(command_text=None):
    print("Extinction de l'ordinateur...")
    subprocess.run(["shutdown", "now"])

# Fonction pour redémarrer l'ordinateur
def restart_computer(command_text=None):
    print("Redémarrage de l'ordinateur...")
    subprocess.run(["reboot"])

# Fonction pour ouvrir les paramètres réseau
def open_network_settings(command_text=None):
    print("Ouverture des paramètres réseau...")
    subprocess.Popen(["gnome-control-center", "network"])

# Fonction pour ouvrir les paramètres d'affichage
def open_display_settings(command_text=None):
    print("Ouverture des paramètres d'affichage...")
    subprocess.Popen(["gnome-control-center", "display"])

# Fonction pour fermer le module système
def close_system_module(command_text=None):
    print("Fermeture du module système...")
    os._exit(0)

# Fonction pour écouter les commandes vocales
def listen_for_commands():
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
