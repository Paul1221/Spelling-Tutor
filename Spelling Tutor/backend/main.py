import io

import requests
from google.cloud import datastore
import os
import flask
from flask_cors import CORS
import random
from flask import request
import hashlib

app = flask.Flask(__name__)
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "main-sunset-309509-f81d9789a11f.json"
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

@app.route('/TTS', methods=['POST'])
def TTS():
    import google.cloud.texttospeech as tts

    client = tts.TextToSpeechClient()

    myText = request.json['text'].lower()
    print(myText)
    synthesis_input = tts.SynthesisInput(text=myText)

    voice = tts.VoiceSelectionParams(
        language_code='en-US',
        ssml_gender=tts.SsmlVoiceGender.MALE
    )

    audio_config = tts.AudioConfig(
        audio_encoding=tts.AudioEncoding.LINEAR16
    )

    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    with open('file1.wav', 'wb') as outout:
        outout.write(response.audio_content)

    return flask.send_file(
        "./file1.wav",
        mimetype="audio/wav",
        as_attachment=True,
        download_name="file1.wav")


@app.route('/register', methods=['POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.json['name']
        password = hashlib.sha1(request.json['pass'].encode()).hexdigest()
        email = request.json['mail']
        result = query_datastore()
        print(username)
        print(password)
        print(email)
        # find email
        for entity in result:
            print(entity)
            if entity['email'] == email or entity['username'] == username:
                return {'r': "NOPE"}

        insert_in_datastore(email, username, password)

        query_datastore()
        return {'r': "LOGIN"}  # flask.render_template('login.html', error=error)
    # return flask.render_template('register.html', error=error)


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':

        username = request.json['name']
        password = hashlib.sha1(request.json['password'].encode()).hexdigest()
        result = query_datastore()

        for entity in result:
            if entity['username'] == username and entity['password'] == password:
                return {'r': "HOME"}  # flask.render_template('home.html')

        return {'r': "REGISTER"}  # flask.render_template('register.html')
    # return flask.render_template('login.html')


def open_datastore():
    client1 = datastore.Client()
    return client1


def insert_in_datastore(email, username, password):
    client = open_datastore()
    key = client.key("Users")
    task = datastore.Entity(key)

    task.update(
        {
            "email": email,
            "username": username,
            "password": password,
        }
    )
    client.put(task)


def query_datastore():
    client = open_datastore()
    query = client.query(kind="Users")
    results = list(query.fetch())
    print(results)
    return results


@app.route('/image', methods=['GET'])
def image():
    with open("Input.txt") as f:
        words = f.read().split("\n")

    image = words[random.randint(0, len(words))]

    subscription_key = "56260760288046aca76a9c0e15df1db4"
    search_url = "https://api.bing.microsoft.com/v7.0/images/search"

    headers = {"Ocp-Apim-Subscription-Key": subscription_key}

    params = {"q": image, "license": "public", "imageType": "photo"}

    response = requests.get(search_url, headers=headers, params=params)

    response.raise_for_status()
    search_results = response.json()
    thumbnail_urls = [search_results["value"][0]["thumbnailUrl"]]
    return {"image": image, 'url': thumbnail_urls[0]}


@app.route('/STT', methods=['POST'])
def STT():
    blob = flask.request.files['audio_data']  # such as `blob.read()`
    print(blob)
    with open('audio.wav', 'wb') as audio:
        blob.save(audio)
        print("OK")
    return transcribe_file()


def transcribe_file():
    """Transcribe the given audio file asynchronously."""
    from google.cloud import speech

    with io.open('audio.wav', "rb") as audio_file:
        content = audio_file.read()

    client = speech.SpeechClient()

    """
     Note that transcription is limited to a 60 seconds audio file.
     Use a GCS file for audio longer than 1 minute.
    """
    audio = speech.RecognitionAudio(content=content)

    config = speech.RecognitionConfig(language_code="en-US")

    operation = client.long_running_recognize(config=config, audio=audio)

    print("Waiting for operation to complete...")
    response = operation.result(timeout=90)

    # Each result is for a consecutive portion of the audio. Iterate through
    # them to get the transcripts for the entire audio file.
    for result in response.results:
        # The first alternative is the most likely one for this portion.
        print(result.alternatives[0].transcript)
        return result.alternatives[0].transcript


@app.route('/Check', methods=['POST'])
def Check():
    blob = flask.request.files['audio_data']  # such as blob.read()
    print(blob)
    with open('audio.wav', 'wb') as audio:
        blob.save(audio)
        print("OK")

    value = transcribe_file()

    command = "check"
    parameter = "text"
    service_id = "3C8nzDiGDwqKWGh"

    search_url = "https://svc.webspellchecker.net/spellcheck31/script/ssrv.fcgi?" \
                 f"cmd={command}&format=json&{parameter}={value}&out_type=words&slang=en_AI&user_dictionary=CC2&customerid={service_id}"

    response = requests.get(search_url)

    search_results = response.json()

    print(search_results)

    result = ""

    for word in search_results["result"]:
        if word["matches"]:
            for match in word["matches"]:
                nr = int(match["offset"])
                length = int(match["length"])
                result += f"You said it wrong this word: {value[nr:nr + length]}, You should say: {match['suggestions'][0]}<br>"
        else:
            result = "You said it correctly."
    print(result)

    return result


CORS(app)
app.run()
