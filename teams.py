"""Team info."""
class Team(object):
    def __init__(self, area, name, stadium_name, address, league, division,
                 short_name=None):
        self.area = area
        self.name = name
        self.league = league
        self.division = division
        self.stadium_name = stadium_name
        self.address = address
        self._short_name = short_name

    def __hash__(self):
        return hash(self.name)

    @property
    def full_name(self):
        return "{} {}".format(self.area, self.name)

    @property
    def short_name(self):
        if self._short_name is not None:
            return self._short_name
        return self.name.replace(" ", "").lower()

    def __repr__(self):
        return self.name

    def __str__(self):
        return self.full_name

AL_EAST = lambda *args: Team(*args, league='American', division='East')
NL_EAST = lambda *args: Team(*args, league='National', division='East')
AL_CENTRAL = lambda *args: Team(*args, league='American', division='Central')
NL_CENTRAL = lambda *args: Team(*args, league='National', division='Central')
AL_WEST = lambda *args: Team(*args, league='American', division='West')
NL_WEST = lambda *args: Team(*args, league='National', division='West')

TEAMS = [
    AL_EAST('Boston', 'Red Sox', 'Fenway Park', '4 Yawkey Way Boston, MA 02215'),
    AL_EAST('New York', 'Yankees', 'Yankee Stadium', 'One East 161st Street Bronx, NY 10451'),
    AL_EAST('Baltimore', 'Orioles', 'Camden Yards', '333 West Camden Street Baltimore, MD 21201'),
    AL_EAST('Tampa Bay', 'Rays', 'Tropicana Field', '1 Tropicana Dr., St. Petersburg, FL 33705'),
    AL_EAST('Toronto', 'Blue Jays', 'Rogers Centre', '1 Blue Jays Way, Toronto, ON M5V 1J1, Canada'),

    NL_EAST('New York', 'Mets', 'Citi Field', '120-01 Roosevelt Avenue Corona, NY 11368'),
    NL_EAST('Philadelphia', 'Phillies', 'Citizens Bank Park', 'One Citizens Bank Way Philadelphia, PA 19148'),
    NL_EAST('Washington', 'Nationals', 'Nationals Park', '1500 South Capitol Street, SE Washington, DC 20003-1507'),
    NL_EAST('Miami', 'Marlins', 'Marlins Park', '501 Marlins Way, Miami, FL 33125'),
    NL_EAST('Atlanda', 'Braves', 'SunTrust Park', '755 Battery Avenue Southeast, Atlanta, GA 30339'),

    AL_CENTRAL('Chicago', 'White Sox', 'Guaranteed Rate Field', '333 W 35th St, Chicago, IL 60616'),
    AL_CENTRAL('Cleveland', 'Indians', 'Progressive Field', '2401 Ontario St, Cleveland, OH 44115'),
    AL_CENTRAL('Minnesota', 'Twins', 'Target Field', '1 Twins Way Minneapolis, MN 55403'),
    AL_CENTRAL('Detroit', 'Tigers', 'Comerica Park', '2100 Woodward Ave, Detroit, MI 48201'),
    AL_CENTRAL('Kansas City', 'Royals', 'Kauffman Stadium', '1 Royal Way, Kansas City, MO 64129'),

    NL_CENTRAL('Chicago', 'Cubs', 'Wrigley Field', '1060 W Addison St, Chicago, IL 60613'),
    NL_CENTRAL('Cincinatti', 'Reds', 'Great American Ball Park', '100 Joe Nuxhall Way, Cincinnati, OH 45202'),
    NL_CENTRAL('Milwaukee', 'Brewers', 'Miller Park', '1 Brewers Way, Milwaukee, WI 53214'),
    NL_CENTRAL('Saint Louis', 'Cardinals', 'Busch Stadium', '700 Clark Ave, St. Louis, MO 63102'),
    NL_CENTRAL('Pittsburgh', 'Pirates', 'PNC Park', '115 Federal Street Pittsburgh, PA 15212'),

    AL_WEST('Los Angeles', 'Angels', 'Angel Stadium', '2000 E Gene Autry Way, Anaheim, CA 92806'),
    AL_WEST('Houston', 'Astros', 'Minute Maid Park', '501 Crawford St, Houston, TX 77002'),
    AL_WEST('Texas', 'Rangers', 'Globe Life Park', '1000 Ballpark Way, Arlington, TX 76011'),
    AL_WEST('Seattle', 'Mariners', 'Safeco Field', '1250 1st Ave S, Seattle, WA 98134'),
    AL_WEST('Oakland', 'Athletics', 'Oadlkand-Alameda County Coliseum', '7000 Coliseum Way, Oakland, CA'),

    NL_WEST('Los Angeles', 'Dodgers', 'Dodger Stadium', '1000 Vin Scully Ave, Los Angeles, CA 90012'),
    NL_WEST('San Francisco', 'Giants', 'AT&T Park', '24 Willie Mays Plaza, San Francisco, CA 94107'),
    NL_WEST('San Diego', 'Padres', 'Petco Park', '100 Park Blvd, San Diego, CA 92101'),
    Team('Arizona', 'Diamondbacks', 'Chase Field', '401 E Jefferson St, Phoenix, AZ 85004', 'National', 'West', 'dbacks'),
    NL_WEST('Colorado', 'Rockies', 'Coors Field', '2001 Blake St, Denver, CO 80205')
]

TEAMS_BY_NAME = {t.name: t for t in TEAMS}
