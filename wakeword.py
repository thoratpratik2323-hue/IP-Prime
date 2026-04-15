import speech_recognition as sr
import requests
import time
import os

# Configuration
WAKE_WORDS = ["prime", "hey prime", "ip prime", "i p prime", "eye p prime", "ip prime sir", "prem"]
COMMAND_PREFIXES = ["open", "play", "check", "who", "what", "where", "how", "show", "tell", "searching", "search", "karo", "dikhao"]
SERVER_URL = "https://127.0.0.1:8340/api/wake" # Note: https because of certs

def log_to_file(msg):
    with open("wakeword.log", "a") as f:
        f.write(msg + "\n")
    print(msg)

def listen_for_wake_word():
    r = sr.Recognizer()
    mic = sr.Microphone()

    log_to_file("IP Prime Listener Active (24/7)")
    log_to_file("Say 'Prime' to wake her up...")
    log_to_file(f"Waiting for wake words: {WAKE_WORDS}")

    with mic as source:
        r.adjust_for_ambient_noise(source, duration=1)
        
    while True:
        try:
            with mic as source:
                print(".", end="", flush=True)
                audio = r.listen(source, timeout=None, phrase_time_limit=3)
            
            # Use Google Speech Recognition (Free tier)
            text = r.recognize_google(audio, language="en-IN").lower()
            log_to_file(f"\nHeard: '{text}'")

            is_wake = any(word in text for word in WAKE_WORDS)
            is_direct_command = any(text.startswith(prefix) for prefix in COMMAND_PREFIXES)

            if is_wake or is_direct_command:
                log_to_file(f"--- {'Wake word' if is_wake else 'Direct command'} detected! Notifying server...")
                try:
                    # Insecure request because of local self-signed certs
                    payload = {"text": text}
                    requests.post(SERVER_URL, json=payload, verify=False, timeout=5)
                except Exception as e:
                    log_to_file(f"Failed to notify server: {e}")
                    
        except sr.UnknownValueError:
            pass # Silent
        except sr.RequestError as e:
            log_to_file(f"Could not request results; {e}")
            time.sleep(5)
        except Exception as e:
            log_to_file(f"Error: {e}")
            time.sleep(1)

if __name__ == "__main__":
    listen_for_wake_word()
