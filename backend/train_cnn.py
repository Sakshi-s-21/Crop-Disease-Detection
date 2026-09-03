import os
import json
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2

# =========================
# 1. Paths
# =========================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATASET_DIR = os.path.join(
    BASE_DIR,
    "dataset",
    "PlantVillage"
)

MODEL_PATH = os.path.join(
    BASE_DIR,
    "plant_disease_model.h5"
)

CLASS_INDICES_PATH = os.path.join(
    BASE_DIR,
    "class_indices.json"
)

# =========================
# 2. Basic settings
# =========================

IMG_SIZE = (224, 224)
BATCH_SIZE = 32
SEED = 42

# =========================
# 3. Load dataset
# =========================

print("Loading dataset...")

train_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="training",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

val_ds = tf.keras.utils.image_dataset_from_directory(
    DATASET_DIR,
    validation_split=0.2,
    subset="validation",
    seed=SEED,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE
)

class_names = train_ds.class_names
num_classes = len(class_names)

print("\nClasses:")
for i, class_name in enumerate(class_names):
    print(i, "->", class_name)

print("\nNumber of classes:", num_classes)

# =========================
# 4. Save class names
# =========================

class_indices = {
    str(i): class_name
    for i, class_name in enumerate(class_names)
}

with open(CLASS_INDICES_PATH, "w") as f:
    json.dump(class_indices, f, indent=4)

print("\nclass_indices.json created.")

# =========================
# 5. Improve performance
# =========================

AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.prefetch(buffer_size=AUTOTUNE)
val_ds = val_ds.prefetch(buffer_size=AUTOTUNE)

# =========================
# 6. Data augmentation
# =========================

data_augmentation = tf.keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.1),
    layers.RandomZoom(0.1),
])

# =========================
# 7. MobileNetV2
# =========================

base_model = MobileNetV2(
    input_shape=(224, 224, 3),
    include_top=False,
    weights="imagenet"
)

# Freeze pretrained layers
base_model.trainable = False

# =========================
# 8. Build model
# =========================

inputs = layers.Input(shape=(224, 224, 3))

x = data_augmentation(inputs)

x = tf.keras.applications.mobilenet_v2.preprocess_input(x)

x = base_model(x, training=False)

x = layers.GlobalAveragePooling2D()(x)

x = layers.Dropout(0.2)(x)

outputs = layers.Dense(
    num_classes,
    activation="softmax"
)(x)

model = models.Model(inputs, outputs)

# =========================
# 9. Compile model
# =========================

model.compile(
    optimizer="adam",
    loss="sparse_categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# =========================
# 10. Train model
# =========================

print("\nStarting training...\n")

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=10
)

# =========================
# 11. Save model
# =========================

model.save(MODEL_PATH)

print("\n===================================")
print("Training completed successfully!")
print("Model saved at:")
print(MODEL_PATH)

print("\nClass mapping saved at:")
print(CLASS_INDICES_PATH)

print("===================================")