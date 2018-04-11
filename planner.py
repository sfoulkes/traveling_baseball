#!/usr/bin/env python

import collections
import datetime
import itertools
import json
import os
import time

import pandas
import requests


START_WEEKDAY = [3]
TRIP_LENGTH_DAYS = 5
GOOGLE_DISTANCE_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&key={api_key}'

MlbTeam = collections.namedtuple('Team', ['name', 'schedule', 'address'])
TEAMS = [
    MlbTeam('Mets', 'mets.csv', '120-01 Roosevelt Avenue Corona, NY 11368'),
    MlbTeam('Nationals', 'nationals.csv', '1500 South Capitol Street, SE Washington, DC 20003-1507'),
    MlbTeam('Orioles', 'orioles.csv', '333 West Camden Street Baltimore, MD 21201'),
    MlbTeam('Phillies', 'phillies.csv', 'One Citizens Bank Way Philadelphia, PA 19148'),
    MlbTeam('Red Sox', 'redsox.csv', '4 Yawkey Way Boston, MA 02215'),
    MlbTeam('Yankees', 'yankees.csv', 'One East 161st Street Bronx, NY 10451')]

# Too far:
#  MlbTeam('Pirates', 'pirates.csv', '115 Federal Street Pittsburgh, PA 15212'),


def build_distance_matrix():
    """ Build a two level dictionary containing the driving distance in
    meters between all stadiums. """
    print('Finding driving distances:')

    if os.path.exists('distances.json'):
        with open('distances.json') as handle:
            distances = json.load(handle)
            print('  cached')
            return distances

    distances = collections.defaultdict(dict)
    for start in TEAMS:
        for end in TEAMS:
            if start.name == end.name:
                continue
        
            print('  {} -> {}'.format(start.name, end.name))

            url = GOOGLE_DISTANCE_URL.format(
                origin=start.address, destination=end.address,
                api_key=os.env['API_KEY'])
            resp = requests.get(url)
            resp.raise_for_status()
            resp_json = resp.json()
        
            distances[start.name][end.name] = (
                resp_json['rows'][0]['elements'][0]['distance']['value'])
            time.sleep(0.5)

    with open('distances.json', 'w') as handle:
        json.dump(distances, handle)

    return distances

def load_schedules():
    """ do something """
    schedule_df = pandas.DataFrame({'team': [], 'date': []})

    for team in TEAMS:
        schedule_path = os.path.join('schedules', team.schedule)
        team_schedule_df = pandas.read_csv(
            schedule_path, parse_dates=['START DATE'])
        team_schedule_df['team'] = team.name
        team_schedule_df.rename(
            index=str, columns={'START DATE': 'date'}, inplace=True)

        schedule_df = pandas.concat(
            [schedule_df, team_schedule_df[['team', 'date']]])

    return schedule_df

def build_trips(schedule_df):
    """ do something """
    trips = collections.defaultdict(list)

    start_date = datetime.datetime.utcnow()
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    while(start_date < max(schedule_df['date']).to_pydatetime()):
        if start_date.weekday() not in START_WEEKDAY:
            start_date += datetime.timedelta(days=1)
            continue

        trip_games = []
        for i in range(TRIP_LENGTH_DAYS):
            trip_date = start_date + datetime.timedelta(days=i)
            games = list(
                schedule_df[schedule_df['date'] == trip_date]['team'].values)
            games.append(None)
            trip_games.append(games)

        combinations = itertools.product(*trip_games)
        [trips[start_date].append(x)
         for x in combinations if x.count(None) < 3]

        start_date += datetime.timedelta(days=1)
           
    return trips

def trip_distance(trip, distance_matrix):
    """ do something """
    trip_hops = [x for x in trip if x is not None]
    hops = [(trip_hops[x-1], trip_hops[x]) 
            for x in range(1, len(trip_hops))]
    distance = sum([distance_matrix[x[0]][x[1]] for x in hops])
    return distance

def score_trips(trips, distance_matrix):
    """ do something """
    best_trip = None
    avg_distance = 0

    for trip_date in trips:
        for trip in trips[trip_date]:
            if trip.count(None) > 0:
                continue
            if len(set(trip)) != len(trip):
                continue

            distance = trip_distance(trip, distance_matrix)
            trip_avg_distance = (distance * 1.0) / len(
                [x for x in trip if x is not None])
            if trip_avg_distance < avg_distance or best_trip is None:
                best_trip = trip
                avg_distance = trip_avg_distance

        if best_trip:
            print('{} {}'.format(trip_date, best_trip))

def main():
    distance_matrix = build_distance_matrix()
    schedule_df = load_schedules()
    trips = build_trips(schedule_df)
    score_trips(trips, distance_matrix)

    import pdb; pdb.set_trace()

    # load all data
    # Find the earliest day (today)
    # Find the latest day (end of seasion)
    # Iterate over intervals, trip_length_days
    #    Find all the games in that window
    #    Iterate over all possible trips in that window

if __name__ == '__main__':
    main()
