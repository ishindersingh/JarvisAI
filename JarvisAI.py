import pvporcupine
import pyaudio
import pyttsx3
import pyautogui
import numpy as np
import speech_recognition as sr
import subprocess
import webbrowser
import face_recognition
import cv2
import os
import json
from datetime import datetime
import mediapipe as mp
import serial
import time
import torch
import tkinter as tk
from tkinter import scrolledtext
import sys
from groq import Groq

client = Groq(api_key="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")

# YOLOv5 model initialization
model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)

# Mediapipe hands setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7, min_tracking_confidence=0.7)

# Initialize Serial Communication with Arduino on COM6
#arduino = serial.Serial('COM6', 9600)
time.sleep(0.5)  # Wait for the connection to establish

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Path to store face data
FACE_DATA_PATH = 'faces.json'
class RobotConsoleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("JarvisAi")
        self.root.geometry("800x500")
        self.root.config(bg='#010517') 
        
        
        self.root.iconbitmap('1.ico')  

     
        self.header = tk.Label(root, text="JarvisAi", font=("OCR A Extended", 18), bg="#010517", fg="#60fdfc")
        self.header.pack(pady=10)

        self.console_display = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("Consolas", 12), bg="#010517", fg="#60fdfc", insertbackground='white', padx=10, pady=10
        )
        self.console_display.pack(fill=tk.BOTH, expand=True)

      
        sys.stdout = self
        sys.stderr = self
        
    def write(self, message):
        # Add bullet points before each new message
        if message.strip():  # Only add bullet for non-empty messages
            formatted_message = f"• {message.strip()}\n"
            self.console_display.insert(tk.END, formatted_message)
           
        self.console_display.see(tk.END)  # Auto-scroll to the bottom

    def flush(self):
        pass
def start_robot_console_gui():
    root = tk.Tk()
    app = RobotConsoleApp(root)
    root.mainloop()

def speak(text):
    """Provides voice feedback."""
    engine.say(text)
    engine.runAndWait()

def load_face_data():
    """Load the face encodings and names from the file."""
    if os.path.exists(FACE_DATA_PATH):
        with open(FACE_DATA_PATH, 'r') as f:
            return json.load(f)
    return {}

def save_face_data(face_data):
    """Save the face encodings and names to the file."""
    with open(FACE_DATA_PATH, 'w') as f:
        json.dump(face_data, f)

def capture_frame():
    """Capture a frame from the webcam."""
    video_capture = cv2.VideoCapture(0)
    ret, frame = video_capture.read()
    video_capture.release()
    return frame

def recognize_face(frame):
    """Recognize a face from a given frame."""
    face_locations = face_recognition.face_locations(frame)
    
    if len(face_locations) == 0:
        return None
    
    face_encoding = face_recognition.face_encodings(frame, face_locations)[0]
    
    # Load known faces
    face_data = load_face_data()
    known_face_encodings = [np.array(enc) for enc in face_data.values()]
    known_face_names = list(face_data.keys())

    # Compare the captured face with known faces using a tolerance for accuracy
    matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.5)
    face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)

    if True in matches:
        best_match_index = np.argmin(face_distances)
        return known_face_names[best_match_index]
    return None

def detect_objects(frame):
    """Detect objects in a given frame and inform the user what is detected."""
    # Run the model on the provided frame
    results = model(frame)

    # Extract labels for detected objects
    detected_objects = results.pandas().xyxy[0]['name'].tolist()

    if detected_objects:
        # Tell the user what has been detected
        detected_list = ', '.join(detected_objects)
        print(f"Detected: {detected_list}")
        speak(f"I see {detected_list}.")
    else:
        # Inform the user if nothing was detected
        print("No objects detected.")
        speak("I can't detect anything right now.")

def run_object_detection():
    """Detect objects in a single frame from the webcam and provide information to the user."""
    cap = cv2.VideoCapture(0)  # Initialize webcam
    
    # Lower the webcam resolution for better performance
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    
    try:
        ret, frame = cap.read()
        if not ret:
            print("Failed to capture image from webcam.")
            speak("Failed to capture image from webcam.")
            return

        # Perform object detection on the current frame
        detect_objects(frame)

    finally:
        cap.release()

def greet_user():
    """Greet the user based on face recognition at program startup."""
    now = datetime.now()
    current_time = now.strftime("%I:%M %p")

    frame = capture_frame()
    user_name = recognize_face(frame)

    if user_name:
        speak(f"Good {get_time_of_day()}, {user_name}.")
        print(f"Recognized {user_name}.")
    else:
        speak(f"Good {get_time_of_day()}, user.")
        print("Unrecognized user.")

