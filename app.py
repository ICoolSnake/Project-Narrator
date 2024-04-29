import os
import threading
from urllib import request
import cv2
import time
import numpy as np
import openai
import base64
import errno
import logging
import langdetect
from PIL import Image
from elevenlabs import generate, set_api_key
from flask import Flask, render_template, Response, send_from_directory, session, jsonify, request, copy_current_request_context
from threading import Thread
from dotenv import load_dotenv

load_dotenv()
folder = "frames"
frames_dir = os.path.join(os.getcwd(), folder)
os.makedirs(frames_dir, exist_ok=True)
audio_files = []
lock = threading.Lock()

openai.api_key = os.getenv('OPENAI_API_KEY')
set_api_key(os.getenv('ELEVENLABS_API_KEY'))


def capture_and_process_image(cap):
    ret, frame = cap.read()
    if ret:
        pil_img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

        max_size = 250
        ratio = max_size / max(pil_img.size)
        if len(pil_img.size) == 2:
            new_size = tuple([int(x * ratio) for x in pil_img.size])
            resized_img = pil_img.resize(new_size, Image.LANCZOS)
        else:
            raise ValueError("Unexpected image size")

        frame = cv2.cvtColor(np.array(resized_img), cv2.COLOR_RGB2BGR)

        path = os.path.join(frames_dir, "frame.jpeg")
        cv2.imwrite(path, frame)
        return path
    else:
        return None


def encode_image(image_path):
    while True:
        try:
            with open(image_path, "rb") as image_file:
                return base64.b64encode(image_file.read()).decode('utf-8')
        except IOError as e:
            if e.errno != errno.EACCES:
                raise
            time.sleep(0.1)


def play_audio(text):
    global audio_files
    with lock:

        voice_id = session.get('voice_id', 'Change with the default voice ID')

        audio = generate(text, voice=voice_id)

        unique_id = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8").rstrip("=")
        dir_path = os.path.join("static/Audio Files", unique_id)
        os.makedirs(dir_path, exist_ok=True)
        file_path = os.path.join(dir_path, "audio.wav")

        with open(file_path, "wb") as f:
            f.write(audio)

        audio_files.clear()
        audio_files.append(unique_id)
        print(f"New audio generated and available in {dir_path}")


def generate_message(base64_image):
    return [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Describe this image"
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{base64_image}"
                },
            ],
        },
    ]


def analyse(base64_image, script, language):
    voice_id = session.get('voice_id', 'Change with the default voice ID')
    language_map = {'German': 'de', 'Turkish': 'tr'}
    iso_language = language_map.get(language, 'en')

    system_content = ""
    if voice_id == 'Change with the first Voice ID option':
        if language == 'German':
            system_content = """Sie sind Sir David Attenborough. Erzählen Sie das Bild des Menschen, als wäre es eine Naturdokumentation.
                                Machen Sie es spöttisch und lustig. Wiederholen Sie sich nicht. Halten Sie es kurz. Maximum 20 Wörter. Beenden Sie Ihre Sätze jedes Mal.
                                Zum Beispiel: Hier sehen wir einen jungen, ungeschickten Menschen, der versucht, Kaffee zu kochen. Ah, die Prüfungen des frühen Erwachsenenalters!"""
        elif language == 'Turkish':
            system_content = """Sen Bay David Attenborough'sun. Resimdeki insanı sanki bir doğa belgeseliymiş gibi anlat.
                                Alaycı ve komik olsun. Kendini tekrar etme. Kısa tut. En fazla 20 kelime. Her seferinde cümlelerini tamamla.
                                Örnek olara: Genç bir insanı beceriksizce kahve yapmaya çalışırken görüyoruz. Ah, erken yetişkinliğin sınavları!"""
        else:
            system_content = """You are Sir David Attenborough. Narrate the picture of the human as if it is a nature documentary.
                                Make it snarky and funny. Don't repeat yourself. Make it short. Maximum 20 words. Complete your sentences every time. If I do anything remotely interesting, make a big deal about it!"""
    elif voice_id == 'Change with the second Voice ID option':
        if language == 'German':
            system_content = """Du bist Loki aus Marvel Movies. Erzählen Sie das Bild des Menschen mit Ihrem charakteristischen schelmischen Gespür. Seien Sie witzig und leicht verächtlich. Halten Sie es prägnant,
                                nicht mehr als 20 Wörter. Stellen Sie sicher, dass jeder Satz vollständig ist. Wenn sie etwas auch nur annähernd Cleveres tun, übertreiben Sie dessen Brillanz übermäßig!"""
        elif language == 'Turkish':
            system_content = """Sen Marvel Filmlerinden Loki'sin. Kendi imzanızı taşıyan muzip yeteneğinizle insan resmini anlatın. Esprili ve biraz küçümseyici olun. Kısa ve öz tutun, 20 kelimeyi geçmeyin.
                                Her cümlenin tamamlandığından emin olun. Biraz dahice bir şey yaparlarsa, onun parlaklığını abartılı bir şekilde abartın!"""
        else:
            system_content = """You are Loki from Marvel Movies. Narrate the picture of the human with your signature mischievous flair. Be witty and slightly disdainful. Keep it concise, no more than 20 words.
                                Ensure each sentence is complete. If they do anything even mildly clever, exaggerate its brilliance extravagantly!"""
    elif voice_id == 'Change with the third Voice ID option':
        if language == 'German':
            system_content = """Erzählen Sie das Bild des Menschen."""
        elif language == 'Turkish':
            system_content = """Görseldeki insanı anlat."""
        else:
            system_content = """Narrate the picture of the human."""
    elif voice_id == 'Change with the fourth Voice ID option':
        if language == 'German':
            system_content = """Erzählen Sie das Bild des Menschen."""
        elif language == 'Turkish':
            system_content = """Görseldeki insanı anlat."""
        else:
            system_content = """Narrate the picture of the human."""
    elif voice_id == 'Change with the fifth Voice ID option':
        if language == 'German':
            system_content = """Erzählen Sie das Bild des Menschen."""
        elif language == 'Turkish':
            system_content = """Görseldeki insanı anlat."""
        else:
            system_content = """Narrate the picture of the human."""

    while True:
        try:
            response = openai.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[{"role": "system", "content": system_content}] + script + generate_message(base64_image),
                max_tokens=100
            )
            response_text = response.choices[0].message.content.strip()

            detected_language = langdetect.detect(response_text)
            is_apology = any(phrase in response_text for phrase in ["I'm sorry", "Sorry", "Özür dilerim", "Es tut mir Leid", "Entschuldigung"])

            if detected_language == iso_language and not is_apology and response_text:
                return response_text
            logging.debug(f"Retry: Generated text not in {iso_language} or is an apology. Retrying...")
        except Exception as e:
            logging.error(f"Unexpected error: {e}. Retrying...")




