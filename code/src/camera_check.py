# camera_check.py
import cv2

# 把 0 换成 20（或 21）
cap = cv2.VideoCapture('/dev/video20', cv2.CAP_V4L2)

while True:
    ret, frame = cap.read()
    if not ret:           # 避免空帧
        print("无法读取画面")
        break
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()