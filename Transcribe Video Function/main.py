import functions_framework
from google.cloud import videointelligence
from flask import jsonify, request


# Cloud Function to handle transcription
@functions_framework.http
def transcribe_video(request):
    """HTTP Cloud Function to transcribe speech from a video in GCS."""

    # Ensure the request contains a 'uri' key
    if not request.json or "uri" not in request.json:
        return jsonify({"error": "No video URI provided"}), 400

    video_uri = request.json["uri"]

    # Initialize Video Intelligence API client
    video_client = videointelligence.VideoIntelligenceServiceClient()

    # Set the features to include speech transcription
    features = [videointelligence.Feature.SPEECH_TRANSCRIPTION]

    # Configure speech transcription (set language and punctuation)
    config = videointelligence.SpeechTranscriptionConfig(
        language_code="en-US", enable_automatic_punctuation=True
    )

    video_context = videointelligence.VideoContext(speech_transcription_config=config)

    # Call the Video Intelligence API
    operation = video_client.annotate_video(
        request={
            "features": features,
            "input_uri": video_uri,
            "video_context": video_context,
        }
    )

    print("Processing video for speech transcription...")

    # Wait for the operation to complete
    result = operation.result(timeout=600)

    # Get the annotation results
    annotation_results = result.annotation_results[0]
    transcript = ""

    # Iterate through the transcriptions and collect the results
    for speech_transcription in annotation_results.speech_transcriptions:
        for alternative in speech_transcription.alternatives:
            transcript += alternative.transcript + " "

    # Return the transcription as a JSON response
    return jsonify({"transcript": transcript.strip()}), 200
