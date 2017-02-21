from savman import gamefind
import os
import gzip
import string
import json
import yaml
import sys
import fnmatch
import logging
import hashlib
from savman.vbackup import Backup

class InvalidIdError(Exception): pass

class Game:
    def __init__(self, gid, name):
        self.id = gid
        self.name = name
        self.locations = []

class GameLocation:
    def __init__(self, path = None, include = None, exclude = None):
        self.path = path
        self.include = include
        self.exclude = exclude
        
class GameMan:
    def __init__(self, database):
        self.games = {}
        self.backups = {}                   #Keys: game id, Values: backup path
        self.db = database
        self.finder = gamefind.Finder()
        self.cachefile = ''
        self.customfile = ''
        self.customdirs = set()
        
        if not database:
            logging.error('No database loaded, exiting')
            sys.exit(1)

    def save_cache(self, file=None):
        if not file: file = self.cachefile
        games_json = {}
        for game, data in self.games.items():
            games_json[game] = [ loc.__dict__ for loc in data.locations ]
        #print(games_json)
        with gzip.open(file, 'wt') as cfile:
            self.finder.trim_cache()
            json.dump({'games': games_json, 'dirs': self.finder.export_cache(),
                'backups': self.backups}, cfile)

    def load_cache(self, file=None, dircache=True, cleargames=False):
        if not file: 
            if not self.cachefile: raise TypeError('No cache file specified')
            file = self.cachefile
        try:
            with gzip.open(file, 'rt') as cfile:
                cache = json.load(cfile)
                cgames = cache['games']
                if dircache: self.finder.import_cache(cache['dirs'])

            # Check that previously found game locations still exist
            for game, data in cgames.copy().items():
                for location in reversed(data):
                    path = location['path']
                    if not os.path.isdir(path) or path in self.customdirs: 
                        data.remove(location)
                if not data: del cgames[game]
            # Check that backups still exist
            for game, backups in cache['backups'].copy().items():
                for backup in reversed(backups):
                    if not os.path.isfile(backup): backups.remove(backup)
                if not backups: del cache['backups'][game]
            self.backups = cache['backups']

            if not cleargames:
                for item, data in cgames.items():
                    if not item in self.games and item in self.db['games']:
                        game = Game(item, self.db['games'][item]['name'])
                        for loc in data:
                            game.locations.append(GameLocation(loc['path'], 
                                loc['include'], loc['exclude']))
                        self.games[item] = game

            if self.backups: 
                logging.info( 'Loaded {} games and {} backups from cache'.format(len(self.games), 
                    len(self.backups)) )
            else: logging.info( 'Loaded {} games from cache'.format(len(self.games)) )

        except FileNotFoundError: 
            logging.info('Cache file not loaded (file not found)')
            return False
            
    def load_custom(self, file=None):
        if not file: file = self.customfile
        else: self.customfile = file
        if not os.path.isfile(file): return
        self.customdirs = set()
        with open(file, 'r') as cfile:
            for item in yaml.safe_load_all(cfile):
                if not {'name', 'directory'} <= set(item): continue
                name = item['name']
                game_id = autoid(name)
                include = list(item['include']) if 'include' in item else None
                exclude = list(item['exclude']) if 'exclude' in item else None
                directory = os.path.normpath(str(item['directory']))             
                
                if os.path.isdir(directory): 
                    self.customdirs.add(directory)
                    location = GameLocation(directory, include, exclude)
                    if not game_id in self.games: self.games[game_id] = Game(game_id, name)
                    self.games[game_id].locations.append(location)
                    
                
    def find_games(self):
        finder = self.finder
        db = self.db
        games =  db['games']
        locations = db['locations']
        self.games = {}
        self.load_custom()

        # Game locations are stored in a dict, where each key is a tuple 
        # with the first value set to the associated game ID and the second  
        # value set to the location ID (or number). 
        
        for loc, data in locations.items():
            variables = {'userdoc':gamefind.USERDOC, 
                'userprofile': gamefind.USERPROFILE,
                'appdata': gamefind.APPDATA}
            if data['type'] == 'variable':
                finder.add_variable(loc, variables[data['variable']],
                    data['subdir'])
            if data['type'] == 'profile':
                finder.add_profile(loc, data['profile_items'], 
                    profile_dir=data['profile_dir'], subdir=data['subdir'])          

        finder.find()

        found = set()
        for find, dirs in finder.found.items():
            loc = locations[find]       # Retrieve location data from database
            dirs = [ d for d in dirs if not d in self.customdirs ]
            gameid, locid = find        # Split tuple
            if not gameid in self.games:
                game = Game(gameid, games[gameid]['name'])
                self.games[gameid] = game
                found.add(gameid)
            else: game = self.games[gameid]
            for directory in dirs:
                location = GameLocation(directory, loc['include'], loc['exclude'])
                game.locations.append(location)
        
        logging.info("{} games found".format(len(found)))
            

    def backup_games(self, dst, games=[], trim_min=None, trim_max=None):
        if not os.path.isdir(dst):
            raise FileNotFoundError("Destination does not exist: '{}'".format(location))
        if not games: games = [ g for g in self.games ]
        logging.info('Starting game backup...')
        if not games:
            logging.info('No games to backup')
            return
        #pool = multiprocessing.Pool(threads)
        for game in sorted(games):
            if not game in self.games: 
                logging.error("Could not backup '{}' - game ID not in database".format(game))
                continue
            for loc in self.games[game].locations:    
                # Append count if more than one directory found
                dirhash = hashlib.sha1(loc.path.encode()).hexdigest()
                name = '{}_{}.savman.vbak'.format(game, dirhash.upper()[:6]) 
                path = os.path.join(dst, name)
                backup = Backup(file=path, id=game)
                backup.build(src=loc.path, include=loc.include,
                    exclude=loc.exclude)
                backup.save()
                if trim_min and trim_max: backup.autotrim(trim_min, trim_max)

        #pool.close()
        #pool.join()

    def load_backups(self, location):
        self.backups = {}
        for item in os.listdir(location):
            path = os.path.realpath(os.path.join(location, item))
            if os.path.isfile(path):
                if fnmatch.fnmatch(item, '*.savman.vbak'):
                    backup = Backup(path)
                    if backup.id in self.db['games']:
                        if not backup in self.backups: self.backups[backup.id] = [path]
                        else:  self.backups[backup.id].append(path)
        logging.info("Loaded {} backups from '{}'".format(len(self.backups), location))

    def restore_backup(self, game_id, dst, source=None):
        try: backups = self.backups[game_id]
        except KeyError:
             raise InvalidIdError("No backup found for game")
        if len(backups) > 1:
            if not source:
                raise TypeError('Source location required as backup has multiple locations')
        else: 
            backup = Backup(backups[0])
            backup.restore(dst)

    def restore_game(self, game_id, dst=None, source=None, target=None):
        gid = next((g for g in self.games if g.lower() == game_id.lower()), game_id)
        try: game = self.games[gid]
        except KeyError: 
            raise InvalidIdError("Not found in current games")
        if len(game.locations) > 1:
            if not target: 
                raise TypeError('Target location required as game has multiple locations')
        else: 
            if dst: self.restore_backup(gid, dst, source)
            else: self.restore_backup(gid, game.locations[0].path, source)       


def autoid(name):
    wlist = []
    name = name.replace('-',' ')
    subabbr = ''
    replace = {'II':'2', 'III':'3', 'IV':'4', 'V':'5', 'VI':'6', 'VII':'7', 'VIII':'8',
            'IX':'9', 'X':'10', 'XI':'11', 'XII':'12', 'XIII':'13', '&':'And','HD':'HD'}
    valid = list(string.ascii_letters+string.digits)+list(replace)
    split = name.split(':', maxsplit=1)
    if len(split) > 1 and len(name) > 32:
        subs = split[1].strip().split(' ')
        if len(subs) > 1:
            for sub in subs:
                sub = ''.join([ x for x in list(sub) if x in valid ])
                if sub: subabbr += replace[sub] if sub in replace else sub[0].upper()
            name = split[0]
        
    for word in name.split(' '):
        if word.lower() == 'the': continue
        chars = [ x.lower() for x in list(word) if x in valid ]
        if chars: chars[0] = chars[0].upper()
        new = ''.join(chars)
        if new.upper() in replace: wlist.append(replace[new.upper()])
        else: wlist.append(new)

    wlist.append(subabbr)
    newname = ''.join(wlist)
    return newname      
