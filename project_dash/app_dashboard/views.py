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
from bs4 import BeautifulSoup

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
    # Fetch games for Week 1–2 (or more weeks as needed)
# Get the current week dynamically
    current_week = get_current_week()

    # Fetch games for the current week
    nfl_games = fetch_week_games(week=current_week) 

    # Construct context data
    upcoming_nfl_games = []
    for game in nfl_games:
        game_date = datetime.strptime(game['gameDate'], "%Y%m%d").strftime("%B %d, %Y")
        upcoming_nfl_games.append({
            "gameID": game['gameID'],
            "home": game['home'],
            "away": game['away'],
            "gameDate": game_date,
            "gameTime": game['gameTime'],
            "espnLink": game['espnLink'],
            "cbsLink": game['cbsLink']
        })   
    
          
    context = {
        'current': current_weather,
        'forecast': forecast_list,
        'events': calendar_events,
        'nytimes_headlines': nytimes_headlines,
        'zen_saying': get_zen_saying(),
        "stocks": stock_data,        
        "current_week": current_week,
        "upcoming_nfl_games": upcoming_nfl_games,
        
        }  # Add NY Times headlines to the
    
   
    

    #
    
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

        print(articles)
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



import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from datetime import datetime, timedelta

# Constants for paths and scopes
CREDENTIALS_PATH = "/home/missy/missydashrepo/project_dash/credentials.json"
TOKEN_PATH = "/home/missy/missydashrepo/project_dash/token.json"
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']


def generate_token():
    """
    Generates a token.json file by running the OAuth flow.
    """
    if not os.path.exists(CREDENTIALS_PATH):
        print(f"Error: credentials.json not found at {CREDENTIALS_PATH}")
        return

    try:
        # Initialize OAuth flow
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)

        # Save the token to token.json
        with open(TOKEN_PATH, "w") as token_file:
            token_data = {
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "refresh_token": creds.refresh_token,
                "type": "authorized_user"
            }
            json.dump(token_data, token_file, indent=4)
        print(f"Token saved to {TOKEN_PATH}")

    except Exception as e:
        print(f"Error during token generation: {e}")


def load_credentials():
    """
    Loads credentials from the token.json file.
    Returns a Credentials object if successful, or None if the token is missing.
    """
    try:
        with open(TOKEN_PATH, "r") as token_file:
            data = json.load(token_file)
        return Credentials.from_authorized_user_info(data, scopes=SCOPES)
    except FileNotFoundError:
        print(f"Error: token.json not found at {TOKEN_PATH}. Run the OAuth flow to generate it.")
        return None
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None


def fetch_calendar_events():
    """
    Fetches events from the Google Calendar API for the next 7 days.
    Returns a list of events with their details.
    """
    creds = load_credentials()
    if not creds:
        print("Failed to load credentials. Run generate_token() to generate a new token.")
        return []

    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.utcnow().isoformat() + 'Z'  # Current time in UTC
        week_later = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

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


if __name__ == "__main__":
    # Check if token exists; if not, generate one
    if not os.path.exists(TOKEN_PATH):
        print("Token not found. Generating a new one...")
        generate_token()

    # Fetch and display calendar events
    events = fetch_calendar_events()
    if events:
        print("Upcoming Events:")
        for event in events:
            print(f"Title: {event['summary']}")
            print(f"Start: {event['start']} | End: {event['end']} | TimeZone: {event['timeZone']}")
            print("-" * 50)
    else:
        print("No events found.")

    
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



import requests

from datetime import datetime, timedelta

def get_current_week():
    """
    Determine the current NFL week (Sunday to Sunday).
    The NFL 2024 season starts on Sunday, September 8, 2024 (adjust as necessary).
    """
    # NFL season start date
    season_start_date = datetime(2024, 9, 8)  # First Sunday of the NFL season
    today = datetime.now()

    # Calculate the number of days since the season started
    days_since_start = (today - season_start_date).days

    if days_since_start < 0:
        # If before the season start, return week 0
        return 0

    # Determine the current week (weeks start on Sunday)
    current_week = (days_since_start // 7) + 1

    # Adjust to ensure weeks run Sunday to Sunday
    if today.weekday() < 6:  # If today is not Sunday
        current_week -= 1

    return current_week + 2


import requests

def fetch_games_from_api(week, season=2024, season_type="reg"):
    """
    Helper function to fetch games for a specific week from the API.
    """
    url = "https://tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com/getNFLGamesForWeek"
    headers = {
        'x-rapidapi-key': "c95415fdc2msh4b509827cdda6cfp1c3042jsn21c6a2c064a6",  # Replace with your actual API key
        'x-rapidapi-host': "tank01-nfl-live-in-game-real-time-statistics-nfl.p.rapidapi.com"
    }
    params = {
        "week": week,
        "seasonType": season_type,
        "season": season
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()  # Raise HTTPError for bad responses
        data = response.json()
        return data.get("body", [])  # Return game data or an empty list if not found
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for Week {week}: {e}")
        return []


def fetch_week_games(week, season=2024, season_type="reg"):
    """
    Fetch games for a single week using the helper function.
    """
    return fetch_games_from_api(week, season, season_type)


def fetch_nfl_games(start_week, num_weeks, season=2024, season_type="reg"):
    """
    Fetch games for multiple weeks by calling the helper function in a loop.
    """
    all_games = []
    for week in range(start_week, start_week + num_weeks):
        print(f"Fetching games for Week {week}...")
        week_games = fetch_games_from_api(week, season, season_type)
        all_games.extend(week_games)
    return all_games









       