def main(language):
    global streaming
    cap = cv2.VideoCapture(1)
    if not cap.isOpened():
        raise IOError("Cannot open webcam")

    script = []

    try:
        while streaming:
            image_path = capture_and_process_image(cap)
            if image_path and streaming:
                base64_image = encode_image(image_path)
                analysis = analyse(base64_image, script=script, language=language)
                if streaming:
                    print(analysis)
                    play_audio(analysis)
                    script = script + [{"role": "assistant", "content": analysis}]
            time.sleep(2)
    except KeyboardInterrupt:
        print("Program stopped by user.")
    finally:
        cap.release()
        cv2.destroyAllWindows()


app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')
streaming = False


def gen_frames():
    global streaming
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Error: Camera is not opened.")
        return
    try:
        while streaming:
            success, frame = cap.read()
            if not success or not streaming:
                print("Error: Could not read frame.")
                break
            
            ret, buffer = cv2.imencode('.jpg', frame)
            if not ret:
                print("Error: Frame could not be encoded.")
                continue

            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        cap.release()
            

@app.route('/start')
def start():
    global streaming
    if not streaming:
        streaming = True

        @copy_current_request_context
        def run_script_with_context():
            language = session.get('language', 'default_language')
            main(language)

        thread = Thread(target=run_script_with_context)
        thread.start()
        return "Started"
    else:
        return "Already Started", 409


@app.route('/stop')
def stop():
    global streaming
    if streaming:
        streaming = False
        with lock:
            audio_files.clear()
        print("Streaming stopped and audio files cleared.")
        return "Stopped"
    return "Already Stopped", 404


@app.route('/set_voice', methods=['POST'])
def set_voice():
    data = request.get_json()
    voice_id = data['voiceID']
    session['voice_id'] = voice_id
    return jsonify({'voiceID': voice_id})


@app.route('/video_feed')
def video_feed():
    if streaming:
        return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
    else:
        return "Streaming not started", 404


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/audio/<path:filename>')
def audio_file(filename):
    response = send_from_directory('static/Audio Files', filename)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@app.route('/get_latest_audio_folder')
def get_latest_audio_folder():
    if audio_files:
        latest_folder = audio_files[-1]
        print(f"Fetching latest audio folder: {latest_folder}")
        return latest_folder
    return '', 404


@app.route('/set_language', methods=['POST'])
def set_language():
    data = request.get_json()
    language = data['language']
    session['language'] = language
    print(f"Language set to {language}")
    return jsonify({"message": "Language set successfully", "language": language})


@app.route('/get_language')
def get_language():
    language = session.get('language', 'English')
    return jsonify({"current_language": language})


if __name__ == '__main__':
    app.run(debug=True)
