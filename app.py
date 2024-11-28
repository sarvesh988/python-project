# imort all libraray here 
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, send_file
from twilio.rest import Client
from googlesearch import search
from flask_socketio import SocketIO, emit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from datetime import datetime, timedelta
import time
import base64
import smtplib
import boto3
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import threading
from flask_sqlalchemy import SQLAlchemy
import getpass
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
import io
import os
import pywhatkit
import pyautogui
import pyttsx3
import speech_recognition as sr
import dlib
from werkzeug.utils import secure_filename
from uuid import uuid4 as uuid
from dotenv import load_dotenv
import urllib.parse
from cvzone.HandTrackingModule import HandDetector
from googlesearch import search as google_search  
from flask_socketio import SocketIO, emit

# Load environment variables
load_dotenv()
app = Flask(__name__)

# -----------------Twilio----------------
account_sid = os.getenv('your_twilio_account_sid')
auth_token = os.getenv('your_twilio_auth_token')
twilio_number = os.getenv('your_twilio_phone_number')
app.secret_key = 'secret_key'

client = Client(account_sid, auth_token)

# render to index.html
@app.route('/')
def index():
    return render_template('index.html')

        # ------------------------------call someone-------------
        
# Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

@app.route('/call', methods=['POST'])
def call():
    number = request.form['number']
    from_number = request.form['from_number']
    delay_minutes = request.form.get('delay_minutes', type=int)

    if delay_minutes and delay_minutes > 0:
  
        delay_time = datetime.now() + timedelta(minutes=delay_minutes)
        scheduler.add_job(make_call, 'date', run_date=delay_time, args=[number, from_number])
        flash(f"Call scheduled successfully in {delay_minutes} minutes!", 'success')
    else:
    
        try:
            call = client.calls.create(
                to=number,
                from_=from_number,
                url='http://demo.twilio.com/docs/voice.xml'
            )
            flash(f"Call Success! Call SID: {call.sid}", 'success')
        except Exception as e:
            flash(str(e), 'danger')

    return redirect(url_for('index'))

def make_call(to, from_):
    try:
        call = client.calls.create(
            to=to,
            from_=from_,
            url='http://demo.twilio.com/docs/voice.xml'
        )
        print(f"Call initiated! Call SID: {call.sid}")
    except Exception as e:
        print(f"Error: {e}")

        
    #    -----------------SMS---------------- 
from_number = os.getenv('TWILIO_PHONE_NUMBER')
client = Client(account_sid, auth_token)


# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.start()

def send_sms(number, message):
    try:
        sent_message = client.messages.create(
            body=message,
            from_=from_number,
            to=number
        )
        return {'status': 'success', 'sid': sent_message.sid}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def send_delayed_sms(number, message):
    return send_sms(number, message)

@app.route('/handle_sms', methods=['POST'])
def handle_sms():
    data = request.json
    number = data.get('number')
    message = data.get('message')
    delay_minutes = int(data.get('delay_minutes', 0))

    if not number:
        return jsonify({'status': 'error', 'message': 'Phone number is required.'})
    if not message:
        return jsonify({'status': 'error', 'message': 'Message is required.'})

    if delay_minutes > 0:
        # Schedule the SMS
        delay_time = datetime.now() + timedelta(minutes=delay_minutes)
        scheduler.add_job(send_delayed_sms, 'date', run_date=delay_time, args=[number, message])
        return jsonify({'status': 'success', 'message': f'SMS scheduled successfully in {delay_minutes} minutes!'})
    else:
        # Send SMS immediately
        result = send_sms(number, message)
        return jsonify(result)
    
    


# -----------------Google Search----------------
@app.route('/google_search', methods=['POST'])
def google_search_route():
    data = request.get_json()
    query = data.get('query')
    
    if not query:
        return jsonify({'results': []}), 400
    
    try:
        results = [url for url in search(query, num_results=5)]
    except Exception as e:
        print(f"Error during Google search: {e}")
        results = []
    
    return jsonify({'results': results})

# ------------------Search Google Query----------------


