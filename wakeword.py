import speech_recognition as sr
import requests
import time
import os

# Configuration
WAKE_WORDS = ["prime", "hey prime", "ip prime", "i p prime", "eye p prime", "ip prime sir"]
COMMAND_PREFIXES = ["open", "play", "check", "who", "what", "where", "how", "show", "tell", "searching", "search"]
SERVER_URL = "https://localhost:8340/api/wake" # Note: https because of certs

def listen_for_wake_word():
    r = sr.Recognizer()
    mic = sr.Microphone()

    print("IP Prime Listener Active (24/7)")
    print("Say 'Prime' to wake her up...")
    print(f"Waiting for wake words: {WAKE_WORDS}")

    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1)
        
    while True:
        try:
            with mic as source:
                print(".", end="", flush=True)
                audio = r.listen(source, timeout=None, phrase_time_limit=3)
            
            # Use Google Speech Recognition (Free tier)
            text = r.recognize_google(audio).lower()
            print(f"\nHeard: '{text}'")

            is_wake = any(word in text for word in WAKE_WORDS)
            is_direct_command = any(text.startswith(prefix) for prefix in COMMAND_PREFIXES)

            if is_wake or is_direct_command:
                print(f"--- {'Wake word' if is_wake else 'Direct command'} detected! Notifying server...")
                try:
                    # Insecure request because of local self-signed certs
                    payload = {"text": text}
                    requests.post(SERVER_URL, json=payload, verify=False, timeout=2)
                except Exception as e:
                    print(f"Failed to notify server: {e}")
                    
        except sr.UnknownValueError:
            pass # Silent
        except sr.RequestError as e:
            print(f"Could not request results; {e}")
            time.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    listen_for_wake_word()
