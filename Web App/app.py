from flask import Flask, render_template, request, jsonify
import requests
from google.cloud import storage
import os

app = Flask(__name__)

# Set the environment variable for Google Cloud service account key
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "airy-adapter-431519-f0-96dd9e4b1f19.json"

# API endpoints
description_api = (
    "https://us-central1-airy-adapter-431519-f0.cloudfunctions.net/describe_video"
)
transcription_api = (
    "https://us-central1-airy-adapter-431519-f0.cloudfunctions.net/transcribe_video"
)

# Temporary storage for API results
api_results = {"video_url": "", "transcript": "", "description": ""}


# Initialize Google Cloud Storage client
def get_signed_url(gs_uri, expiration_time=3600):
    # gs://bucket_name/object_name
    if not gs_uri.startswith("gs://"):
        raise ValueError("Invalid GCS URI")

    bucket_name, object_name = gs_uri.replace("gs://", "").split("/", 1)

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    # Generate a signed URL for temporary access
    signed_url = blob.generate_signed_url(expiration=expiration_time)

    return signed_url


# Index route to render the video upload page
@app.route("/")
def index():
    return render_template("index.html")


# Route for displaying the result page once both API calls are done
@app.route("/result")
def result():
    return render_template(
        "result.html",
        video_url=api_results["video_url"],
        transcript=api_results["transcript"],
        description=api_results["description"],
    )


# Handle the video upload, process with APIs, and redirect to the result page
@app.route("/upload_video", methods=["POST"])
def upload_video():
    video_file = request.files.get("video")

    if video_file:
        # Send video to description API
        files = {"file": video_file}
        description_response = requests.post(description_api, files=files)

        if description_response.status_code == 200:
            description_data = description_response.json()
            video_uri = description_data["video_uri"]
            api_results["description"] = description_data["description"]

            # Call transcription API using the video URI from the description response
            transcription_response = requests.post(
                transcription_api, json={"uri": video_uri}
            )

            if transcription_response.status_code == 200:
                transcription_data = transcription_response.json()
                api_results["transcript"] = transcription_data["transcript"]

                # Generate a signed URL for the video file from the video URI
                try:
                    signed_url = get_signed_url(video_uri)
                    api_results["video_url"] = signed_url
                except ValueError as e:
                    return jsonify({"status": "error", "error": str(e)})

                # Once both APIs are successful, redirect to result page
                return jsonify({"status": "success"})
            else:
                return jsonify({"status": "error", "error": "Transcription API failed"})
        else:
            return jsonify({"status": "error", "error": "Description API failed"})
    else:
        return jsonify({"status": "error", "error": "No video file uploaded"}), 400


if __name__ == "__main__":
    app.run(debug=True)
