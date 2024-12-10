import requests
from datetime import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import os
from django.shortcuts import redirect, render
import requests
import random
import sys
import isodate
import yfinance as yf
import http.client
import json
from datetime import datetime, timedelta






# Google Calendar API Scope
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def home(request):
    # OpenWeatherMap API details
    api_key = os.getenv("API_KEY_WEATHER")  # Replace with your actual OpenWeatherMap API key
    latitude = 27.800583
    longitude = -97.396378

    # URLs for Current Weather and Forecast APIs
    current_weather_url = 'https://api.openweathermap.org/data/2.5/weather'
    forecast_url = 'https://api.openweathermap.org/data/2.5/forecast'

    # Fetch current weather
    current_params = {
        'lat': latitude,
        'lon': longitude,
        'units': 'imperial',
        'appid': api_key
    }
    current_response = requests.get(current_weather_url, params=current_params)
    if current_response.status_code != 200:
        return render(request, 'mirror/error.html', {'error': f"Failed to fetch current weather: {current_response.text}"})

    current_data = current_response.json()
    current_weather = {
        'temp': current_data['main']['temp'],
        'weather': current_data['weather'][0]['description'],
        'icon': current_data['weather'][0]['icon'],
    }

    # Fetch forecast data
    forecast_response = requests.get(forecast_url, params=current_params)
    if forecast_response.status_code != 200:
        return render(request, 'mirror/error.html', {'error': f"Failed to fetch forecast: {forecast_response.text}"})

    forecast_data = forecast_response.json()
    forecast_list = [
        {
            'datetime': item['dt_txt'],
            'temp': item['main']['temp'],
            'weather': item['weather'][0]['description'],
            'icon': item['weather'][0]['icon']
        }
        for item in forecast_data['list'][:5]
    ]

    # Fetch sports headlines and details using scraping
    articles = scrape_featured_stories("https://www.foxsports.com")  # Replace URL with the actual one
   
    # Fetch calendar events
    calendar_events = fetch_calendar_events()
    
    zen_saying = get_zen_saying()

    # Fetch NY Times headlines
    nytimes_headlines = fetch_nytimes_headlines()
    
     # Default stock tickers
    stock_tickers = ["AAPL", "GOOGL", "MSFT", "MMLP"]
    

    stock_data = []
    for ticker in stock_tickers:
        data = get_yahoo_stock_data(ticker)
        if data:
            stock_data.append(data)
    #print(f"Stock data passed to template: {stock_data}")

    # Fetch sports-headline data
    #stock_data = [get_stock_data(ticker) for ticker in stock_tickers]

    
    
          
    context = {
        'current': current_weather,
        'forecast': forecast_list,
        'events': calendar_events,
        'nytimes_headlines': nytimes_headlines,
        'zen_saying': get_zen_saying(),
        "stocks": stock_data,        
        'articles': articles,
        }  # Add NY Times headlines to the
    
   
    

    print(articles)
    return render(request, 'app_dashboard/home.html', context)


def get_zen_saying():
    sayings = [
"Feelings are just visitors. Let them come and go.",
"Don’t fight with your thoughts; just observe them and they will dissolve.",
"The mind loves to create problems, but it also loves to invent solutions.",
"Be the sky, not the clouds.",
"Happiness is your nature. It is not wrong to desire it. What is wrong is seeking it outside when it is inside.",
    ]
    return random.choice(sayings)


from bs4 import BeautifulSoup
import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
import time

import requests
from bs4 import BeautifulSoup

import requests
from bs4 import BeautifulSoup

def scrape_featured_stories(url):
    """
    Scrape the title and image from specific divs with data-v-53b7e5d8.

    Args:
        url (str): The URL of the webpage to scrape.

    Returns:
        list[dict]: A list of dictionaries containing the title and image URL.
    """
    try:
        # Fetch the webpage
        response = requests.get(url)
        response.raise_for_status()  # Raise an HTTPError for bad responses

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all `a` tags with the desired class
        articles = []
        for card in soup.find_all('a', class_='card-inner-grid card-story'):
            title = None
            image_url = None

            # Extract the title from h2 with class 'card-title'
            title_element = card.find('h2', class_='card-title')
            if title_element:
                title = title_element.text.strip()

            # Extract the image URL from <img> inside the `picture` tag
            image_element = card.find('img')
            if image_element and image_element.has_attr('src'):
                image_url = image_element['src']

            # Append to the list if both title and image exist
            if title and image_url:
                articles.append({
                    'title': title,
                    'image_url': image_url
                })

        return articles

    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return []

