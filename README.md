Ce script permet d'utiliser son ordinateur avec la voix et des mouvement de tête, probablement utile pour ceux qui n'ont plus une très motricité au niveau des bras.

Lancer la commande dans le fichier apt_commande.txt ( juste copié coller )
installer les truk nécessaire avec "pip install -r requirements.txt"
télécharger et décompresser le modèle vosk ( vosk-model-fr-0.22 ) dans le même dossier que le script ( https://alphacephei.com/vosk/models )
lancer le script avec la commande : python3 NovaNav_webcam_modulaire.py

le script a besoin d'une webcam et d'un micro pour fonctionner : lien du tuto et utilisation du script nova_commander : https://youtu.be/JRSw3fqL2iI

ne fonctionne que avec ubuntu 22.04 avec cette méthode , probalement possible de le faire fonctionner avec d'autre système linux mais j'ai pas essayer
Il faut lancer la sessions sur xorg pour que le script fonctionne !

02/09/2024 :
ajout du module wakfu pour jouer au jeu wakfu de ankama
  -pour que le module fonctionne il faut changer les raccourie du jeu par les numéro du numpad , pareil pour la barre d'action 2 shift + numéro du numpad
