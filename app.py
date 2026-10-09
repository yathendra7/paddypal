
import streamlit as st
import torch
from pathlib import Path
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

from auth import login_page, logout

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="PaddyPal",
    page_icon="🌾",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent

# -----------------------------
# Login / Signup
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    # Logo is handled in auth.py — do not render it again here.
    login_page()
    st.stop()

# -----------------------------
# Dashboard
# -----------------------------
from pathlib import Path
import streamlit as st

LOGO_PATH = Path(__file__).resolve().parent / "logo.png"

def show_centered_logo(width=220):
    if not LOGO_PATH.is_file():
        st.error(f"Logo file not found: {LOGO_PATH}")
        return

    st.image(
        str(LOGO_PATH),
        width=width
    )

st.title("🌾 PaddyPal")
st.subheader("AI-Based Rice Leaf Disease Detection")

logout()

st.write(
    f"Welcome, **{st.session_state.get('identifier', 'Farmer')}** 👋"
)

st.divider()

# -----------------------------
# Load Rice Disease Model
# -----------------------------
MODEL_NAME = "prithivMLmods/Rice-Leaf-Disease"


@st.cache_resource
def load_model():
    processor = AutoImageProcessor.from_pretrained(MODEL_NAME)
    model = AutoModelForImageClassification.from_pretrained(MODEL_NAME)
    model.eval()
    return processor, model


try:
    with st.spinner("Loading rice leaf disease model..."):
        processor, model = load_model()
except Exception as e:
    st.error(f"Could not load the AI model: {e}")
    st.info("Check your internet connection and model dependencies.")
    st.stop()

# -----------------------------
# Image Upload
# -----------------------------
st.write("### 🍃 Upload a Rice Leaf Image")

uploaded_file = st.file_uploader(
    "Choose a leaf image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    try:
        image = Image.open(uploaded_file).convert("RGB")

        left, center, right = st.columns([1, 2, 1])
        with center:
            st.image(
                image,
                caption="Uploaded Rice Leaf",
                use_container_width=True
            )

        # -----------------------------
        # AI Prediction
        # -----------------------------
        with st.spinner("Analyzing the leaf image..."):
            inputs = processor(images=image, return_tensors="pt")

            with torch.inference_mode():
                outputs = model(**inputs)
                probabilities = torch.softmax(
                    outputs.logits,
                    dim=-1
                )[0]

            predicted_index = int(probabilities.argmax().item())
            confidence = float(probabilities[predicted_index].item()) * 100

            id2label = model.config.id2label
            disease_name = id2label.get(
                predicted_index,
                str(predicted_index)
            )

        # -----------------------------
        # Results
        # -----------------------------
        st.divider()
        st.write("### 🔍 AI Prediction Results")

        result_left, result_center, result_right = st.columns(3)

        with result_center:
            st.metric("Predicted Class", disease_name)
            st.metric("Model Confidence", f"{confidence:.2f}%")

        st.caption(
            "This is an AI-generated prediction, not a confirmed diagnosis. "
            "Image quality and model limitations can affect results."
        )

        # -----------------------------
        # Other Possible Classes
        # -----------------------------
        st.write("### 📊 Other Possible Classes")

        top_count = min(3, len(probabilities))
        top_values, top_indices = torch.topk(
            probabilities,
            k=top_count
        )

        for probability, index in zip(
            top_values.tolist(),
            top_indices.tolist()
        ):
            label = id2label.get(index, str(index))
            st.write(f"**{label}** — {probability * 100:.2f}%")

        # -----------------------------
        # Basic Disease Guidance
        # -----------------------------
        st.write("### 🌱 Next Steps")

        disease_lower = disease_name.lower()

        if "healthy" in disease_lower:
            st.success(
                "The model classified this leaf as healthy. "
                "Continue regular field monitoring."
            )
        elif "bacterial" in disease_lower:
            st.info(
                "Possible bacterial disease detected. Check nearby plants "
                "and consult a local agricultural extension officer before "
                "choosing any treatment."
            )
        elif "blast" in disease_lower:
            st.info(
                "Possible rice blast detected. Inspect the crop carefully "
                "and seek local agricultural guidance on suitable management."
            )
        elif "brown spot" in disease_lower:
            st.info(
                "Possible brown spot detected. Review crop nutrition, field "
                "conditions and disease symptoms with an agricultural expert."
            )
        else:
            st.info(
                "Compare the prediction with visible symptoms and consult "
                "a local agricultural expert for confirmation and treatment advice."
            )

    except Exception as e:
        st.error(f"Could not analyze this image: {e}")

else:
    st.info("Upload a rice leaf image to get an AI prediction.")