# Example usage
if __name__ == "__main__":
    url = "https://www.foxsports.com/stories"  # Replace with the actual URL
    scraped_articles = scrape_title_and_image(url)

    for index, article in enumerate(scraped_articles, 1):
        print(f"Article {index}:")
        print(f"Title: {article['title']}")
        print(f"Image URL: {article['image_url']}")
        print("-" * 50)


    
    
def get_yahoo_stock_data(ticker):
    """
    Fetch and print all raw stock data from the Yahoo Finance API for debugging.
    """
    try:
        import yfinance as yf
        
        stock = yf.Ticker(ticker)
        stock_info = stock.info

        # Print the entire raw response to the terminal for debugging
        #print(f"Raw data fetched for {ticker}:")
        #for key, value in stock_info.items():
         #   print(f"{key}: {value}")

        # Example of extracting specific fields (you can customize these as needed)
        stock_data = {
            "symbol": stock_info.get("symbol", ticker),
            "price": stock_info.get("currentPrice"),
            "currency": stock_info.get("currency", "N/A"),
            "fifty_two_week_high": stock_info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": stock_info.get("fiftyTwoWeekLow"),
            "fifty_two_week_change": stock_info.get("52WeekChange"),
            
        }

        return stock_data
    except Exception as e:
        #print(f"Error fetching stock data for {ticker}: {e}")
        return None
    
def fetch_full_stock_data_raw(ticker):
    stock = yf.Ticker(ticker)
    #print(f"Raw object for {ticker}: {stock}")
    #print(f"Methods available: {dir(stock)}")

   
def fetch_weather():
    """
    Fetch current weather and forecast data from OpenWeatherMap API.
    """
    api_key = os.getenv("API_KEY_WEATHER")
    latitude = 27.800583
    longitude = -97.396378

    current_weather_url = 'https://api.openweathermap.org/data/2.5/weather'
    forecast_url = 'https://api.openweathermap.org/data/2.5/forecast'

    params = {'lat': latitude, 'lon': longitude, 'units': 'imperial', 'appid': api_key}
    current_response = requests.get(current_weather_url, params=params)
    forecast_response = requests.get(forecast_url, params=params)

    if current_response.status_code != 200 or forecast_response.status_code != 200:
        raise Exception("Failed to fetch weather data")

    current_data = current_response.json()
    current_weather = {
        'temp': f"{current_data['main']['temp']}°F",
        'weather': current_data['weather'][0]['description'].capitalize(),
        'icon': current_data['weather'][0]['icon']
    }

    forecast_data = forecast_response.json()
    forecast_list = [
        {
            'datetime': item['dt_txt'],
            'temp': f"{item['main']['temp']}°F",
            'weather': item['weather'][0]['description'].capitalize(),
            'icon': item['weather'][0]['icon']
        }
        for item in forecast_data['list'][:5]
    ]
    print(f"Current weather response: {current_response.json()}")
    print(f"NY Times headlines: {fetch_nytimes_headlines()}")


    return current_weather, forecast_list




SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

def generate_token():
    credentials_path = "credentials.json"  # Path to your credentials.json
    scopes = ['https://www.googleapis.com/auth/calendar.readonly']

    # Run OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
    creds = flow.run_local_server(port=0)

    # Save tokens to token.json
    with open("token.json", "w") as token_file:
        token_data = {
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "refresh_token": creds.refresh_token,
            "type": "authorized_user"
        }
        json.dump(token_data, token_file, indent=4)

    print("Token saved to token.json")

if __name__ == "__main__":
    generate_token()


from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