def get_time_of_day():
    """Return the time of day (morning, afternoon, or evening) based on the current hour."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 18:
        return "afternoon"
    else:
        return "evening"

def remember_face():
    """Capture the user's face and store it in the database with their name."""
    speak("Capturing your face...")

    # Capture a frame
    frame = capture_frame()

    # Detect face in the frame
    face_locations = face_recognition.face_locations(frame)
    if len(face_locations) == 0:
        speak("No face detected. Please try again.")
        return

    # Extract face encoding
    face_encoding = face_recognition.face_encodings(frame, face_locations)[0]

    # Ask for the user's name
    speak("Please tell me your name.")
    print("Listening for the user's name...")
    with sr.Microphone() as source:
        recognizer = sr.Recognizer()
        try:
            audio = recognizer.listen(source, phrase_time_limit=5)
            user_name = recognizer.recognize_google(audio).lower()
            print(f"User's name: {user_name}")
        except:
            speak("Sorry, I didn't catch that. Try again.")
            return

    # Save the face encoding and name
    face_data = load_face_data()
    face_data[user_name] = face_encoding.tolist()  # Convert numpy array to list
    save_face_data(face_data)

    speak(f"Face remembered as {user_name}.")
    print(f"Face saved as {user_name}.")

def who_am_i():
    """Recognize the user's face by comparing with known faces in the database."""
    print("Capturing your face...")
    
    # Capture a frame
    frame = capture_frame()

    # Recognize the face
    user_name = recognize_face(frame)

    if user_name:
        speak(f"You are {user_name}.")
        print(f"Recognized as {user_name}.")
    else:
        speak("I don't recognize you.")
        print("Face not recognized.")

def listen_for_wake_word():
    """Listen for the wake word using Porcupine."""
    print("Listening for wake word...")

    # Replace with your actual AccessKey and path to .ppn file
    access_key = 'pRVF6gEgGIEd9nQnFdoeEgbSbWghq2cog3pEgUt8kMD5sbbvYiiv+A=='
    keyword_path = 'C:\\python\\Jarvis\\hey_computer.ppn'
    
    try:
        porcupine = pvporcupine.create(access_key=access_key, keyword_paths=[keyword_path])
    except Exception as e:
        print(f"Error initializing Porcupine: {e}")
        return False

    try:
        pa = pyaudio.PyAudio()
        stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
    except Exception as e:
        print(f"Error initializing PyAudio: {e}")
        return False

    try:
        while True:
            audio_data = stream.read(porcupine.frame_length, exception_on_overflow=False)
            audio_frame = np.frombuffer(audio_data, dtype=np.int16)
            keyword_index = porcupine.process(audio_frame)

            if keyword_index >= 0:
                print("Wake word detected!")
                speak("I'm listening")
                return True
    except Exception as e:
        print(f"Error during wake word detection: {e}")
    finally:
        stream.stop_stream()
        stream.close()
        pa.terminate()
        porcupine.delete()

def listen_for_command(source):
    """Listen for a command after the wake word is detected with a 5-second phrase time limit."""
    print("Listening for your command...")

    recognizer = sr.Recognizer()

    try:
        audio = recognizer.listen(source, phrase_time_limit=3)
        command = recognizer.recognize_google(audio).lower()
        print(f"You said: {command}")
        return command

    except sr.UnknownValueError:
        print("Sorry, I didn't catch that.")
        return None
    
    except sr.RequestError:
        print("Could not request results from Google Speech Recognition service.")
        return None

def control_led(command):
    """Control the built-in LED on the Arduino Nano."""
    if "on" in command:
        #arduino.write(b'1')  # Send '1' to turn on LED
        speak("Turning on the Fan.")
        print("Fan turned on")
    elif "off" in command:
        #arduino.write(b'0')  # Send '0' to turn off LED
        speak("Turning off the Fan.")
        print("Fan turned off")

