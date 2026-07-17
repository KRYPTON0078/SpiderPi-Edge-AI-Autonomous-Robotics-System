import cv2
import os

gesture_name = "point"   # change this for each gesture
save_path = f"dataset/{gesture_name}"
os.makedirs(save_path, exist_ok=True)

cap = cv2.VideoCapture(0)
count = 0
max_images = 80   # small dataset

print(f"Collecting {max_images} images for gesture: {gesture_name}")
print("Press 'c' to capture, 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    cv2.imshow("Capture Gesture", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('c'):
        img_name = f"{gesture_name}_{count}.jpg"
        cv2.imwrite(os.path.join(save_path, img_name), frame)
        print(f"Saved {img_name}")
        count += 1

    if count >= max_images:
        print("Image collection complete.")
        break

    if key == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