def fetch_calendar_events():
    # Load credentials
    creds = load_credentials()
    if not creds:
        print("Failed to load credentials.")
        return []

    try:
        # Initialize the Google Calendar API client
        service = build('calendar', 'v3', credentials=creds)
        
        # Define the time range for the next 7 days
        now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        week_later = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

        # Fetch events from the primary calendar
        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=week_later,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        # Extract and format events
        events = events_result.get('items', [])
        formatted_events = [
            {
                'summary': event.get('summary', 'No Title'),
                'start': event['start'].get('dateTime', event['start'].get('date')),
                'end': event['end'].get('dateTime', event['end'].get('date')),
                'timeZone': event['start'].get('timeZone', 'UTC'),
            }
            for event in events
        ]

        return formatted_events

    except HttpError as error:
        print(f"An error occurred: {error}")
        return []

import json
from google.oauth2.credentials import Credentials

def load_credentials():
    try:
        with open("token.json", "r") as file:
            data = json.load(file)
        return Credentials.from_authorized_user_info(data, scopes=['https://www.googleapis.com/auth/calendar.readonly'])
    except FileNotFoundError:
        print("Token file not found. Run the OAuth flow to generate token.json.")
        return None
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None

def generate_token():
    # Path to your credentials.json file
    credentials_path = "/workspaces/missydashrepo/project_dash/credentials.json"
    scopes = ['https://www.googleapis.com/auth/calendar.readonly']

    # Verify the file exists
    if not os.path.exists(credentials_path):
        print(f"Error: credentials.json not found at {credentials_path}")
        return

    # Run the OAuth flow
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, scopes)
    creds = flow.run_local_server(port=0)

    # Save the tokens to token.json
    with open("token.json", "w") as token_file:
        token_data = {
            "client_id": creds.client_id,
            "client_secret": creds.client_secret,
            "refresh_token": creds.refresh_token,
            "type": "authorized_user"
        }
        json.dump(token_data, token_file, indent=4)

    print("Token saved to token.json")

if __name__ == "__main__":
    generate_token()
    
def fetch_nytimes_headlines():
    """
    Fetch the latest NY Times headlines using the Top Stories API.
    """
    NYTIMES_API_KEY = os.getenv("NYTIMES_API_KEY")
    NYTIMES_API_URL = "https://api.nytimes.com/svc/topstories/v2/home.json"

    try:
        response = requests.get(NYTIMES_API_URL, params={"api-key": NYTIMES_API_KEY})
        response.raise_for_status()
        data = response.json()

        # Extract and handle multimedia data
        headlines = []
        for article in data.get("results", [])[:10]:
            # Check if multimedia exists
            if article.get("multimedia"):
                # Look for 'superJumbo' format
                image_url = next(
                    (media["url"] for media in article["multimedia"] if media["format"] == "Super Jumbo"),
                    None
                )
                # If 'superJumbo' not found, fallback to first image
                if not image_url:
                    image_url = article["multimedia"][0]["url"]
            else:
                # Use a placeholder if no multimedia is available
                image_url = "https://via.placeholder.com/800x400?text=No+Image+Available"

            # Append the processed headline data
            headlines.append({
                "title": article.get("title", "No Title"),
                "abstract": article.get("abstract", ""),
                "url": article.get("url", "#"),
                "image_url": image_url,
            })

        return headlines
    except Exception as e:
        print(f"Error fetching NY Times headlines: {e}")
        return []

import http.client
import json

import http.client
import json


def fetch_nfl_data(year):
    """
    Fetches the NFL weekly schedule for a specific year using RapidAPI.

    Args:
        year (str): The year for which to fetch the schedule (e.g., "2022").
    
    Returns:
        dict: Parsed JSON data if the request is successful.
        None: If the request fails.
    """
    url = "https://sports-information.p.rapidapi.com/nfl/weekly-schedule"
    querystring = {"year": year}  # Ensure year is passed as an argument
    headers = {
        "x-rapidapi-key": "ffda10e22cmshcb6236d6bc8f365p1b8b5fd75",
        "x-rapidapi-host": "sport-highlights-api.p.rapidapi.com"
    }

    try:
        response = requests.get(url, headers=headers, params=querystring)

        # Check if the response is successful
        if response.status_code == 200:
            return response.json()  # Parse and return the JSON data
        else:
            print(f"Error: Received status code {response.status_code}")
            print(f"Response: {response.text}")
            return None

    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None




       








