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
#import nfl_data_py as nfl

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

    # Fetch NFL Schedule
    year = datetime.now().year
    week = 15  # Replace with dynamic week calculation if needed
    weekly_schedule_df = fetch_weekly_schedule(year, week)

    if weekly_schedule_df is not None:
        nfl_schedule = [
            {
                "home": row['home_team'],
                "home_logo": construct_team_logo_url(row['home_team']),
                "away": row['away_team'],
                "away_logo": construct_team_logo_url(row['away_team']),
                "gameDate": row['gameday'],
                "gameTime": row['gametime']
            }
            for _, row in weekly_schedule_df.iterrows()
        ]
    else:
        nfl_schedule = []

    # Other context data...
          
    context = {
        'current': current_weather,
        'forecast': forecast_list,
        'events': calendar_events,
        'nytimes_headlines': nytimes_headlines,
        'zen_saying': get_zen_saying(),
        "stocks": stock_data,        
        "nfl_schedule": nfl_schedule,
        "nfl_schedule": nfl_schedule,
        "current_week": week,
        
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


# Google Calendar API Scope
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'token.json')

def generate_token():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())

generate_token()

def load_credentials():
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
    creds = load_credentials()
    if not creds:
        print("Failed to load credentials. Run generate_token() to generate a new token.")
        return []

    try:
        service = build('calendar', 'v3', credentials=creds)
        now = datetime.utcnow().isoformat() + 'Z'
        week_later = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'

        events_result = service.events().list(
            calendarId='primary',
            timeMin=now,
            timeMax=week_later,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])
        formatted_events = []
        for event in events:
            start_time = event['start'].get('dateTime', event['start'].get('date'))
            end_time = event['end'].get('dateTime', event['end'].get('date'))
            formatted_events.append({
                'summary': event.get('summary', 'No Title'),
                'date': datetime.fromisoformat(start_time).strftime('%Y-%m-%d'),
                'time': datetime.fromisoformat(start_time).strftime('%I:%M:%S %p') if 'T' in start_time else 'All Day',
                'timeZone': event['start'].get('timeZone', 'UTC'),
                'end_time': datetime.fromisoformat(end_time).strftime('%I:%M:%S %p') if 'T' in end_time else 'All Day', 
                'htmlLink': event.get('htmlLink', '#')
            })

        return formatted_events

    except Exception as error:
        print(f"An error occurred: {error}")
        return []

# Base URL for team logos
BASE_URL = "https://www.sportshub.com/app/uploads/rdg-blocks/images/"

# Team abbreviation to URL name dictionary
TEAM_NAME_DICT = {
    "ARI": "arizona-cardinals",
    "ATL": "atlanta-falcons",
    "BAL": "baltimore-ravens",
    "BUF": "buffalo-bills",
    "CAR": "carolina-panthers",
    "CHI": "chicago-bears",
    "CIN": "cincinnati-bengals",
    "CLE": "cleveland-browns",
    "DAL": "dallas-cowboys",
    "DEN": "denver-broncos",
    "DET": "detroit-lions",
    "GB": "green-bay-packers",
    "HOU": "houston-texans",
    "IND": "indianapolis-colts",
    "JAX": "jacksonville-jaguars",
    "KC": "kansas-city-chiefs",
    "LAC": "los-angeles-chargers",
    "LAR": "los-angeles-rams",
    "LV": "las-vegas-raiders",
    "MIA": "miami-dolphins",
    "MIN": "minnesota-vikings",
    "NE": "new-england-patriots",
    "NO": "new-orleans-saints",
    "NYG": "new-york-giants",
    "NYJ": "new-york-jets",
    "PHI": "philadelphia-eagles",
    "PIT": "pittsburgh-steelers",
    "SEA": "seattle-seahawks",
    "SF": "san-francisco-49ers",
    "TB": "tampa-bay-buccaneers",
    "TEN": "tennessee-titans",
    "WAS": "washington-commanders"
}

def construct_team_logo_url(team_abbr):
    """
    Constructs the logo URL for a given team abbreviation.

    Args:
        team_abbr (str): The team abbreviation (e.g., "SF").

    Returns:
        str: The constructed URL or a placeholder if not found.
    """
    team_name_url = TEAM_NAME_DICT.get(team_abbr)
    if not team_name_url:
        return "https://via.placeholder.com/50"  # Default placeholder URL
    return f"{BASE_URL}{team_name_url}.webp"



def fetch_weekly_schedule(year, week):
    """
    Fetch the weekly schedule for a specific year and week.

    Args:
        year (int): The season year.
        week (int): The week number.

    Returns:
        pandas.DataFrame: The filtered weekly schedule.
    """
    try:
        # Fetch the full season schedule
        schedule = nfl.import_schedules([year])

        # Ensure the week column exists
        if 'week' not in schedule.columns:
            print(f"The schedule data does not contain a 'week' column.")
            return None

        # Filter for the specific week
        weekly_schedule = schedule[schedule['week'] == week]

        if weekly_schedule.empty:
            print(f"No games found for Week {week} in {year}.")
            return None

        print(f"Weekly Schedule for Week {week} ({year}):")
        print(weekly_schedule[['home_team', 'away_team', 'gameday', 'gametime']])  # Example columns to display
        return weekly_schedule

    except Exception as e:
        print(f"Error fetching schedule: {e}")
        return None

# Example usage
if __name__ == "__main__":
    year = 2024
    week = 15
    weekly_schedule = fetch_weekly_schedule(year, week)

    if weekly_schedule is not None:
        # Process the schedule further if needed
        print("Schedule fetched successfully.")










       








