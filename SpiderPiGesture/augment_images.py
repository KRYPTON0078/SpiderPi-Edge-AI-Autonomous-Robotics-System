import cv2
import os

# Only keep the gestures you want
gestures = ["stop", "thumbs_up", "point"]

def augment(img):
    augmented = []
    h, w = img.shape[:2]

    # Flip horizontally
    augmented.append(cv2.flip(img, 1))

    # Rotate +15 and -15 degrees
    M1 = cv2.getRotationMatrix2D((w//2, h//2), 15, 1)
    M2 = cv2.getRotationMatrix2D((w//2, h//2), -15, 1)
    augmented.append(cv2.warpAffine(img, M1, (w, h)))
    augmented.append(cv2.warpAffine(img, M2, (w, h)))

    # Brightness adjustments
    brighter = cv2.convertScaleAbs(img, alpha=1.2, beta=30)
    darker = cv2.convertScaleAbs(img, alpha=0.8, beta=-30)
    augmented.extend([brighter, darker])

    return augmented

for gesture in gestures:
    folder = f"dataset/{gesture}"
    for file in os.listdir(folder):
        path = os.path.join(folder, file)
        img = cv2.imread(path)
        if img is None: continue

        aug_images = augment(img)
        for i, aug in enumerate(aug_images):
            new_name = f"{file.split('.')[0]}_aug{i}.jpg"
            cv2.imwrite(os.path.join(folder, new_name), aug)

print("Augmentation complete!")
