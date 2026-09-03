import os
import json
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.utils import load_img, img_to_array


# =========================
# 1. Paths
# =========================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "plant_disease_model.h5"
)

CLASS_INDICES_PATH = os.path.join(
    BASE_DIR,
    "class_indices.json"
)

IMAGE_PATH = os.path.join(
    BASE_DIR,
    "test_images",
    "test.jpg"
)


# =========================
# 2. Basic settings
# =========================

IMG_SIZE = (224, 224)


# =========================
# 3. Load class names
# =========================

print("Loading class names...")

with open(CLASS_INDICES_PATH, "r") as f:
    class_indices = json.load(f)

num_classes = len(class_indices)

print("Number of classes:", num_classes)


# =========================
# 4. Create same model
# =========================

print("\nCreating MobileNetV2 model...")

base_model = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights=None
)

base_model.trainable = False


inputs = layers.Input(
    shape=(224, 224, 3)
)

x = tf.keras.applications.mobilenet_v2.preprocess_input(
    inputs
)

x = base_model(
    x,
    training=False
)

x = layers.GlobalAveragePooling2D()(x)

x = layers.Dropout(0.2)(x)

outputs = layers.Dense(
    num_classes,
    activation="softmax"
)(x)

model = models.Model(
    inputs,
    outputs
)


# =========================
# 5. Load trained weights
# =========================

print("\nLoading trained model weights...")

model.load_weights(MODEL_PATH)

print("Model weights loaded successfully!")


# =========================
# 6. Load test image
# =========================

print("\nLoading test image...")

if not os.path.exists(IMAGE_PATH):
    print("ERROR: test.jpg not found!")
    print("Expected location:")
    print(IMAGE_PATH)
    exit()

img = load_img(
    IMAGE_PATH,
    target_size=IMG_SIZE
)

img_array = img_to_array(img)

img_array = np.expand_dims(
    img_array,
    axis=0
)


# =========================
# 7. Prediction
# =========================

print("Making prediction...\n")

predictions = model.predict(
    img_array,
    verbose=1
)

predicted_index = int(
    np.argmax(predictions[0])
)

confidence = float(
    predictions[0][predicted_index]
)

predicted_class = class_indices[
    str(predicted_index)
]


# =========================
# 8. Result
# =========================

print("\n================================")
print("       PREDICTION RESULT")
print("================================")

print("Disease/Class :", predicted_class)

print(
    "Confidence    : {:.2f}%".format(
        confidence * 100
    )
)

print("================================")