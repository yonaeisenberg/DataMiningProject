from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
import os
from argparse import ArgumentParser

TIMEOUT = 10
URL = 'https://www.premierleague.com'
COLUMN_NAMES = ["Club", "Name", "Number", "Position", "Nationality", "Appearances", "Clean Sheets", "Goals", "Assists"]
DIRECTORY = "Squads_Players"


class Player:
    def __init__(self, name="", number="", position="", clean_sheets="", nationality="", appearances="", goals="",
                 assists="", team=""):
        self.team = team
        self.name = name
        self.number = number
        self.position = position
        self.nationality = nationality
        self.appearances = appearances
        self.clean_sheets = clean_sheets
        self.goals = goals
        self.assists = assists

    def __repr__(self):
        return "Name: " + str(self.name) + "; Number: " + self.number + "; Position: " + str(
            self.position) + "; Nationality: " + str(self.nationality)


def scrape_url_team(driver):
    """Scrape all match results for specified, competition, season and team"""
    urls = []
    driver.get('https://www.premierleague.com/clubs')
    webdriver_wait = WebDriverWait(driver, TIMEOUT)
    condition = EC.presence_of_element_located((By.CLASS_NAME, "indexBadge"))
    webdriver_wait.until(condition)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    tags = soup.find_all('a', class_='indexItem', href=True)
    for tag in tags:
        url = tag['href']
        urls.append(url)
    return urls


def convert_url_to_stats(url):
    words = url.split('/')
    words[-1] = 'squad'
    words[0] = URL
    new_url = '/'.join(words)
    return new_url


def convert_urls_to_stats(urls):
    return list(map(convert_url_to_stats, urls))


def scrape_team_squad(driver, url):
    team = url_to_team(url)
    driver.get(url)
    webdriver_wait = WebDriverWait(driver, TIMEOUT)
    condition = EC.presence_of_element_located((By.CLASS_NAME, "playerCardInfo"))
    webdriver_wait.until(condition)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    player_names = soup.find_all(class_='playerCardInfo')
    players = []
    for i in range(len(player_names)):
        info = player_names[i].get_text().split()
        if len(info) > 3:
            number, name, position = info[0], ' '.join(info[1:-1]), info[-1]
        else:
            number, name, position = info[0], info[1], info[2]
        p = Player(number=number, name=name, position=position, team=team)
        players.append(p)

    player_stats = soup.find_all(class_='squadPlayerStats')

    for i in range(len(player_stats)):
        info = player_stats[i].get_text().split()
        j = 1
        nationality = ''
        while info[j] != 'Appearances':
            nationality += info[j] + ' '
            j += 1
        j += 1
        appearances = info[j]
        j += 1
        if len(info[j:]) == 3:
            clean_sheets = info[-1]
            players[i].clean_sheets = clean_sheets
        elif len(info[j:]) == 5:
            clean_sheets = info[j + 2]
            goals = info[-1]
            players[i].goals = goals
            players[i].clean_sheets = clean_sheets
        elif len(info[j:]) == 4:
            goals = info[j + 1]
            assists = info[-1]
            players[i].goals = goals
            players[i].assists = assists
        players[i].nationality = nationality
        players[i].appearances = appearances
    return players


def write_to_csv(players, team):
    result = []
    filename = DIRECTORY + '/' + team + '_players.csv'
    for player in players:
        result.append(list(player.__dict__.values()))
    df = pd.DataFrame(result, columns=COLUMN_NAMES)
    df.to_csv('../Data/' + filename, index=False)


def url_to_team(url):
    return url.split('/')[-2]


def team_to_url(team, urls):
    team = team.title()
    match = [s for s in urls if team in s]
    try:
        url = match[0]
    except IndexError:
        print("Please provide a valid club name.")
        return
    return url


def main():
    arg_parser = ArgumentParser()
    arg_parser.add_argument("--team", action="store", default="", nargs="+")
    args = arg_parser.parse_args()
    team = args.team
    team = '-'.join(team)
    if not os.path.exists(DIRECTORY):
        os.mkdir(DIRECTORY)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("headless")
    with webdriver.Chrome(chrome_options=chrome_options) as driver:
        urls = scrape_url_team(driver)
    urls = convert_urls_to_stats(urls)
    with webdriver.Chrome(chrome_options=chrome_options) as driver:
        if not team:
            for url in urls:
                team = url_to_team(url)
                print("Scraping {}'s players data...".format(team))
                players = scrape_team_squad(driver, url)
                write_to_csv(players, team)
            return
        else:
            print("Scraping {}'s players data...".format(team))
            url = team_to_url(team, urls)
            if url:
                players = scrape_team_squad(driver, url)
                write_to_csv(players, team)
            return


if __name__ == '__main__':
    main()