def parse_intent(command):
    """Parse user intent using the Groq API."""
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant that helps with various tasks. "
                        "Extract intent, query, platform, and action from the user's input. "
                        "You can perform the following functions: "
                        "1. Search: 'Search Python tutorials on YouTube' -> intent: search, query: Python tutorials, platform: YouTube. "
                        "2. Get Time: 'What is the time?' -> intent: get_time. "
                        "3. Remember Face: 'Remember my face' -> intent: remember_face. "
                        "4. Who Am I: 'Who am I?' -> intent: who_am_i. "
                        "5. Open Application: 'Open GitHub' -> intent: open_application, platform: GitHub. "
                        "6. Perform Task: 'Write an email to John' -> intent: perform_task, action: write email to John. "
                        "7. Control Device: 'Turn on the fan' -> intent: control_device, action: turn on fan. "
                        "8. Detect Objects: 'What do you see?' -> intent: detect_objects."
                    )
                },
                {"role": "user", "content": command}
            ],
            temperature=0.5,
            max_tokens=50
        )
        response = completion.choices[0].message.content.strip()
        print(f"Raw response from Groq API: {response}")
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Handle the case where the response is not valid JSON
            lines = response.split('\n')
            intent_data = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    intent_data[key.strip().lower()] = value.strip()
            return intent_data
    except Exception as e:
        print(f"Error parsing intent: {e}")
        return None

def handle_command(command):
    """Handle commands by parsing intent using the Groq API."""
    intent_data = parse_intent(command)
    if not intent_data:
        speak("Sorry, I couldn't understand the command.")
        return

    intent = intent_data.get("intent")
    query = intent_data.get("query")
    platform = intent_data.get("platform")
    action = intent_data.get("action")

    if intent == "search":
        handle_search_command(f"search {query} on {platform}")
    elif intent == "get_time":
        handle_time_command()
    elif intent == "remember_face":
        remember_face()
    elif intent == "who_am_i":
        who_am_i()
    elif intent == "open_application" and platform == "GitHub":
        opengithub()
    elif intent == "perform_task" and action:
        speak(f"Performing task: {action}")
        print(f"Performing task: {action}")
        # Add code to perform the specific task if needed
    elif intent == "control_device" and "fan" in action:
        control_led(action)
    elif intent == "detect_objects":
        frame = capture_frame()
        detect_objects(frame)
    elif intent == "perform_task" and action:
        handle_undefined_task(action)
    else:
        speak("Sorry, I didn't understand that command.")
        print("Unrecognized command.")

def opengithub():
    """Open the user's GitHub profile in the default browser."""
    url = "https://github.com/ishindersingh"  # Replace 'YOUR_USERNAME' with your GitHub username
    webbrowser.open(url)
def handle_undefined_task(task):
    """Handle tasks that are not predefined in the program using Groq to generate Python code."""
    try:
        completion = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant that generates Python code for given tasks. "
                        "Ensure the code is pure Python and does not contain any text like ~~~ or '''. "
                        "If the task is to write an essay, generate the essay within the Python code and print it."
                    )
                },
                {"role": "user", "content": task}
            ],
            temperature=0.5,
            max_tokens=200
        )
        generated_code = completion.choices[0].message.content.strip()
        print(f"Generated code:\n{generated_code}")

        # Check for required libraries and install if necessary
        required_libraries = []
        for line in generated_code.split('\n'):
                if line.startswith('import ') or line.startswith('from '):
                    lib = line.split()[1]
                    if lib not in sys.modules:
                        required_libraries.append(lib)

        if required_libraries:
                for lib in required_libraries:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", lib])

        # Execute the generated code
        exec(generated_code)

    except Exception as e:
        print(f"Error handling undefined task: {e}")
        speak("Sorry, I couldn't complete the task due to an error.")

    # Example usage
    # handle_undefined_task("Write an essay on the importance of AI in healthcare.")
def handle_search_command(command):
    """Handle the 'search' command by determining where to search and what to search for."""
    if "youtube" in command:
        search_platform = "youtube"
    elif "google" in command:
        search_platform = "google"
    else:
        speak("Please specify where to search: on YouTube or Google.")
        return

    search_query = command.replace("search", "").replace(f"on {search_platform}", "").strip()

    if search_platform == "youtube":
        url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
    elif search_platform == "google":
        url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"

    speak(f"Searching for {search_query} on {search_platform}")

    webbrowser.open(url)

    print(f"Searching for '{search_query}' on {search_platform}...")

def handle_time_command():
    """Tell the current time."""
    now = datetime.now()
    current_time = now.strftime("%I:%M %p")
    speak(f"The current time is {current_time}")
    print(f"The current time is {current_time}")

if __name__ == "__main__":
    
    import threading
    gui_thread = threading.Thread(target=start_robot_console_gui)
    gui_thread.start()
    print("Starting Robotic System...")
    print("System Ready.")
    greet_user()  # Greet user upon initialization
    speak("Please say 'Hey Computer' to wake me up.")

    while True:
        if listen_for_wake_word():
            print("Ready for command...")
            with sr.Microphone() as source:
                command = listen_for_command(source)
                
                if command:
                    handle_command(command)
                
                speak("Going back to sleep...")
