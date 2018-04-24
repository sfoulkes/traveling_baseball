"""Script to download all team schedules"""
from os.path import dirname, join, exists
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from teams import TEAMS

def download_home_schedule(team):
    print("Getting schedule CSV for {}".format(team))
    schedule_page_url = ("https://www.mlb.com/{}/fans/downloadable-schedule"
                         .format(team.short_name))
    schedule_page_response = requests.get(schedule_page_url)
    schedule_page_response.raise_for_status()

    schedule_page_html = schedule_page_response.content.decode()
    schedule_page_soup = BeautifulSoup(schedule_page_html, "html.parser")

    for link in schedule_page_soup.find_all('a'):
        if 'Download Home Game Schedule' in link.get_text():
            break
    else:
        raise RuntimeError("No home game schedule download link")

    parsed_url = urlparse(link.get("href"))
    csv_url = "https://www.ticketing-client.com" + parsed_url.path

    csv_response = requests.get(csv_url)
    csv_response.raise_for_status()

    return csv_response.content.decode()

def download_schedules(directory, force=False):
    for team in TEAMS:
        csv_path = join(directory, team.short_name + ".csv")
        if exists(csv_path) and not force:
            print("Schedule for {} already downloaded".format(team))
            continue

        csv_text = download_home_schedule(team)
        with open(csv_path, "w") as f:
            f.write(csv_text)

if __name__ == '__main__':
    download_schedules(join(dirname(__file__), "schedules"))
