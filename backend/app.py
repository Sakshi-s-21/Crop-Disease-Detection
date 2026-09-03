import os
import sys
import json
import traceback

import numpy as np
import tensorflow as tf

from PIL import Image

from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    send_from_directory
)

# ============================================================
# PROJECT ROOT
# ============================================================

PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..")
)

sys.path.insert(0, PROJECT_ROOT)


# ============================================================
# CHATBOT IMPORT
# ============================================================

from chat.chatbot import get_chat_response


# ============================================================
# KERAS
# ============================================================

from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2


# ============================================================
# PATHS
# ============================================================

MODEL_PATH = os.path.join(
    PROJECT_ROOT,
    "plant_disease_model.h5"
)

CLASS_JSON = os.path.join(
    PROJECT_ROOT,
    "class_indices.json"
)

UPLOAD_FOLDER = os.path.join(
    PROJECT_ROOT,
    "frontend",
    "static",
    "uploads"
)


# ============================================================
# SETTINGS
# ============================================================

IMG_SIZE = (224, 224)

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(
    __name__,
    static_folder=os.path.join(
        PROJECT_ROOT,
        "frontend",
        "static"
    ),
    template_folder=os.path.join(
        PROJECT_ROOT,
        "frontend",
        "templates"
    )
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# ============================================================
# LOAD CLASS INDICES
# ============================================================

if not os.path.exists(CLASS_JSON):

    raise FileNotFoundError(
        f"class_indices.json not found:\n{CLASS_JSON}"
    )


with open(
    CLASS_JSON,
    "r",
    encoding="utf-8"
) as f:

    class_indices = json.load(f)


NUM_CLASSES = len(class_indices)


# ============================================================
# SERVER INFORMATION
# ============================================================

print("=" * 70)
print("CROP DISEASE DETECTION SERVER")
print("=" * 70)

print("Project root :", PROJECT_ROOT)
print("Model path   :", MODEL_PATH)
print("Class file   :", CLASS_JSON)
print("Classes      :", NUM_CLASSES)


# ============================================================
# BUILD EXACT MODEL ARCHITECTURE
# ============================================================

def build_model(num_classes):

    base_model = MobileNetV2(
        input_shape=(224, 224, 3),
        include_top=False,
        weights=None
    )

    base_model.trainable = False

    inputs = layers.Input(
        shape=(224, 224, 3)
    )

    # IMPORTANT:
    # Same preprocessing used during model testing
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

    return model


# ============================================================
# LOAD MODEL
# ============================================================

if not os.path.exists(MODEL_PATH):

    raise FileNotFoundError(
        f"Model file not found:\n{MODEL_PATH}"
    )


print()
print("Loading model...")

model = build_model(NUM_CLASSES)

model.load_weights(MODEL_PATH)

print("MODEL LOADED SUCCESSFULLY")

print(
    "Model size:",
    round(
        os.path.getsize(MODEL_PATH) / (1024 * 1024),
        2
    ),
    "MB"
)

print("=" * 70)


# ============================================================
# GET DISEASE NAME
# ============================================================

def get_disease_name(index):

    index = int(index)

    disease = class_indices.get(
        str(index),
        f"Unknown Class {index}"
    )

    return str(disease)


# ============================================================
# LANDING PAGE
# ============================================================

@app.route("/")
def home():

    return render_template(
        "landing.html"
    )


# ============================================================
# UPLOAD / ANALYSIS PAGE
# ============================================================

@app.route("/upload")
def upload_page():

    return render_template(
        "index.html"
    )


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/api/health")
def health():

    groq_configured = bool(
        os.getenv("GROQ_API_KEY")
    )

    return jsonify({

        "status": "ok",

        "model_loaded": model is not None,

        "model_exists": os.path.exists(
            MODEL_PATH
        ),

        "model_path": MODEL_PATH,

        "classes": NUM_CLASSES,

        "groq_configured": groq_configured

    })


# ============================================================
# PREDICTION API
# ============================================================

@app.route(
    "/api/predict",
    methods=["POST"]
)
def predict():

    try:

        # ====================================================
        # CHECK FILE
        # ====================================================

        if "file" not in request.files:

            return jsonify({
                "error": "No image file uploaded."
            }), 400


        file = request.files["file"]


        if file.filename == "":

            return jsonify({
                "error": "No image selected."
            }), 400


        # ====================================================
        # SAVE FILE
        # ====================================================

        filename = file.filename

        filepath = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        file.save(filepath)

        print()
        print("Image received :", filename)


        # ====================================================
        # OPEN IMAGE
        # ====================================================

        img = Image.open(
            filepath
        ).convert("RGB")

        img = img.resize(
            IMG_SIZE
        )


        # ====================================================
        # IMAGE ARRAY
        # ====================================================

        # IMPORTANT:
        # Do NOT divide by 255 here.
        #
        # MobileNetV2 preprocess_input()
        # is already inside the model.

        img_array = np.asarray(
            img,
            dtype=np.float32
        )

        img_array = np.expand_dims(
            img_array,
            axis=0
        )


        # ====================================================
        # PREDICTION
        # ====================================================

        prediction = model.predict(
            img_array,
            verbose=0
        )[0]


        top_idx = int(
            np.argmax(prediction)
        )

        confidence = float(
            prediction[top_idx]
        ) * 100


        # ====================================================
        # DISEASE NAME
        # ====================================================

        disease_raw = get_disease_name(
            top_idx
        )

        disease = disease_raw.replace(
            "_",
            " "
        )


        print(
            "Disease    :",
            disease
        )

        print(
            "Confidence :",
            f"{confidence:.2f}%"
        )


        # ====================================================
        # EXPERT ADVICE
        # ====================================================

        advice = get_chat_response(

            "Give practical treatment and prevention advice for this disease.",

            disease=disease_raw

        )


        # ====================================================
        # IMAGE URL
        # ====================================================

        image_url = (
            f"/static/uploads/{filename}"
        )


        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "success": True,

            "disease": disease,

            "disease_raw": disease_raw,

            "confidence": round(
                confidence,
                2
            ),

            "advice": advice,

            "image": image_url,

            "image_url": image_url

        })


    except Exception as e:

        print()
        print("=" * 70)
        print("PREDICTION ERROR")
        print("=" * 70)

        print(
            type(e).__name__,
            ":",
            str(e)
        )

        traceback.print_exc()

        print("=" * 70)


        return jsonify({

            "success": False,

            "error": str(e)

        }), 500


