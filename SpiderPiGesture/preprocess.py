import cv2, os, numpy as np

# Only the gestures you kept
gestures = ["stop","thumbs_up","point"]
data, labels = [], []

for idx, gesture in enumerate(gestures):
    folder = f"dataset/{gesture}"
    for file in os.listdir(folder):
        img = cv2.imread(os.path.join(folder,file))
        if img is None: 
            continue
        # Resize to 64x64 and normalize pixel values
        img = cv2.resize(img,(64,64))/255.0
        data.append(img)
        labels.append(idx)

# Convert to numpy arrays
data, labels = np.array(data), np.array(labels)

# Save arrays for training
np.save("data.npy", data)
np.save("labels.npy", labels)

print("✅ Preprocessing complete! Data and labels saved.")
