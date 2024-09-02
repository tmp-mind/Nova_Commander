import os
import sys
import json
import queue
import subprocess
import threading
import sounddevice as sd
from vosk import Model, KaldiRecognizer
from TTS.api import TTS
import time

# Initialiser Coqui TTS avec un modèle anglais
tts = TTS(model_name="tts_models/en/ljspeech/vits", progress_bar=False, gpu=False)

# Chemin vers le modèle Vosk
MODEL_PATH = "vosk-model-fr-0.22"  # Assurez-vous de mettre le chemin correct

# Mot-clé d'activation et commandes en français
ACTIVATION_KEYWORD = "nova"  # Mot-clé pour activer les commandes vocales
COMMANDS = {
    "ouvre le navigateur": "open_browser",
    "ouvre youtube": "open_youtube",
    "cherche sur youtube": "search_youtube",
    "cherche sur google": "search_google",
    "sélectionne vidéo": "select_video",
    "active le module d'écriture": "start_writing_mode",
    "active le module du curseur": "start_cursor_move",
    "active le module système": "start_os_controller",
    "active le module wakfu": "start_wakfu_module",
    "curseur stop": "stop_cursor_move",
    "lire la vidéo": "play_selected_video",
    "pause la vidéo": "pause_video",
    "reprendre la vidéo": "play_video",
    "retour accueil youtube": "youtube_home",
    "ferme firefox": "close_firefox",
    "onglet un": "select_tab_one",
    "onglet deux": "select_tab_two",
    "onglet trois": "select_tab_three",
    "onglet quatre": "select_tab_four",
    "onglet cinq": "select_tab_five",
    "onglet six": "select_tab_six",
    "onglet sept": "select_tab_seven",
    "onglet huit": "select_tab_eight",
    "ouvre onglet": "open_tab",
    "ferme onglet": "close_tab",
    "cherche sur la page": "search_in_page",
    "valide la commande": "press_enter",
    "actualiser la page": "refresh_page",
    "cible le mot": "target_word"
}

# Queue pour gérer les données audio
audio_queue = queue.Queue()