@app.route('/search/google', methods=['POST'])
def search_google():
    query = request.form.get('query')
    query = urllib.parse.quote(query)
    return redirect(f'https://www.google.com/search?q={query}')




# -----------------Search Bing Query----------------

@app.route('/search/bing', methods=['POST'])
def search_bing():
    query = request.form.get('query')
    query = urllib.parse.quote(query)
    return redirect(f'https://www.bing.com/search?q={query}')


# -------------Photo Click and Capture------------


UPLOAD_FOLDER = 'static/images'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def capture_frame(ip):
    cap_ip = cv2.VideoCapture(f"http://{ip}/video")
    success, frame = cap_ip.read()
    cap_ip.release()
    if success:
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        cv2.imwrite(filepath, frame)
        return filename
    return None
@app.route('/capture_photo', methods=['POST'])
def capture_photo():
    data = request.get_json()
    ip = data.get('ip')
    if ip:
        filename = capture_frame(ip)
        if filename:
            return jsonify(message=f"Photo captured and saved as {filename}")
        else:
            return jsonify(message="Failed to capture photo"), 500
    return jsonify(message="IP address not provided"), 400

@app.route('/image/<filename>')
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)



# -------------Send Email----------------


@app.route('/send_email', methods=['POST'])
def send_email():
    data = request.json
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = smtp_user
    to_email = data.get('to_email')
    subject = data.get('subject')
    body = data.get('body')

    subject = subject.encode('utf-8').decode('utf-8')
    body = body.encode('utf-8').decode('utf-8')

    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject

    message.attach(MIMEText(body, 'plain', 'utf-8'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, to_email, message.as_string())
        server.quit()

        return jsonify({'status': 'success', 'message': 'Email sent successfully!'})

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/send_delayed_email', methods=['POST'])
def handle_send_delayed_email():
    data = request.json
    smtp_user = os.getenv('SMTP_USER')
    smtp_password = os.getenv('SMTP_PASSWORD')
    from_email = smtp_user
    to_email = data.get('to_email')
    subject = data.get('subject')
    body = data.get('body')
    delay_seconds = int(data.get('delay_seconds', 0))  # Delay in seconds

    subject = subject.encode('utf-8').decode('utf-8')
    body = body.encode('utf-8').decode('utf-8')

    if delay_seconds > 0:
        def send_email_after_delay(smtp_user, smtp_password, from_email, to_email, subject, body, delay_seconds):
            time.sleep(delay_seconds)
            send_email(smtp_user, smtp_password, from_email, to_email, subject, body)
        
        thread = threading.Thread(target=send_email_after_delay, args=(smtp_user, smtp_password, from_email, to_email, subject, body, delay_seconds))
        thread.start()
        return jsonify({'status': 'success', 'message': 'Email scheduled successfully!'})
    else:
        send_email(smtp_user, smtp_password, from_email, to_email, subject, body)
        return jsonify({'status': 'success', 'message': 'Email sent immediately!'})


# -----------------Create EC2 instance----------------
@app.route("/ec2", methods=["GET", "POST"])
def create_ec2():
    if request.method == "POST":
        # Get AWS credentials and other details from form
        aws_access_key_id = request.form["aws_access_key_id"]
        aws_secret_access_key = request.form["aws_secret_access_key"]
        region = request.form["region"]
        instance_type = request.form["instance_type"]
        image_id = request.form["image_id"]
        max_count = int(request.form["max_count"])
        min_count = int(request.form["min_count"])
        
        # Create EC2 instance
        ec2_instance = boto3.resource(
            service_name="ec2",
            region_name=region,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )

        ec2_instance.create_instances(
            InstanceType=instance_type,
            ImageId=image_id,
            MaxCount=max_count,
            MinCount=min_count
        )

        return "EC2 Instance(s) Created"

    return render_template("index.html")

# -----------------Opencv2 Ec2 instance ------------------


# AWS EC2 configurations
AWS_ACCESS_KEY_ID = ''  # Replace with your actual access key
AWS_SECRET_ACCESS_KEY = ''  # Replace with your actual secret key
REGION_NAME = ''  # Replace with your desired AWS region
IMAGE_ID = ''  # Replace with your AMI ID
INSTANCE_TYPE = ''
# Initialize the EC2 resource
ec2 = boto3.resource(
    service_name="ec2",
    region_name=REGION_NAME,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# Initialize the hand detector
detector = HandDetector(maxHands=1)
is_detecting = False

def create_ec2_instances(count):
    """Create EC2 instances based on the count."""
    if count <= 0:
        print("Invalid number of instances. Must be greater than 0.")
        return

    instances = ec2.create_instances(
        InstanceType=INSTANCE_TYPE,
        ImageId=IMAGE_ID,
        MinCount=count,
        MaxCount=count
    )
    instance_ids = [instance.id for instance in instances]
    print(f"Created {count} EC2 instance(s): {instance_ids}")

def count_fingers(lm_list):
    """Count the number of fingers extended based on hand landmarks."""
    finger_tips = [4, 8, 12, 16, 20]  # Tips of the fingers
    extended_fingers = []

    for i in range(5):
        # Each finger has 3 joints, we check the tip and the joint before it
        if lm_list[finger_tips[i]][1] < lm_list[finger_tips[i] - 2][1]:
            extended_fingers.append(i)
    
    return len(extended_fingers)

def detect_fingers_and_manage_instances():
    global is_detecting
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    is_detecting = True
    while is_detecting:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Detect hands in the frame
        hands, img = detector.findHands(frame, draw=True)

        if hands:
            for hand in hands:
                if 'lmList' in hand:
                    lmlist = hand['lmList']  # Access landmarks list
                    finger_count = count_fingers(lmlist)
                    
                    print(f"Detected fingers: {finger_count}")

                    if finger_count > 0:
                        print(f"Launching {finger_count} instance(s)")
                        create_ec2_instances(finger_count)
                        # Sleep to avoid rapid instance creation
                        is_detecting = False
                        break

        cv2.imshow("Camera Feed", img)
        if cv2.waitKey(1) & 0xFF == 27:  # ESC key to exit
            break

    cap.release()
    cv2.destroyAllWindows()
    print("Detection stopped.")

@app.route('/start_detection', methods=['POST'])
def start_detection():
    if not is_detecting:
        threading.Thread(target=detect_fingers_and_manage_instances).start()
        return jsonify({"message": "Started hand detection and instance creation."})
    else:
        return jsonify({"message": "Detection already in progress."})
    

# ----------------------------------instagram ---------------------------------------
from instagrapi import Client
from PIL import Image


app.config['UPLOAD_FOLDER'] = 'uploads/'

# Ensure the upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

from werkzeug.utils import secure_filename

@app.route('/insta', methods=['POST'])
def insta():
    cl = Client()
    cl.login("username", "your_password")

    if 'photo' not in request.files:
        return "No file part"
    
    file = request.files['photo']
    
    if file.filename == '':
        return "No selected file"
    
    if file:
        filename = secure_filename(file.filename)
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(photo_path)
        
        caption = request.form.get('caption', '')

        try:
            with Image.open(photo_path) as img:
                img.verify()  # This will check if the image is corrupted
            cl.photo_upload(photo_path, caption)
            return "Photo posted successfully!"
        except (IOError, SyntaxError) as e:
            return f"An error occurred while processing the image: {e}"
        except Exception as e:
            return f"An error occurred: {e}"
        
        
        # --------------------------------face crop ------------------------------------
UPLOAD_FOLDER = 'uploads/'
OUTPUT_FOLDER = 'static/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload and output directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)



@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        output_image_path = process_image(file_path)
        return jsonify({'output_image': output_image_path})
    return 'No file uploaded', 400

def process_image(image_path):
    image = cv2.imread(image_path)
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    if len(faces) > 0:
        (x, y, w, h) = faces[0]
        cropped_face = image[y:y+h, x:x+w]

        resized_face = cv2.resize(cropped_face, (100, 100))

        image[0:100, 0:100] = resized_face

    output_image_path = os.path.join(OUTPUT_FOLDER, os.path.basename(image_path))
    cv2.imwrite(output_image_path, image)

    return output_image_path




# -----------------Filter onn image----------------
UPLOAD_FOLDER = 'uploads'
FILTERED_FOLDER = 'filtered'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FILTERED_FOLDER, exist_ok=True)

def apply_color_filter(image_path, filter_color, output_path):
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Could not load image.")
        return

    filtered_image = image.copy()

    if filter_color.lower() == 'red':
        filtered_image[:, :, 0] = 0
        filtered_image[:, :, 1] = 0
    elif filter_color.lower() == 'green':
        filtered_image[:, :, 0] = 0
        filtered_image[:, :, 2] = 0
    elif filter_color.lower() == 'blue':
        filtered_image[:, :, 1] = 0
        filtered_image[:, :, 2] = 0
    else:
        print("Invalid color filter.")
        return

    cv2.imwrite(output_path, filtered_image)



@app.route('/uploadfilter', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    filter_color = request.form.get('filter_color')

    if file.filename == '':
        return "No selected file", 400

    if file:
        filename = file.filename
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        output_path = os.path.join(FILTERED_FOLDER, filename)
        apply_color_filter(file_path, filter_color, output_path)
        return send_from_directory(FILTERED_FOLDER, filename)

@app.route('/capture', methods=['POST'])
def capture_image():
    filter_color = request.form.get('filter_color')

    # Capture image from webcam
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if not ret:
        return "Error capturing image", 500

    filename = 'captured_image.jpg'
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    cv2.imwrite(file_path, frame)
    output_path = os.path.join(FILTERED_FOLDER, filename)
    apply_color_filter(file_path, filter_color, output_path)
    return send_from_directory(FILTERED_FOLDER, filename)



# ------------------------------------swip image--------------------

app.config['UPLOAD_FOLDER'] = 'uploads/'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")

def get_face_landmarks(image):
    if image is None:
        return None
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = detector(gray, 1)
    
    if len(faces) == 0:
        return None
    
    return [np.matrix([[p.x, p.y] for p in predictor(gray, face).parts()]) for face in faces]

def warp_image(img1, img2, landmarks1, landmarks2):
    return img1

@app.route('/swap_faces', methods=['POST'])
def swap_faces():
    if 'file1' not in request.files or 'file2' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file1 = request.files['file1']
    file2 = request.files['file2']
    
    if file1.filename == '' or file2.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    filename1 = secure_filename(file1.filename)
    filename2 = secure_filename(file2.filename)
    
    path1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
    path2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)
    
    file1.save(path1)
    file2.save(path2)
    
    img1 = cv2.imread(path1)
    img2 = cv2.imread(path2)
    
    landmarks1 = get_face_landmarks(img1)
    landmarks2 = get_face_landmarks(img2)
    
    if landmarks1 is None or landmarks2 is None:
        return jsonify({'error': 'No face detected in one or both images'}), 400
    
    output_img = warp_image(img1, img2, landmarks1, landmarks2)
    
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], 'output.jpg')
    cv2.imwrite(output_path, output_img)
    
    return send_file(output_path, mimetype='image/jpeg')

