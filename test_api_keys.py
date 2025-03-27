# Load environment variables from .env file
from dotenv import load_dotenv
import os
import google.generativeai as genai
import replicate

# Load .env and access keys
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# Check if both API keys are available
print("Checking API keys...")
print("GOOGLE_API_KEY:", "Loaded ✅" if GOOGLE_API_KEY else "Missing ❌")
print("REPLICATE_API_TOKEN:", "Loaded ✅" if REPLICATE_API_TOKEN else "Missing ❌")

# Test Gemini API
if GOOGLE_API_KEY:
    try:
        # Configure Gemini with your API key
        genai.configure(api_key=GOOGLE_API_KEY)

        # Print available models (for reference)
        print("\nAvailable Gemini Models:")
        for model in genai.list_models():
            print("-", model.name)

        # Initialize the Gemini 1.5 Pro model
        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-latest")

        # Run a basic test prompt
        response = model.generate_content("Say hello in 3 different languages.")
        print("\nGemini API Response:\n", response.text)
    except Exception as e:
        print("Gemini API Test Failed:", e)

# Test Replicate API
if REPLICATE_API_TOKEN:
    try:
        # Set environment variable for Replicate API
        os.environ["REPLICATE_API_TOKEN"] = REPLICATE_API_TOKEN

        # Run Stable Diffusion model
        output = replicate.run(
            "stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            input={
                "prompt": "a futuristic cityscape at sunset",
                "width": 512,
                "height": 512,
            }
        )

        # Extract URLs from output and print them
        image_urls = [str(img) for img in output]
        print("\nReplicate API Response:")
        for url in image_urls:
            print("Image URL:", url)

    except replicate.exceptions.ReplicateError as e:
        print("Replicate API Test Failed:", e)
    except Exception as e:
        print("Unexpected error with Replicate API:", e)