# Fonction de callback pour la reconnaissance vocale
def callback(indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    audio_queue.put(bytes(indata))

def start_writing_mode(command_text=None):
    """Lance le script de contrôle du mode écriture dans un nouveau terminal"""
    speak("Starting writing mode.")
    
    # Définir le chemin du script de contrôle du mode écriture
    writing_script = os.path.join(os.path.dirname(__file__), 'Modules', 'writing_control.py')
    
    # Lancer le script dans un nouveau terminal
    subprocess.Popen(["gnome-terminal", "--", "python3", writing_script])
    
    # Utiliser xdotool pour minimiser la dernière fenêtre (le terminal nouvellement ouvert)
    time.sleep(1)  # Attendre que le terminal soit lancé
    subprocess.run(["xdotool", "getactivewindow", "windowminimize"])
    
    speak("Writing mode activated.")

def start_os_controller(command_text=None):
    """Lance le module de contrôle du système d'exploitation dans un nouveau terminal"""
    speak("Starting system control module.")
    
    # Définir le chemin du script de contrôle du système
    os_controller_script = os.path.join(os.path.dirname(__file__), 'Modules', 'OS_Controller.py')
    
    # Lancer le script dans un nouveau terminal
    subprocess.Popen(["gnome-terminal", "--", "python3", os_controller_script])
    
    # Utiliser xdotool pour minimiser la dernière fenêtre (le terminal nouvellement ouvert)
    time.sleep(1)  # Attendre que le terminal soit lancé
    subprocess.run(["xdotool", "getactivewindow", "windowminimize"])
    
    speak("System control module activated.")

def speak(text, delay_after=1.5):
    """Utilise Coqui TTS pour parler en anglais et joue le fichier audio avec un délai après la lecture"""
    output_file = "output_en.wav"
    tts.tts_to_file(text=text, file_path=output_file)
    subprocess.run(["aplay", output_file])
    os.remove(output_file)  # Supprimer le fichier temporaire après utilisation
    time.sleep(delay_after)  # Attendre la fin de lecture pour éviter d'enregistrer le son

def open_browser(command_text=None):
    """Ouvre le navigateur web par défaut et informe l'utilisateur"""
    subprocess.Popen(["firefox"])
    speak("The web browser has been opened.")

def open_youtube(command_text=None):
    """Ouvre YouTube dans Firefox et informe l'utilisateur"""
    subprocess.Popen(["firefox", "https://www.youtube.com"])
    speak("YouTube has been opened.")

def search_youtube(command_text):
    """Recherche sur YouTube en ajoutant directement les mots-clés"""
    search_query = command_text.replace("cherche sur youtube", "").strip()
    if search_query:
        url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
        subprocess.Popen(["firefox", url])
        speak(f"Searching YouTube for {search_query}.")
    else:
        speak("No search query provided.")

def search_google(command_text):
    """Recherche sur Google en ajoutant directement les mots-clés"""
    search_query = command_text.replace("cherche sur google", "").strip()
    if search_query:
        url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        subprocess.Popen(["firefox", url])
        speak(f"Searching Google for {search_query}.")
    else:
        speak("No search query provided.")

def youtube_home(command_text=None):
    """Retourner à la page d'accueil de YouTube"""
    subprocess.Popen(["firefox", "https://www.youtube.com"])
    speak("Returning to YouTube home.")

def start_wakfu_module(command_text=None):
    """Lance le script de contrôle du curseur pour le jeu Wakfu dans un nouveau terminal, puis le minimise."""
    speak("Launching cursor games control.")
    
    # Définir le chemin du script de contrôle du curseur pour le jeu Wakfu
    cursor_script = os.path.join(os.path.dirname(__file__), 'Modules', 'cursor_games.py')
    
    # Lancer le script dans un nouveau terminal
    subprocess.Popen(["gnome-terminal", "--", "python3", cursor_script])
    
    # Utiliser xdotool pour minimiser la dernière fenêtre (le terminal nouvellement ouvert)
    time.sleep(3)  # Attendre que le terminal soit lancé
    subprocess.run(["xdotool", "getactivewindow", "windowminimize"])
    
    speak("Cursor control finished.")



def start_cursor_move(command_text=None):
    """Lance le script de contrôle du curseur dans un nouveau terminal, puis le minimise"""
    speak("Launching cursor control.")
    
    # Définir le chemin du script de contrôle du curseur
    cursor_script = os.path.join(os.path.dirname(__file__), 'Modules', 'cursor_control.py')
    
    # Lancer le script dans un nouveau terminal
    subprocess.Popen(["gnome-terminal", "--", "python3", cursor_script])
    
    # Utiliser xdotool pour minimiser la dernière fenêtre (le terminal nouvellement ouvert)
    time.sleep(3)  # Attendre que le terminal soit lancé
    subprocess.run(["xdotool", "getactivewindow", "windowminimize"])
    
    speak("Cursor control finished.")

def stop_cursor_move(command_text=None):
    """Cette commande arrête le script de contrôle du curseur (qui se termine automatiquement)"""
    speak("Cursor movement mode deactivated.")

def refresh_page(command_text=None):
    """Actualise la page web active"""
    subprocess.run(["xdotool", "key", "F5"])
    speak("Page refreshed.")

def search_in_page(command_text=None):
    """Ouvre la boîte de dialogue de recherche et entre le texte recherché"""
    search_query = command_text.replace("cherche sur la page", "").strip()
    if search_query:
        subprocess.run(["xdotool", "key", "ctrl+f"])
        subprocess.run(["xdotool", "type", search_query])
        speak(f"Searching for {search_query} on the page.")
    else:
        speak("No search query provided.")

def target_word(command_text=None):
    """Cible un mot sur la page en le recherchant puis en positionnant le curseur"""
    word_to_target = command_text.replace("cible le mot", "").strip()
    if word_to_target:
        # Recherche du mot sur la page
        subprocess.run(["xdotool", "key", "ctrl+f"])
        subprocess.run(["xdotool", "type", word_to_target])
        subprocess.run(["xdotool", "key", "Return"])  # Valide la recherche
        speak(f"Targeting the word {word_to_target}.")
        # Ferme la recherche pour éviter des effets indésirables
        subprocess.run(["xdotool", "key", "Escape"])
    else:
        speak("No word provided to target.")

def select_tab_one(command_text=None):
    """Sélectionne l'onglet 1"""
    subprocess.run(["xdotool", "key", "Alt+1"])
    speak("Tab one selected.")

def select_tab_two(command_text=None):
    """Sélectionne l'onglet 2"""
    subprocess.run(["xdotool", "key", "Alt+2"])
    speak("Tab two selected.")

def select_tab_three(command_text=None):
    """Sélectionne l'onglet 3"""
    subprocess.run(["xdotool", "key", "Alt+3"])
    speak("Tab three selected.")

def select_tab_four(command_text=None):
    """Sélectionne l'onglet 4"""
    subprocess.run(["xdotool", "key", "Alt+4"])
    speak("Tab four selected.")

def select_tab_five(command_text=None):
    """Sélectionne l'onglet 5"""
    subprocess.run(["xdotool", "key", "Alt+5"])
    speak("Tab five selected.")

def select_tab_six(command_text=None):
    """Sélectionne l'onglet 6"""
    subprocess.run(["xdotool", "key", "Alt+6"])
    speak("Tab six selected.")

def select_tab_seven(command_text=None):
    """Sélectionne l'onglet 7"""
    subprocess.run(["xdotool", "key", "Alt+7"])
    speak("Tab seven selected.")

def select_tab_eight(command_text=None):
    """Sélectionne l'onglet 8"""
    subprocess.run(["xdotool", "key", "Alt+8"])
    speak("Tab eight selected.")

def open_tab(command_text=None):
    """Ouvre un nouvel onglet dans le navigateur"""
    subprocess.run(["xdotool", "key", "Ctrl+t"])
    speak("New tab opened.")

def close_tab(command_text=None):
    """Ferme l'onglet actuel"""
    subprocess.run(["xdotool", "key", "Ctrl+w"])
    speak("Tab closed.")

def press_enter(command_text=None):
    """Valide la commande"""
    subprocess.run(["xdotool", "key", "Return"])
    speak("Command validated.")

# Queue pour gérer les données audio
audio_queue = queue.Queue()

# Fonction pour écouter le mot-clé d'activation
def listen_for_keyword():
    print(f"En attente du mot-clé '{ACTIVATION_KEYWORD}'...")
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
                    if ACTIVATION_KEYWORD in recognized_text:
                        print("Mot-clé détecté : Activation de l'écoute...")
                        return  # Quitter pour commencer l'écoute de la commande

# Fonction pour écouter et exécuter les commandes
def listen_for_command():
    print("Démarrage de l'écoute de la commande...")

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
                            matched = True
                            threading.Thread(target=globals()[action], args=(command_text,)).start()
                            break

                    if not matched:
                        print("Commande non reconnue.")
                        return  # Retourner à l'écoute du mot-clé sans boucler sur l'erreur

# Vérification du modèle Vosk
if not os.path.exists(MODEL_PATH):
    print(f"Le modèle Vosk est introuvable dans {MODEL_PATH}. Veuillez vérifier le chemin.")
    sys.exit(1)

# Chargement du modèle Vosk
model = Model(MODEL_PATH)
rec = KaldiRecognizer(model, 16000)

# Boucle principale
while True:
    listen_for_keyword()
    listen_for_command()
