import tensorflow as tf
import os

print("🚀 Starting export...")

# Load the trained model
model = tf.keras.models.load_model("gesture_model.h5")
print("✅ Model loaded successfully")

# Convert to TensorFlow Lite
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()
print("✅ Conversion successful")

# Save the .tflite file
with open("gesture_model.tflite","wb") as f:
    f.write(tflite_model)

print("✅ gesture_model.tflite saved")
print("📂 Files in current directory:", os.listdir("."))
