import queue
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import threading
import json
import pyautogui
import sys
import time
import os

# Chemin vers le modèle Vosk pour la reconnaissance vocale
MODEL_PATH = "vosk-model-fr-0.22"
STOP_COMMANDS = ["fermez le module de messagerie"]

# Commandes pour la gestion du chat
CHAT_COMMANDS = {
    "envoyer le message": "send_message",
    "fermer le module de messagerie": "close_chat_module"
}

# Queue pour gérer les données audio
audio_queue = queue.Queue()

# Fonction de callback pour la reconnaissance vocale
def callback(indata, frames, time, status):
    if status:
        print(f"Status d'erreur dans le flux audio : {status}", file=sys.stderr)
    audio_queue.put(bytes(indata))

# Fonction pour envoyer un message dans le chat
def send_message(command_text=None):
    if not command_text:
        print("Erreur : aucun texte de commande n'a été fourni à la fonction send_message.")
        return

    try:
        # Appuyer sur 'Entrée' pour ouvrir la boîte de dialogue du chat
        pyautogui.press("enter")

        # Extraire le texte à écrire après "envoyer le message"
        message_to_send = command_text.replace("envoyer le message", "").strip()

        if not message_to_send:
            print("Erreur : aucun message à envoyer.")
            return

        # Écrire le message dans la boîte de dialogue
        pyautogui.typewrite(message_to_send)
        print(f"Message écrit: {message_to_send}")

        # Attendre 1 seconde pour s'assurer que le message est bien écrit
        time.sleep(1)

        # Appuyer sur 'Entrée' pour envoyer le message
        pyautogui.press("enter")
        pyautogui.press("enter")
        print("Message envoyé.")
    except Exception as e:
        print(f"Erreur lors de l'envoi du message : {e}")

# Fonction pour fermer le module de chat
def close_chat_module(command_text=None):
    print("Fermeture du module de chat.")
    sys.exit(0)  # Terminer le script proprement

# Fonction pour écouter les commandes vocales
def listen_for_chat_commands():
    print("En attente des commandes du module chat...")
    try:
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

                        matched = False
                        for command, action in CHAT_COMMANDS.items():
                            if command in recognized_text:
                                # Démarrer un thread avec la commande reconnue
                                threading.Thread(target=globals()[action], args=(recognized_text,)).start()
                                matched = True
                                break

                        if not matched:
                            print("Commande non reconnue.")

                        # Si une commande de fermeture est détectée, on arrête le module
                        if recognized_text in STOP_COMMANDS:
                            print("Commande de fin détectée : Fermeture du module chat...")
                            close_chat_module()
    except Exception as e:
        print(f"Erreur dans la fonction d'écoute des commandes chat : {e}")

# Vérification du modèle Vosk
try:
    if not os.path.exists(MODEL_PATH):
        print(f"Le modèle Vosk est introuvable dans {MODEL_PATH}. Veuillez vérifier le chemin.")
        sys.exit(1)
    else:
        print("Modèle Vosk trouvé.")
except Exception as e:
    print(f"Erreur lors de la vérification du modèle Vosk : {e}")
    sys.exit(1)

# Chargement du modèle de reconnaissance vocale
try:
    model = Model(MODEL_PATH)
    rec = KaldiRecognizer(model, 16000)
    print("Modèle Vosk chargé avec succès.")
except Exception as e:
    print(f"Erreur lors du chargement du modèle Vosk : {e}")
    sys.exit(1)

# Initialisation de l'entrée audio
try:
    # Démarrage du thread de reconnaissance vocale pour le module chat
    threading.Thread(target=listen_for_chat_commands, daemon=True).start()
    print("Thread de reconnaissance vocale démarré avec succès.")
    
    # Boucle principale pour garder le script actif
    while True:
        time.sleep(1)
except Exception as e:
    print(f"Erreur lors de l'initialisation du module chat : {e}")
    sys.exit(1)
