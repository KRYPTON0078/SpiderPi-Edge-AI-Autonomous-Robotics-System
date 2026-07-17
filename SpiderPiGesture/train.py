import numpy as np
import tensorflow as tf
from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D, Flatten, Dense

# Load preprocessed data
try:
    data = np.load("data.npy", allow_pickle=True)
    labels = np.load("labels.npy", allow_pickle=True)
except FileNotFoundError:
    print("❌ data.npy or labels.npy not found. Run preprocess.py first.")
    exit()

print(f"Data shape: {data.shape}")
print(f"Labels shape: {labels.shape}")

# Define CNN model
model = Sequential([
    Conv2D(16,(3,3),activation='relu',input_shape=(64,64,3)),
    MaxPooling2D(2,2),
    Conv2D(32,(3,3),activation='relu'),
    MaxPooling2D(2,2),
    Flatten(),
    Dense(64,activation='relu'),
    Dense(3,activation='softmax')   # 3 gestures
])

# Compile
model.compile(optimizer='adam',
              loss='sparse_categorical_crossentropy',
              metrics=['accuracy'])

# Train
model.fit(data, labels, epochs=5, validation_split=0.2)

# Save
model.save("gesture_model.h5")
print("✅ Training complete! Model saved as gesture_model.h5")