# ------------------------speak---------------------------- 

engine = pyttsx3.init()

def speak():
    return render_template('index.html')


@app.route('/speak', methods=['POST'])
def speak():
    text = request.form['text']
    if text:
        try:
            engine.say(text)
            engine.runAndWait()
            return jsonify(success=True)
        except Exception as e:
            print(f"Error: {e}")
            return jsonify(success=False)
    else:
        return jsonify(success=False)


# --------------------------sunglass set------------------------- 
# Load the face detection classifier
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

# Define paths to accessory images
hat_path = 'old-fedora-hat-removebg-preview.png'
sunglasses_path = 'sunglasses.jpg'

def add_accessory(frame, accessory_path, face_rect, scale=1, position_offset=(0, 0)):
    accessory = cv2.imread(accessory_path, cv2.IMREAD_UNCHANGED)
    if accessory is None:
        print("Error: Could not load accessory.")
        return frame

    accessory_width = int(face_rect[2] * scale)
    accessory_height = int(accessory_width * accessory.shape[0] / accessory.shape[1])
    accessory_resized = cv2.resize(accessory, (accessory_width, accessory_height), interpolation=cv2.INTER_LINEAR)

    if accessory_resized.shape[2] == 4:
        alpha_channel = accessory_resized[:, :, 3] / 255.0
        accessory_resized = accessory_resized[:, :, :3]
    else:
        alpha_channel = np.ones(accessory_resized.shape[:2])

    x, y, w, h = face_rect
    y = y - accessory_height // 2 + position_offset[1]
    x = x + w // 2 - accessory_width // 2 + position_offset[0]

    if y < 0 or x < 0 or y + accessory_height > frame.shape[0] or x + accessory_width > frame.shape[1]:
        print("Error: Accessory position out of bounds.")
        return frame

    for c in range(3):
        frame[y:y+accessory_height, x:x+accessory_width, c] = (1 - alpha_channel) * frame[y:y+accessory_height, x:x+accessory_width, c] + alpha_channel * accessory_resized[:, :, c]

    return frame

