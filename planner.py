#!/usr/bin/env python
from argparse import ArgumentParser
import collections
import datetime
import itertools
import json
import os
import time
from sys import stderr

import pandas
import requests
from dateutil.parser import parse as dateutil_parse


START_WEEKDAY = [3]
TRIP_LENGTH_DAYS = 5
GOOGLE_DISTANCE_URL = 'https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&key={api_key}'

MlbTeam = collections.namedtuple('Team', ['name', 'schedule', 'address'])
TEAMS = [
    MlbTeam('Red Sox', 'redsox.csv', '4 Yawkey Way Boston, MA 02215'),
    MlbTeam('Yankees', 'yankees.csv', 'One East 161st Street Bronx, NY 10451'),
    MlbTeam('Mets', 'mets.csv', '120-01 Roosevelt Avenue Corona, NY 11368'),
    MlbTeam('Phillies', 'phillies.csv', 'One Citizens Bank Way Philadelphia, PA 19148'),
    MlbTeam('Orioles', 'orioles.csv', '333 West Camden Street Baltimore, MD 21201'),
    MlbTeam('Nationals', 'nationals.csv', '1500 South Capitol Street, SE Washington, DC 20003-1507'),
]

# Too far:
#  MlbTeam('Pirates', 'pirates.csv', '115 Federal Street Pittsburgh, PA 15212'),


def build_distance_matrix():
    """ Build a two level dictionary containing the driving distance in
    meters between all stadiums. """
    print('Finding driving distances:', file=stderr)

    if os.path.exists('distances.json'):
        with open('distances.json') as handle:
            distances = json.load(handle)
            print('  cached', file=stderr)
            return distances

    distances = collections.defaultdict(dict)
    for start in TEAMS:
        for end in TEAMS:
            if start.name == end.name:
                continue

            print('  {} -> {}'.format(start.name, end.name), file=stderr)

            url = GOOGLE_DISTANCE_URL.format(
                origin=start.address, destination=end.address,
                api_key=os.environ['API_KEY'])
            resp = requests.get(url)
            resp.raise_for_status()
            resp_json = resp.json()

            distances[start.name][end.name] = (
                resp_json['rows'][0]['elements'][0]['distance']['value'])
            time.sleep(0.5)

    with open('distances.json', 'w') as handle:
        json.dump(distances, handle, indent=4, sort_keys=True)

    return distances

def load_schedules():
    """ CSV stuff """
    schedule_df = pandas.DataFrame({'team': [], 'date': []})
    schedule_dict = {}

    for team in TEAMS:
        schedule_path = os.path.join('schedules', team.schedule)
        team_schedule_df = pandas.read_csv(
            schedule_path, parse_dates=['START DATE'])
        schedule_dict[team.name] = team_schedule_df
        team_schedule_df['team'] = team.name
        team_schedule_df.rename(
            index=str, columns={'START DATE': 'date'}, inplace=True)

        schedule_df = pandas.concat(
            [schedule_df, team_schedule_df[['team', 'date']]])

    return schedule_df, schedule_dict

def build_trips(schedule_df):
    """ Build up all the possible trips. """
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
        for combo in combinations:
            if combo.count(None) == 0 and len(set(combo)) == len(combo):
                trips[start_date].append(combo)

        start_date += datetime.timedelta(days=1)

    return trips

def trip_distance(trip, distance_matrix):
    """ Calculate total distance traveled for the given trip.  """
    trip_hops = [x for x in trip if x is not None]
    hops = [(trip_hops[x-1], trip_hops[x])
            for x in range(1, len(trip_hops))]
    hop_distances = [distance_matrix[x[0]][x[1]] for x in hops]
    distance = sum(hop_distances)
    return distance

def score_trips(trips, distance_matrix):
    """ Iterate over all the trip dates and find the trip with the
    min distance. """
    for trip_date, trips in trips.items():
        best_trip = None
        avg_distance = 0

        for trip in trips:
            if trip.count(None) > 0:
                continue
            if len(set(trip)) != len(trip):
                continue

            distance = trip_distance(trip, distance_matrix)
            trip_avg_distance = (distance * 1.0) / len(trip)
            if trip_avg_distance < avg_distance or best_trip is None:
                best_trip = trip
                avg_distance = trip_avg_distance

        if best_trip:
            print('{} {}'.format(trip_date, best_trip), file=stderr)

class NoDatesSatisfyRequirements(Exception):
    pass

