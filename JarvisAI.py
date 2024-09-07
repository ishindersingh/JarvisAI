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

# Initialize the text-to-speech engine
engine = pyttsx3.init()

# Path to store face data
FACE_DATA_PATH = 'faces.json'

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
        audio = recognizer.listen(source, phrase_time_limit=5)
        command = recognizer.recognize_google(audio).lower()
        print(f"You said: {command}")
        return command

    except sr.UnknownValueError:
        print("Sorry, I didn't catch that.")
        return None
    
    except sr.RequestError:
        print("Could not request results from Google Speech Recognition service.")
        return None

def handle_command(command):
    """Handle commands like 'be my keyboard', 'search', 'tell time', 'remember my face', 'who am I'."""
    if "be my keyboard" in command:
        speak("What would you like me to type?")
        print("What would you like me to type?")
        
        # Listen for the text to type
        with sr.Microphone() as source:
            text_to_type = listen_for_command(source)
        
        if text_to_type:
            speak(f"Typing {text_to_type}")
            pyautogui.typewrite(text_to_type)
            print(f"Typed: {text_to_type}")
    
    elif "search" in command:
        handle_search_command(command)
    
    elif "time" in command:
        handle_time_command()
    
    elif "remember my face" in command:
        remember_face()
    
    elif "who am i" in command:
        who_am_i()

def handle_search_command(command):
    """Handle the 'search' command by determining where to search and what to search for."""
    if "on youtube" in command:
        search_platform = "youtube"
    elif "on google" in command:
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

    chrome_path = 'C:\Program Files\Google\Chrome\Application\chrome.exe'

    try:
        subprocess.run([chrome_path, url])
    except Exception as e:
        print(f"Failed to open Chrome: {e}")
        webbrowser.open(url)

    print(f"Searching for '{search_query}' on {search_platform}...")

def handle_time_command():
    """Tell the current time."""
    now = datetime.now()
    current_time = now.strftime("%I:%M %p")
    speak(f"The current time is {current_time}")
    print(f"The current time is {current_time}")

if __name__ == "__main__":
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
