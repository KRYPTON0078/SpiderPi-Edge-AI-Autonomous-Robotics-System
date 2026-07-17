import cv2, tensorflow as tf, numpy as np

# Load TFLite model
interpreter = tf.lite.Interpreter(model_path="gesture_model.tflite")
interpreter.allocate_tensors()
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

cap = cv2.VideoCapture(0)
gestures = ["stop","thumbs_up","point"]

print("✅ Webcam opened. Press 'q' to quit.")

while True:
    ret, frame = cap.read()
    if not ret:
        print("❌ Failed to grab frame.")
        break

    # Preprocess frame
    img = cv2.resize(frame,(64,64))/255.0
    img = np.expand_dims(img.astype('float32'),axis=0)

    # Run inference
    interpreter.set_tensor(input_details[0]['index'], img)
    interpreter.invoke()
    prediction = interpreter.get_tensor(output_details[0]['index'])
    gesture = np.argmax(prediction)

    # Display result
    cv2.putText(frame, f"Gesture: {gestures[gesture]}", (10,30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
    cv2.imshow("Gesture Recognition", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
