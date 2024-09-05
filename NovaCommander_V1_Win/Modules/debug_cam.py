import cv2

cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Impossible d'ouvrir la webcam.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Impossible de recevoir le flux (déconnexion ?).")
        break

    cv2.imshow('frame', frame)
    if cv2.waitKey(1) == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