class DateFinder(object):
    def __init__(self, schedules):
        self.schedules = schedules

    def find_date(self, team, earliest, latest=None):
        # Default latest date to be one day after the earliest date
        schedule = self.schedules[team]
        # TODO this is slow and dumb
        for idx, date in enumerate(schedule['date']):
            date = date.to_pydatetime()
            if latest is None and earliest <= date:
                break
            elif earliest <= date <= latest:
                break
        else:
            raise ValueError("Couldn't find a date from {} to {} for the {}"
                             .format(earliest, latest, team))

        opponent = schedule.iloc[idx]['SUBJECT'].split(' at ')[0]
        return {
            'date': date,
            'opponent': opponent
        }

    def find_events(self, earliest, order):
        events = {}
        prev_date = None
        start_date = None
        for team in order:
            if prev_date is not None:
                earliest = prev_date + datetime.timedelta(days=1)
                latest = earliest + datetime.timedelta(days=1)
            else:
                latest = None
            try:
                event = self.find_date(team, earliest, latest)
                prev_date = event['date']
                events[team] = event
                if start_date is None:
                    start_date = prev_date
            except ValueError as e:
                # This means we couldn't find a schedule with all of the teams in order.
                if start_date is None:
                    # This means we couldn't find any events at all,
                    # which means we exhausted all of the events. Raise
                    # the error.
                    raise NoDatesSatisfyRequirements()
                # Otherwise, keep looking beginning with the next day.
                else:
                    tomorrow = start_date + datetime.timedelta(days=1)
                    return self.find_events(tomorrow, order)

        return start_date, events

    def find_trips(self, earliest, order):
        all_events = []
        while True:
            try:
                start_date, events = self.find_events(earliest, order)
                all_events.append(events)
                earliest = start_date + datetime.timedelta(days=1)
            except NoDatesSatisfyRequirements:
                break
        return all_events

def sublists(items, length):
    # produce all possible sublists at this length which preserve ordering
    if length == 0 or length > len(items):
        # There can't be any sublists of this length then.
        return []
    elif length == len(items):
        # Then there's only one possible answer; return it.
        return [items]
    elif length == 1:
        # Another case where there's only one possible answer.
        return [[item] for item in items]

    # Choose an element, recur on all sublists of the remaining list at length-1.
    results = []
    for i in range((len(items) - length) + 1):
        item = items[i]
        sublists_ = sublists(items[i+1:], length - 1)
        for s in sublists_:
            results.append([item] + s)
    return results

def get_args():
    parser = ArgumentParser()
    parser.add_argument("--min-games", type=int, default=4)
    parser.add_argument("--max-games", type=int, default=5)
    parser.add_argument("--required-teams", nargs="*")
    parser.add_argument("--earliest-date", type=dateutil_parse,
                        default=datetime.datetime.now())
    parser.add_argument("--dump-csv")
    return parser.parse_args()

def main():
    distance_matrix = build_distance_matrix()
    schedule_df, schedule_dict = load_schedules()
    trips = build_trips(schedule_df)

    args = get_args()
    finder = DateFinder(schedule_dict)

    # Find all orderings of either 4 or 5 teams
    orderings = []
    team_names = [t.name for t in TEAMS]
    for count in range(args.min_games, args.max_games + 1):
        orderings.extend(sublists(team_names, count))

    # Filter to those that include required teams
    for t in (args.required_teams or []):
        orderings = [o for o in orderings if t in o]

    # For each ordering we generated, reverse the order and swap Mets
    # and Yankees if the ordering contains both.
    for ordering in orderings.copy():
        orderings.append(list(reversed(ordering)))
        if 'Mets' in ordering and 'Yankees' in ordering:
            o = ordering.copy()
            mets_idx, yankees_idx = o.index('Mets'), o.index('Yankees')
            o[mets_idx] = 'Yankees'
            o[yankees_idx] = 'Mets'
            orderings.append(o)
            orderings.append(list(reversed(o)))

    # Generate trips for all orderings we determined.
    trips = {
        tuple(o): finder.find_trips(args.earliest_date, o)
        for o in orderings
    }

    trip_rows = []

    # Display all of the trips.
    for order, events in trips.items():
        if events:
            print("Dates for {}:".format(" -> ".join(order)))
            for event_set in events:
                pretty = {t: "{}, {}".format(e['opponent'], e['date'].strftime("%A %m/%d"))
                          for t, e in event_set.items()}
                print(pretty)
                trip_rows.append([None if t.name not in event_set else pretty[t.name]
                                  for t in TEAMS])
            print("\n")

    trip_rows.sort(key=lambda r: min([d for d in r if d is not None]))
    import csv, io
    sio = io.StringIO()
    writer = csv.writer(sio)
    writer.writerow([t.name for t in TEAMS])
    for row in trip_rows:
        writer.writerow(row)

    if args.dump_csv is not None:
        with open(args.dump_csv, "w") as f:
            f.write(sio.getvalue())
        print("Wrote CSV to {}".format(args.dump_csv))

    print("Generated {} trips".format(len(trip_rows)))

if __name__ == '__main__':
    main()
