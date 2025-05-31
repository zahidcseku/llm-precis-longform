import requests
from bs4 import BeautifulSoup


def scrape_forecast_texts(state, city):
    """
    Scrapes the Melbourne weather forecast from the Bureau of Meteorology (BoM) website.

    Fetches the HTML content, parses it, and extracts the date, short summary,
    and detailed forecast text for each available day.
    """
    url = f"http://www.bom.gov.au/{state}/forecasts/{city}.shtml"
    forecast_data = []

    print(f"Fetching forecast data from: {url}\n")

    # Define a User-Agent header to mimic a browser request
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        # Send a GET request to the URL with the headers
        response = requests.get(
            url, headers=headers, timeout=10
        )  # Added timeout and headers
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # Send a GET request to the URL
        # response = requests.get(url, timeout=10)  # Added timeout
        # response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        forecast_data = {}

        # Extract forecast issued date
        date_tag = soup.find("p", class_="date")
        if date_tag:
            forecast_data["issued_at"] = date_tag.get_text(strip=True).replace(
                "Forecast issued at ", ""
            )

        # Extract forecasts for subsequent 7 days
        daily_forecasts = []
        # Find all 'div' elements with class 'day' that are not 'day main'
        other_day_divs = soup.find_all("div", class_="day")

        for day_div in other_day_divs:
            day_forecast = {}
            day_forecast["day"] = day_div.find("h2").get_text(strip=True)

            summary_dl = day_div.find("div", class_="forecast").find("dl")
            if summary_dl:
                day_forecast["precis"] = summary_dl.find(
                    "dd", class_="summary"
                ).get_text(strip=True)

            city_p = day_div.find("div", class_="forecast").find("p")
            if city_p:
                day_forecast["long_form_text"] = city_p.get_text(strip=True)

            daily_forecasts.append(day_forecast)
        forecast_data["daily_forecasts"] = daily_forecasts

        # replace "Forecast for the rest of " by date and day from "issued_at"
        date_to_update = forecast_data["issued_at"].split("on")[1]
        date_to_update = date_to_update[:-5]

        # find the key in the forecast_data dictionary that contains "Forecast for the rest of "
        for dic in forecast_data.get("daily_forecasts", []):
            if "Forecast for the rest of" in dic.get("day", ""):
                # change key
                dic["day"] = date_to_update.strip()
                break

        return forecast_data
    except requests.RequestException as e:
        print(f"An error occurred: {e}")
        return None


if __name__ == "__main__":
    import json

    state = "qld"  # State code for Victoria
    city = "brisbane"  # City name for Melbourne
    melbourne_forecasts = scrape_forecast_texts(state=state, city=city)
    print(json.dumps(melbourne_forecasts, indent=2, ensure_ascii=False))
