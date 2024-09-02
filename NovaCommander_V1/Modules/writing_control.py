import os
import subprocess
import threading
import sounddevice as sd
from vosk import Model, KaldiRecognizer
import json
import queue
import sys
import signal

# Chemin vers le modèle Vosk
MODEL_PATH = "vosk-model-fr-0.22"

# Commandes spécifiques pour le mode écriture et numpad
COMMANDS = {
    "efface le mot": "delete_last_word",
    "efface deux mots": "delete_two_words",
    "efface trois mots": "delete_three_words",
    "efface quatre mots": "delete_four_words",
    "efface cinq mots": "delete_five_words",
    "efface la lettre": "delete_last_letter",
    "efface deux lettres": "delete_two_letters",
    "efface trois lettres": "delete_three_letters",
    "efface quatre lettres": "delete_four_letters",
    "efface cinq lettres": "delete_five_letters",
    "appuyez sur entrée": "press_enter",
    "écrire": "write_text",
    "espace": "insert_space",
    "ferme le module d'écriture": "close_writing_module",
    "sélectionne tout": "select_all_text",
    "passe en mode numérique": "switch_to_numpad_mode",
    "passe en mode écriture normale": "switch_to_normal_mode",
    "insérez deux points": "insert_colon",
    "point": "insert_period",
    "virgule": "insert_comma",
    "arobase": "insert_at_symbol",
    "ouvrir parenthèse": "insert_parenthesis",
    "ouvrir guillemet": "insert_quotes",
    "ouvrir accolade": "insert_braces",
    "ouvrir crochet": "insert_brackets",
}

# Mapping des mots vers les chiffres pour le mode numpad
NUMBER_MAP_NUMPAD = {
    "zéro": "0",
    "un": "1",
    "deux": "2",
    "trois": "3",
    "quatre": "4",
    "cinq": "5",
    "six": "6",
    "sept": "7",
    "huit": "8",
    "neuf": "9",
}

# Mapping des mots vers les chiffres pour le mode écriture normale
NUMBER_MAP_NORMAL = {
    "un": "un ",
    "deux": "deux ",
    "trois": "trois ",
    "quatre": "quatre ",
    "cinq": "cinq ",
    "six": "six ",
    "sept": "sept ",
    "huit": "huit ",
    "neuf": "neuf ",
    "zéro": "zéro ",
}

# Mode actuel (par défaut en mode écriture normale)
current_mode = "normal"

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

# Fonction pour supprimer le dernier mot
def delete_last_word(command_text=None):
    subprocess.run(["xdotool", "key", "ctrl+BackSpace"])
    print("Dernier mot supprimé.")

# Fonction pour supprimer plusieurs mots
def delete_two_words(command_text=None):
    for _ in range(2):
        delete_last_word()

def delete_three_words(command_text=None):
    for _ in range(3):
        delete_last_word()

def delete_four_words(command_text=None):
    for _ in range(4):
        delete_last_word()

def delete_five_words(command_text=None):
    for _ in range(5):
        delete_last_word()

# Fonction pour supprimer la dernière lettre
def delete_last_letter(command_text=None):
    subprocess.run(["xdotool", "key", "BackSpace"])
    print("Dernière lettre supprimée.")

# Fonction pour supprimer plusieurs lettres
def delete_two_letters(command_text=None):
    for _ in range(2):
        delete_last_letter()

def delete_three_letters(command_text=None):
    for _ in range(3):
        delete_last_letter()

def delete_four_letters(command_text=None):
    for _ in range(4):
        delete_last_letter()

def delete_five_letters(command_text=None):
    for _ in range(5):
        delete_last_letter()

# Fonction pour appuyer sur la touche Entrée
def press_enter(command_text=None):
    subprocess.run(["xdotool", "key", "Return"])
    print("Entrée pressée.")

# Fonction pour insérer un espace
def insert_space(command_text=None):
    subprocess.run(["xdotool", "key", "space"])
    print("Espace inséré.")

# Fonction pour insérer un point
def insert_period(command_text=None):
    subprocess.run(["xdotool", "type", "."])
    print("Point inséré.")

# Fonction pour insérer une virgule
def insert_comma(command_text=None):
    subprocess.run(["xdotool", "type", ","])
    print("Virgule insérée.")

# Fonction pour insérer le symbole arobase (@)
def insert_at_symbol(command_text=None):
    subprocess.run(["xdotool", "type", "@"])
    print("Symbole @ inséré.")

# Fonction pour insérer un deux-points
def insert_colon(command_text=None):
    subprocess.run(["xdotool", "type", ":"])
    print("Deux-points insérés.")

# Fonction pour insérer une paire de parenthèses
def insert_parenthesis(command_text=None):
    subprocess.run(["xdotool", "type", "()"])
    subprocess.run(["xdotool", "key", "Left"])
    print("Parenthèses insérées.")

# Fonction pour insérer une paire de guillemets
def insert_quotes(command_text=None):
    subprocess.run(["xdotool", "type", "\"\""])
    subprocess.run(["xdotool", "key", "Left"])
    print("Guillemets insérés.")

# Fonction pour insérer une paire d'accolades
def insert_braces(command_text=None):
    subprocess.run(["xdotool", "type", "{}"])
    subprocess.run(["xdotool", "key", "Left"])
    print("Accolades insérées.")

# Fonction pour insérer une paire de crochets
def insert_brackets(command_text=None):
    subprocess.run(["xdotool", "type", "[]"])
    subprocess.run(["xdotool", "key", "Left"])
    print("Crochets insérés.")


# Fonction pour écrire du texte
def write_text(command_text):
    # Supprimer "écrire" du texte reconnu
    text_to_write = command_text.replace("écrire", "").strip()
    
    words = text_to_write.split()
    final_text = ""
    
    # Sélectionner le bon mapping en fonction du mode
    number_map = NUMBER_MAP_NUMPAD if current_mode == "numpad" else NUMBER_MAP_NORMAL
    
    for word in words:
        if word in number_map:
            final_text += number_map[word]
        else:
            final_text += word + " "
# Fonction pour passer en mode numpad
def switch_to_numpad_mode(command_text=None):
    global current_mode
    current_mode = "numpad"
    print("Mode numpad activé.")

# Fonction pour passer en mode écriture normale
def switch_to_normal_mode(command_text=None):
    global current_mode
    current_mode = "normal"
    print("Mode écriture normale activé.")

# Fonction pour fermer le module d'écriture
def close_writing_module(command_text=None):
    print("Fermeture du module d'écriture.")
    os.kill(os.getpid(), signal.SIGTERM)  # Terminer le processus actuel du script

# Fonction pour sélectionner tout le texte
def select_all_text(command_text=None):
    # Simule un triple clic pour sélectionner tout le texte
    subprocess.run(["xdotool", "click", "1"])
    subprocess.run(["xdotool", "click", "1"])
    subprocess.run(["xdotool", "click", "1"])
    print("Tout le texte a été sélectionné.")

# Fonction pour écouter les commandes vocales
def listen_for_commands():
    print("En mode écriture...")
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

if __name__ == "__main__":
    print("En attente du mode écriture...")
    listen_for_commands()
