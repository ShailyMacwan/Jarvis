import re
import threading
import time
import tkinter as tk
from tkinter import scrolledtext
import speech_recognition as sr
import webbrowser
import pyttsx3
import requests
import openai
import json
import os

openai_api_key = os.getenv("OPENAI_API_KEY")
newsapi = os.getenv("NEWS_API_KEY")
currencyapi = os.getenv("CURRENCY_API_KEY")
weatherapi = os.getenv("WEATHER_API_KEY")


# Initialize services
recogniser = sr.Recognizer()
engine = pyttsx3.init()
root = tk.Tk()
root.title("JARVIS Assistant")
root.geometry("600x400")

# Create a scrolled text widget
text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD)
text_area.pack(expand=True, fill=tk.BOTH)

def speak(text):
    engine.say(text)
    engine.runAndWait()
    text_area.insert(tk.END, f"JARVIS: {text}\n")
    text_area.yview(tk.END)

def delayed_speak(text, delay):
    time.sleep(delay)
    speak(text)

def openai_process(command):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Virtual Assistant named JARVIS skilled in general tasks like Alexa"},
            {"role": "user", "content": command}
        ]
    )
    content = response.choices[0].message['content']
    return content

def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?appid={weatherapi}&q={city}"

    try:
        response = requests.get(url).json()
        
        if response['cod'] != 200:
            return "Sorry, I couldn't fetch the weather data."

        weather_description = response['weather'][0]['description']
        temperature = response['main']['temp']
        city_name = response['name']

        return f"The weather in {city_name} is currently {weather_description} with a temperature of {temperature}°C."

    except Exception as e:
        return f"An error occurred: {e}"
    
def get_exchange_rate(base_currency, target_currency):
    url = f"https://v6.exchangerate-api.com/v6/{currencyapi}/pair/{base_currency}/{target_currency}"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        exchange_rate = data.get("conversion_rate", None)
        if exchange_rate:
            return f"The exchange rate from {base_currency} to {target_currency} is {exchange_rate}"
        else:
            return "Sorry, I could not retrieve the exchange rate."
            
def extract_currency(command):
    pattern = r"(convert|exchange rate)\s+([A-Za-z]{3})\s+(to|and|into)\s+([A-Za-z]{3})"
    match = re.search(pattern, command.lower())
    if match:
        base_currency = match.group(2).upper()
        target_currency = match.group(4).upper()
        return base_currency, target_currency
    return None, None

def processCommand(c):
    print(c)
    
    # Check for exchange rate request
    base_currency, target_currency = extract_currency(c)

    if base_currency and target_currency:
        exchange_rate_info = get_exchange_rate(base_currency, target_currency)
        speak(exchange_rate_info)

    # Check for Google search request
    elif "open google" in c.lower():
        webbrowser.open("https://google.com")
        speak("Opening Google.")

    # Check for news request
    elif "news" in c.lower():
        try:
            r = requests.get(f"https://newsapi.org/v2/top-headlines?country=us&apiKey={newsapi}")
            if r.status_code == 200:
                data = r.json()
                articles = data.get('articles', [])
                if articles:
                    for article in articles[:5]:  # Limit to 5 headlines
                        speak(article['title'])
                else:
                    speak("No news articles found.")
            else:
                speak("Failed to retrieve news.")
        except Exception as e:
            speak(f"An error occurred: {e}")

    # Check for weather request
    elif "weather" in c.lower():
        try:
            city = c.split("weather in ")[1]
            weather_info = get_weather(city)
            speak(weather_info)
        except IndexError:
            speak("Please specify the city.")
        except Exception as e:
            speak(f"An error occurred: {e}")

    # Check for exchange rate or currency conversion
    elif "exchange rate" in c.lower() or "currency" in c.lower() or "convert" in c.lower():
        try:
            words = c.split()
            base_currency = words[-3].upper()
            target_currency = words[-1].upper()
            exchange_rate_info = get_exchange_rate(base_currency, target_currency)
            speak(exchange_rate_info)
        except Exception as e:
            speak(f"Error processing currency conversion: {e}")

    # Check for exit command
    elif "exit" in c.lower():
        speak("Shutting down. Goodbye!")
        root.quit()  # Close the GUI window
        exit()

    # For other commands, use OpenAI API
    else:
        try:
            process_content = openai_process(c)
            speak(process_content)
        except Exception as e:
            speak(f"Error processing your request with OpenAI: {e}")


def listen_command():
    # Listen for voice commands.
    try:
        with sr.Microphone() as source:
            print("Listening!")
            audio = recogniser.listen(source, timeout=5, phrase_time_limit=5)
        word = recogniser.recognize_google(audio, language="en-IN")
        print(f"Recognized: {word}")
        processCommand(word)

    except sr.WaitTimeoutError:
        print("Listening timed out, no input detected.")
    except sr.UnknownValueError:
        print("Sorry, I didn't catch that.")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")
    except Exception as e:
        print(f"An error occurred: {e}")

    # Schedule the function to be called again after a delay
    root.after(1000, listen_command)  # 1000 ms = 1 second

if __name__ == "__main__":
    threading.Thread(target=delayed_speak, args=("Initializing Jarvis", 1)).start()
    root.after(0, listen_command)  # Start listening immediately
    root.mainloop()
