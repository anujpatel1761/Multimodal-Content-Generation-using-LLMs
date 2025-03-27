from dotenv import load_dotenv
import os
import streamlit as st
import google.generativeai as genai
import replicate
from PIL import Image
import time

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize models
vision_model = genai.GenerativeModel("models/gemini-1.5-flash")
language_model = genai.GenerativeModel("models/gemini-1.5-pro-latest")

# Function to generate Gemini response
def get_gemini_response(prompt, image=None):
    if prompt and image:
        return vision_model.generate_content([prompt, image]).text
    elif prompt:
        return language_model.generate_content(prompt).text
    elif image:
        return vision_model.generate_content(image).text
    return ""

# Function to stream response word by word
def stream_data(prompt, image):
    sentences = get_gemini_response(prompt, image).split(". ")
    for sentence in sentences:
        for word in sentence.split():
            yield word + " "
            time.sleep(0.02)

# Streamlit page config
st.set_page_config(page_title="Multimodal Content Generation", layout="wide")

# Sidebar controls
st.sidebar.title("Multimodal Content Generation")
multimodal_mode = st.sidebar.radio("Select Task", ["Chat and Image Summarization", "Text 2 Image"])
st.sidebar.divider()

# ------------------------ Chat + Image Summarization ------------------------

if multimodal_mode == "Chat and Image Summarization":
    if st.sidebar.button("New Chat"):
        st.session_state["messages"] = []
        st.experimental_rerun()

    image = None
    with st.expander("Upload an image for summarization (optional)"):
        uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)

    chat_container = st.container()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display previous messages
    for msg in st.session_state.messages:
        with chat_container:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        with chat_container:
            with st.chat_message("user"):
                st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with chat_container:
            with st.chat_message("assistant"):
                response = get_gemini_response(prompt, image)
                if any(kw in prompt.lower() for kw in ["code", "python", "html", "css", "js", "react", "c++", "java"]):
                    st.code(response)
                else:
                    st.write_stream(stream_data(prompt, image))
                st.session_state.messages.append({"role": "assistant", "content": response})

# ------------------------------ Text to Image -------------------------------

def generate_and_display_image(submitted, width, height, num_outputs, scheduler, steps, prompt_strength, prompt):
    if REPLICATE_API_TOKEN.startswith('r8_') and submitted and prompt:
        with st.status("Generating your image...", expanded=True):
            try:
                output = replicate.run(
                    "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                    input={
                        "prompt": prompt,
                        "width": width,
                        "height": height,
                        "num_outputs": num_outputs,
                        "scheduler": scheduler,
                        "num_inference_steps": steps,
                        "guidance_scale": 7.5,
                        "prompt_strength": prompt_strength,
                        "negative_prompt": "worst quality, distorted features",
                        "refine": "expert_ensemble_refiner",
                        "high_noise_frac": 0.8
                    }
                )
                st.session_state.generated_image = output

                for image in output:
                    st.image(str(image), caption="Generated Image", use_container_width=True)

            except replicate.exceptions.ReplicateError as e:
                st.error(f"Error: {e}")
    elif not prompt:
        st.toast("Please enter a prompt.", icon="⚠️")


def refine_output():
    with st.expander("Refine your output if you want..."):
        width = st.number_input("Image Width", value=1024)
        height = st.number_input("Image Height", value=1024)
        num_outputs = st.slider("Number of Images", 1, 4, 1)
        scheduler = st.selectbox("Scheduler", ["DDIM", "DPMSolverMultistep", "HeunDiscrete", "KarrasDPM", "K_EULER_ANCESTRAL", "K_EULER", "PNDM"])
        steps = st.slider("Denoising Steps", 1, 500, 50)
        prompt_strength = st.slider("Prompt Strength", 0.1, 1.0, 0.8)
    prompt = st.text_input("Enter your prompt for the image:", value="Dog and cat dancing on moon")
    submitted = st.button("Generate")
    return submitted, width, height, num_outputs, scheduler, steps, prompt_strength, prompt

if multimodal_mode == "Text 2 Image":
    REPLICATE_API_TOKEN = st.sidebar.text_input("Enter your REPLICATE API TOKEN", type="password")
    os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

    if not REPLICATE_API_TOKEN.startswith("r8_"):
        st.warning("Please enter a valid Replicate API token.")
    else:
        submitted, width, height, num_outputs, scheduler, steps, prompt_strength, prompt = refine_output()
        generate_and_display_image(submitted, width, height, num_outputs, scheduler, steps, prompt_strength, prompt)
