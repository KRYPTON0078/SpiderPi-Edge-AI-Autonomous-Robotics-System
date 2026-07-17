import tensorflow as tf
import os

print("🔍 Starting export...")

# Check if gesture_model.h5 exists
if not os.path.exists("gesture_model.h5"):
    print("❌ gesture_model.h5 not found. Run train.py first.")
    exit()

print("✅ gesture_model.h5 found")

# Try loading the model
model = tf.keras.models.load_model("gesture_model.h5")
print("✅ Model loaded successfully")

# Convert to TensorFlow Lite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
print("✅ Conversion successful")

# Save the file
with open("gesture_model.tflite","wb") as f:
    f.write(tflite_model)

print("✅ gesture_model.tflite saved")
print("📂 Files in current directory:", os.listdir("."))
