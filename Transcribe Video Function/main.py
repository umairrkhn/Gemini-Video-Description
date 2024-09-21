import functions_framework
from google.cloud import videointelligence
from flask import jsonify, request


@functions_framework.http
def transcribe_video(request):
    """HTTP Cloud Function to transcribe speech from a video in GCS with each dialogue on a separate line."""

    if not request.json or "uri" not in request.json:
        return jsonify({"error": "No video URI provided"}), 400

    video_uri = request.json["uri"]

    video_client = videointelligence.VideoIntelligenceServiceClient()

    features = [videointelligence.Feature.SPEECH_TRANSCRIPTION]

    config = videointelligence.SpeechTranscriptionConfig(
        language_code="en-US",
        enable_automatic_punctuation=True,
        diarization_speaker_count=2,  # Adjust this based on expected number of speakers
    )

    video_context = videointelligence.VideoContext(speech_transcription_config=config)

    operation = video_client.annotate_video(
        request={
            "features": features,
            "input_uri": video_uri,
            "video_context": video_context,
        }
    )

    print("Processing video for speech transcription...")

    result = operation.result(timeout=600)

    annotation_results = result.annotation_results[0]
    transcript = []

    for speech_transcription in annotation_results.speech_transcriptions:
        for alternative in speech_transcription.alternatives:
            if len(alternative.words) > 0:
                speaker_tag = alternative.words[0].speaker_tag
                line = f"Speaker {speaker_tag}: {alternative.transcript}"
                transcript.append(line)

    formatted_transcript = "\n".join(transcript)

    return jsonify({"transcript": formatted_transcript}), 200
