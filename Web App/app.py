from flask import Flask, render_template, request, jsonify, url_for
import os

app = Flask(__name__)

# Placeholder for the video API URLs
VIDEO_API_URL = "http://video-api.com/transcript"
DESCRIPTION_API_URL = "http://video-api.com/description"


# Serve the HTML page
@app.route("/")
def index():
    return render_template("index.html")


# API to handle video upload and API interaction
@app.route("/upload_video", methods=["POST"])
def upload_video():
    video_file = request.files.get("video")

    if video_file:
        # Save the uploaded video temporarily
        video_path = os.path.join("static", "uploads", video_file.filename)
        video_file.save(video_path)

        # Placeholder response for transcript and description
        # These would be fetched from real APIs with `requests.post` or `requests.get`
        transcript = "This is a placeholder transcript for the uploaded video."
        description = "This is a placeholder description for the video content."

        # Return the video URL and placeholders for transcript and description
        return jsonify(
            {
                "video_url": url_for(
                    "static", filename=f"uploads/{video_file.filename}"
                ),
                "transcript": transcript,
                "description": description,
            }
        )
    else:
        return jsonify({"error": "No video file uploaded."}), 400


if __name__ == "__main__":
    os.makedirs(
        os.path.join("static", "uploads"), exist_ok=True
    )  # Create uploads directory
    app.run(debug=True)
