import assemblyai as aai, asyncio, ldclient, os, validators
from flask import Flask, request
from ldclient import Context
from ldclient.config import Config


ld_sdk_key = os.getenv("LAUNCHDARKLY_SDK_KEY")
feature_flag_key = os.getenv("LAUNCHDARKLY_FLAG_KEY")
ldclient.set_config(Config(ld_sdk_key))

transcriber = aai.Transcriber()

app = Flask(__name__)


@app.route("/transcribe")
def email_transcription():
    email = request.args.get('email', '')
    if not validators.email(email):
        return "<h1>You need to specify a valid 'email' query parameter.</h1>"
    # specify the user and email to LaunchDarkly as a Context 
    context = Context.builder('transcript-app').kind('user')\
                                               .set("email", email).build()

    transcribe_url = request.args.get('url', '')
    if not validators.url(transcribe_url):
        return "<h1>You need to specify a valid 'url' query parameter.</h1>"

    # LaunchDarkly evaluates whether this is a high potential customer
    flag_value = ldclient.get().variation(feature_flag_key, context, False)
    # for most users, use the lower-cost option
    config = aai.TranscriptionConfig(speech_model="nano")
    if flag_value:
        # for high value potential customers, use highest transcription tier
        config = aai.TranscriptionConfig(speech_model="best")

    # uses ASSEMBLYAI_API_KEY from environment variables if set
    transcriber = aai.Transcriber(config=config)
    print(f"transcribing URL: {transcribe_url}")

    # this API can take awhile - typically done asynchronously
    transcript = transcriber.transcribe(transcribe_url)
    return f"<h1>Transcription</h1><p>{transcript.text}</p>"

