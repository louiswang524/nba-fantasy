import json
import os
from pathlib import Path
from dotenv import load_dotenv
from yahoo_oauth import OAuth2

load_dotenv()

CREDENTIALS_FILE = "credentials.json"

def get_oauth() -> OAuth2:
    """Return an authenticated Yahoo OAuth2 session, refreshing token if needed."""
    if not Path(CREDENTIALS_FILE).exists():
        # First-time setup: write a minimal credentials file for yahoo_oauth
        creds = {
            "consumer_key": os.environ["YAHOO_CLIENT_ID"],
            "consumer_secret": os.environ["YAHOO_CLIENT_SECRET"],
        }
        Path(CREDENTIALS_FILE).write_text(json.dumps(creds))
    oauth = OAuth2(None, None, from_file=CREDENTIALS_FILE)
    if not oauth.token_is_valid():
        oauth.refresh_access_token()
    return oauth

def discover_leagues() -> None:
    """Print all leagues and teams for the authenticated user."""
    import requests
    oauth = get_oauth()
    url = "https://fantasysports.yahooapis.com/fantasy/v2/users;use_login=1/games;game_keys=nba/leagues?format=json"
    resp = requests.get(url, headers={"Authorization": f"Bearer {oauth.access_token}"})
    resp.raise_for_status()
    data = resp.json()
    leagues = (data["fantasy_content"]["users"]["0"]["user"][1]["games"]
               ["0"]["game"][1]["leagues"])
    for i in range(leagues["count"]):
        league = leagues[str(i)]["league"][0]
        print(f"League: {league['name']}  key={league['league_key']}")
        teams_url = f"https://fantasysports.yahooapis.com/fantasy/v2/league/{league['league_key']}/teams?format=json"
        tr = requests.get(teams_url, headers={"Authorization": f"Bearer {oauth.access_token}"})
        teams = tr.json()["fantasy_content"]["league"][1]["teams"]
        for j in range(teams["count"]):
            team = teams[str(j)]["team"][0]
            print(f"  Team: {team[2]['name']}  key={team[0][0]['team_key']}")

if __name__ == "__main__":
    print("Authenticating with Yahoo...")
    get_oauth()
    print("Auth successful. Discovering leagues...")
    discover_leagues()
    print("\nCopy YAHOO_LEAGUE_KEY and YAHOO_TEAM_KEY into your .env file.")
