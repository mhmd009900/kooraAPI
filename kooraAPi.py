from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
import requests
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_request(match_type):
    today = datetime.now().strftime("%m/%d/%Y")
    url = f"https://www.yallakora.com/match-center/مركز-المباريات?date={today}#days"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')
    match_cards = soup.find_all("div", class_=lambda c: c and "matchCard" in c)

    matches = []
    for card in match_cards:
        title_tag = card.find("div", class_="title")
        league_name = title_tag.h2.get_text(strip=True) if title_tag and title_tag.h2 else ""
        excluded_keywords = ['كرة السلة', 'سيدات', 'لكرة اليد']
        if any(keyword in league_name for keyword in excluded_keywords):
            continue

        match_divs = card.find_all("div", class_=f"item {match_type} liItem")
        for match_div in match_divs:
            match_data = extract_match_data(match_div)
            match_data['league'] = league_name
            matches.append(match_data)

    return matches


def extract_match_data(match_div):
    team_a_div = match_div.find('div', class_='teams teamA')
    team_b_div = match_div.find('div', class_='teams teamB')

    team_a = team_a_div.find('p').text.strip()
    team_b = team_b_div.find('p').text.strip()

    team_a_img = team_a_div.find('img')['src'] if team_a_div.find('img') else ""
    team_b_img = team_b_div.find('img')['src'] if team_b_div.find('img') else ""

    match_status = match_div.find('div', class_='matchStatus').find('span').text.strip()
    scores = match_div.find('div', class_='MResult').find_all('span', class_='score')
    score_a = scores[0].text.strip()
    score_b = scores[1].text.strip()
    match_time = match_div.find('div', class_='MResult').find('span', class_='time').text.strip()

    return {
        'team_a': team_a,
        'team_b': team_b,
        'team_a_img': team_a_img,
        'team_b_img': team_b_img,
        'score_a': score_a,
        'score_b': score_b,
        'match_time': match_time,
        'status': match_status
    }


@app.get("/matches/{match_type}")
def get_matches(match_type: str):
    """
    match_type: one of ['future', 'now', 'ended']
    """
    if match_type not in ['future', 'now', 'ended']:
        return {"error": "match_type must be one of ['future', 'now', 'ended']"}
    matches = get_request(match_type)
    return {"matches": matches}