@app.route('/add_accessory', methods=['POST'])
def add_accessory_route():
    data = request.json
    image_data = data['image'].split(',')[1]
    accessory = data['accessory']

    image = np.frombuffer(base64.b64decode(image_data), dtype=np.uint8)
    frame = cv2.imdecode(image, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.1, 4)

    for face_rect in faces:
        if accessory == 'hat':
            frame = add_accessory(frame, hat_path, face_rect, scale=1, position_offset=(0, -face_rect[3] // 4))
        elif accessory == 'sunglasses':
            frame = add_accessory(frame, sunglasses_path, face_rect, scale=1, position_offset=(0, face_rect[3] // 5))

    _, buffer = cv2.imencode('.jpg', frame)
    frame_encoded = base64.b64encode(buffer).decode('utf-8')

    return jsonify({'image': frame_encoded})

# ---------------------------whastsapp message------------------- 


def what():
    return render_template('index.html')

@app.route('/send', methods=['POST'])
def send():
    number = request.form['number']
    message = request.form['message']

    pywhatkit.sendwhatmsg_instantly(number, message, wait_time=10, tab_close=True, close_time=10)
    time.sleep(10)
    pyautogui.press('enter')

    return 'Message sent!'

# ---------------------------------------custom image-----------------------

@app.route('/', methods=['GET', 'POST'])
def image():
    if request.method == 'POST':
        width = int(request.form['width'])
        height = int(request.form['height'])
        shape = request.form['shape'].strip().lower()
        start_x = int(request.form['start_x'])
        start_y = int(request.form['start_y'])
        end_x = int(request.form['end_x'])
        end_y = int(request.form['end_y'])
        color_b = int(request.form['color_b'])
        color_g = int(request.form['color_g'])
        color_r = int(request.form['color_r'])

        # Create image
        image = np.zeros((height, width, 3), dtype=np.uint8)
        color = (color_b, color_g, color_r)

        if shape == 'rectangle':
            cv2.rectangle(image, (start_x, start_y), (end_x, end_y), color, -1)
        elif shape == 'line':
            thickness = int(request.form['thickness'])
            cv2.line(image, (start_x, start_y), (end_x, end_y), color, thickness)
        elif shape == 'circle':
            radius = int(request.form['radius'])
            cv2.circle(image, (start_x, start_y), radius, color, -1)
        else:
            return render_template('index.html', error="Shape not recognized. Please enter 'rectangle', 'line', or 'circle'.")

        # Convert the image to a format Flask can send
        _, img_encoded = cv2.imencode('.png', image)
        img_io = io.BytesIO(img_encoded.tobytes())
        return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='custom_image.png')

if __name__ == '__main__':
    app.run(debug=True)
