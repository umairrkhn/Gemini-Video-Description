from flask import Flask, render_template, request, jsonify, url_for
import requests
import os
from werkzeug.utils import secure_filename
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# API endpoints
description_api = (
    "https://us-central1-airy-adapter-431519-f0.cloudfunctions.net/describe_video"
)
transcription_api = (
    "https://us-central1-airy-adapter-431519-f0.cloudfunctions.net/transcribe_video"
)

# Temporary storage for API results
api_results = {"video_filename": "", "transcript": "", "description": ""}

# Ensure the upload directory exists
UPLOAD_FOLDER = os.path.join("static", "videos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Index route to render the video upload page
@app.route("/")
def index():
    return render_template("index.html")


# Route for displaying the result page once both API calls are done
@app.route("/result")
def result():
    video_url = url_for("static", filename=f'videos/{api_results["video_filename"]}')
    app.logger.debug(f"Video URL: {video_url}")
    return render_template(
        "result.html",
        video_url=video_url,
        transcript=api_results["transcript"],
        description=api_results["description"],
    )


# Handle the video upload, process with APIs, and redirect to the result page
@app.route("/upload_video", methods=["POST"])
def upload_video():
    video_file = request.files.get("video")

    if video_file:
        try:
            # Save the video file locally
            filename = secure_filename(video_file.filename)
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            video_file.save(filepath)
            app.logger.info(f"Video saved to {filepath}")

            # Send video to description API
            with open(filepath, "rb") as f:
                files = {"file": f}
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

                    # Store the video filename for display
                    api_results["video_filename"] = filename

                    # Once both APIs are successful, redirect to result page
                    return jsonify({"status": "success"})
                else:
                    app.logger.error(
                        f"Transcription API failed: {transcription_response.text}"
                    )
                    return jsonify(
                        {"status": "error", "error": "Transcription API failed"}
                    )
            else:
                app.logger.error(f"Description API failed: {description_response.text}")
                return jsonify({"status": "error", "error": "Description API failed"})
        except Exception as e:
            app.logger.error(f"Error processing video: {str(e)}")
            return jsonify({"status": "error", "error": str(e)}), 500
    else:
        return jsonify({"status": "error", "error": "No video file uploaded"}), 400


if __name__ == "__main__":
    app.run(debug=True)
