import functions_framework
import tempfile
import os
import vertexai
from vertexai.generative_models import GenerativeModel, Part, SafetySetting
from flask import jsonify


# Initialize Vertex AI
def init_vertex_ai():
    vertexai.init(project="airy-adapter-431519-f0", location="us-central1")


# Function to generate video description
def generate_video_description(video_uri):
    model = GenerativeModel("gemini-1.5-flash-001")

    # Prepare video part from URI
    video_part = Part.from_uri(mime_type="video/mp4", uri=video_uri)

    # Generation configuration
    generation_config = {
        "max_output_tokens": 8192,
        "temperature": 1,
        "top_p": 0.95,
    }

    # Safety settings to avoid inappropriate content
    safety_settings = [
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
        SafetySetting(
            category=SafetySetting.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        ),
    ]

    # Generate content (description) from the video
    responses = model.generate_content(
        [video_part, "write a detailed description for this video"],
        generation_config=generation_config,
        safety_settings=safety_settings,
        stream=True,
    )

    # Collect and return the generated text
    video_description = "".join([response.text for response in responses])
    return video_description


# HTTP Cloud Function to handle video upload and description generation
@functions_framework.http
def describe_video(request):
    # Ensure request has a file part
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files["file"]

    # Ensure a file is provided
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    # Create a temporary file to store the uploaded video
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_video:
        file.save(temp_video.name)
        temp_video.flush()
        video_path = temp_video.name

    try:
        # Initialize Vertex AI
        init_vertex_ai()

        # Upload the video to a Cloud Storage bucket for Vertex AI to access
        video_uri = upload_to_gcs(video_path)

        # Generate the video description
        description = generate_video_description(video_uri)

        # Return the description in JSON format
        return jsonify({"description": description}), 200

    finally:
        # Clean up the temporary file
        os.remove(video_path)


# Helper function to upload the video to a GCS bucket
from google.cloud import storage


def upload_to_gcs(local_path):
    # Define bucket name and file path
    bucket_name = "sample_video_gemini"
    destination_blob_name = os.path.basename(local_path)

    # Initialize Cloud Storage client
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    # Upload file
    blob.upload_from_filename(local_path)

    # Return the URI of the uploaded video
    return f"gs://{bucket_name}/{destination_blob_name}"
