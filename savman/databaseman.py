import json
import gzip
import hashlib
import logging
import requests
from requests.exceptions import ConnectionError

logger = logging.getLogger('database')

class Manager:
    def __init__(self):
        self.db = {}
        self.locations = {}
        self.games = {}
        self.ver = 0
        self.latest = {}
        self.latesturl = ''

    def load(self, filename): 
        logger.info("Loading database")
        try:
            with gzip.open(filename,'rt') as dbfile:
                db = json.load(dbfile)
                # JSON doesn't accept tuples as keys so locations are
                # stored in the database as 'GameID:LocationID'.                 
                db['locations'] = { 
                    tuple(key.split(':')): value for key, value in db['locations'].items()
                }
                self.db = db.copy()
                self.ver = db['version']
                self.games = self.db['games']
                self.locations = self.db['locations']
        except FileNotFoundError: logger.error('Could not load database (file not found)')

        optional = ['include','exclude','subdir','profile_dir']
        for loc, data in self.locations.items():
            for item in optional:
                if not item in data: data[item] = None

    def check_update(self):
        logger.info("Checking for database update...")
        # Download JSON file containng info about latest database
        try: req = requests.get(self.latesturl)
        except ConnectionError: 
            logging.error('Could not connect to server') 
            return False
        latest = json.loads(req.text)
        if latest['version'] > self.ver:
            logger.info('New database version available!')
            self.latest = latest
            return True    
        else:
            logger.info('No new database found')
            return False

    def download(self, filename):
        if not self.latest: self.check_update()
        logger.info('Downloading new database ({})'.format(self.latest['url']))
        try: req = requests.get(self.latest['url'])
        except ConnectionError: 
            logging.error('Could not connect to server') 
            return
        data = req.content
        # Check hash of downloaded against hash from latest info
        dbhash = hashlib.sha1(data).hexdigest()
        if dbhash == self.latest['hash']:
            logger.debug('Saving new database to file')
            with open(filename,'wb') as dbfile:
                dbfile.write(data)
            self.load(filename)
        else: 
            logger.error('Failed to download database (hash mismatch)')