# ============================================================
# SERVE UPLOADED IMAGES
# ============================================================

@app.route(
    "/uploads/<filename>"
)
def uploaded_file(filename):

    return send_from_directory(
        UPLOAD_FOLDER,
        filename
    )


# ============================================================
# CHAT API
# ============================================================

@app.route(
    "/api/chat",
    methods=["POST"]
)
def chat():

    try:

        # ====================================================
        # GET JSON
        # ====================================================

        data = request.get_json(
            silent=True
        ) or {}


        # ====================================================
        # USER QUERY
        # ====================================================

        query = str(
            data.get(
                "query",
                ""
            )
        ).strip()


        if not query:

            return jsonify({

                "success": False,

                "response":
                    "Please type your question."

            }), 400


        # ====================================================
        # DISEASE
        # ====================================================

        disease = data.get(
            "disease"
        )


        # ====================================================
        # CHAT HISTORY
        # ====================================================

        history = data.get(
            "history",
            []
        )


        if not isinstance(
            history,
            list
        ):

            history = []


        # ====================================================
        # PRINT CHAT REQUEST
        # ====================================================

        print()
        print("=" * 70)
        print("CHAT REQUEST")
        print("Question :", query)
        print("Disease  :", disease)
        print("=" * 70)


        # ====================================================
        # CHATBOT
        # ====================================================

        response = get_chat_response(

            query=query,

            disease=disease,

            history=history

        )


        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "success": True,

            "response": response

        })


    except Exception as e:

        print()
        print("=" * 70)
        print("CHAT ERROR")
        print("=" * 70)

        print(
            type(e).__name__,
            ":",
            str(e)
        )

        traceback.print_exc()

        print("=" * 70)


        return jsonify({

            "success": False,

            "response":
                "Sorry, chatbot is temporarily unavailable."

        }), 500


# ============================================================
# RUN SERVER
# ============================================================

if __name__ == "__main__":

    print()
    print("=" * 70)
    print("Starting Flask server...")
    print("=" * 70)

    print()
    print("Landing page:")
    print(
        "http://127.0.0.1:5000/"
    )

    print()
    print("Upload / Analysis page:")
    print(
        "http://127.0.0.1:5000/upload"
    )

    print()
    print("Health check:")
    print(
        "http://127.0.0.1:5000/api/health"
    )

    print()
    print("Chat API:")
    print(
        "http://127.0.0.1:5000/api/chat"
    )

    print()
    print("=" * 70)


    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )