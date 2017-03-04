import os
import logging
import fnmatch
import win32api
import win32file
from win32com.shell import shell, shellcon

VARIABLE = 2
PROFILE = 4

USERPROFILE = 6
APPDATA = 8
USERDOC = 10


def get_drives():
    # Get all drives except those that are network drives
    drives = win32api.GetLogicalDriveStrings().split('\x00')[:-1]
    return [ d for d in drives if not win32file.GetDriveType(d) == win32file.DRIVE_REMOTE ]

class Finder:
    def __init__(self, searchpaths=[]):
        self.excl = ['Windows','Windows.old','WINDOWS','ProgramData','AppData',
                     '$Recycle.Bin','$RECYCLE.BIN','$Windows.~WS','$Windows.~BT',
                     '$SysReset']
        self.vars = {USERPROFILE: os.environ['USERPROFILE'],
                     APPDATA: os.path.normpath(os.path.join(os.environ['APPDATA'],'..')),
                     USERDOC: shell.SHGetFolderPath(0, shellcon.CSIDL_PERSONAL, None, 0)
                     }
        self.deep = ['*/Steam/steamapps','*/Steam/userdata']
        self.searchpaths = get_drives() if not searchpaths else searchpaths
        self.tofind = {}
        self.found = {}
        self.profiles = {}
        self.dircache = {}
        self.itemdict = {}
        self.lookups = 0           

    def add_profile(self, game_id, profile_items, profile_dir=None, subdir=''):
        if not type(profile_items) == list: 
            raise TypeError('Profile items should be a list')
        location  = {'type': PROFILE, 'subdir': subdir, 
                     'pitems': set([p.lower() for p in profile_items]), 
                     'pname': profile_dir }
        self.add_location(game_id, location)

    def add_variable(self, game_id, variable, subdir=''):
        if not variable in self.vars: raise ValueError('Incorrect variable chosen')
        location = {'type': VARIABLE, 'subdir': subdir, 'variable': variable }
        self.add_location(game_id, location)

    def add_location(self, game, loc):
        if not game in self.tofind:
            self.tofind[game] = [loc]
        else: self.tofind[game].append(loc)

    def add_found(self, game, directory):
        if not game in self.found:
            self.found[game] = [directory]
        else: 
            if not directory in self.found[game]:
                self.found[game].append(directory)
        
    def has_games(self, location):
        paths = [location]
        for p in paths:
            dirname = os.path.dirname(p)
            if not dirname in paths: paths.append(dirname)
            self.dircache[p]['hasgames'] = True
            
    def import_cache(self, cache):
        for item, data in cache.items():
            if not os.path.isdir(item): continue
            data['profile'] = set(data['profile'])
            self.dircache[item] = data
        #self.dircache = cache
            
    def export_cache(self):
        cache = self.dircache.copy()
        for item, data in cache.items():
            data['profile'] = list(data['profile'])
        return cache
        
    def trim_cache(self):
        cachelist = sorted(self.dircache)       
        cache = self.dircache
        before = len(cache)
        for idx, item in enumerate(cachelist):
            if item in cache and not cache[item]['hasgames']:
                itemsep = item.count(os.sep)
                for sub in cachelist[(idx+1):]:
                    if sub in cache and sub.startswith(item + os.sep):
                        subsep = sub.count(os.sep)
                        if (subsep-itemsep) > 1: del cache[sub]                  
                    elif not sub.startswith(item): break
                    
        logging.debug('Trimmed - before: {}, after: {}'.format(before, len(cache)))
                

    def match_directory(self, root, dirprofile):
        match = False
        matched = set()
        
        # Check if any directory item matches any item in any profile
        for item in dirprofile:
            if item in self.itemdict:
                matched = matched | self.itemdict[item]

        for item in matched:
            profile = self.profiles[item]
            if profile['items'] <= dirprofile:
                # If directory name specified, check that it matches
                name = profile['name']
                if name and not root.lower().endswith(name.lower()): continue
                # Append subdir if it exists
                if profile['sub']: gamedir = os.path.join(root, profile['sub'])
                else: gamedir = root
                gamedir = os.path.normpath(gamedir)
                self.add_found(profile['game'], os.path.normpath(gamedir))  
                self.has_games(root)
                match = True
       
        return match
            
        
    def find(self):
        logging.info("Looking for games...")
        for game, data in self.tofind.items():
            for loc in data:
                searchtype = loc['type']

                # If a variable is specified we can just check it directly
                if searchtype == VARIABLE:
                    var = self.vars[loc['variable']]
                    gdir = os.path.join(var, loc['subdir'])
                    if os.path.isdir(gdir): 
                        self.add_found(game, os.path.normpath(gdir))

                # Otherwise we'll need to search for a matching directory
                elif searchtype == PROFILE:    
                    profile = { 'game': game, 'items': loc['pitems'], 
                                'name': loc['pname'], 'sub': loc['subdir'] }
                    self.profiles[game] = profile
                    # Add each profile item to dictionary and associate with game
                    for item in profile['items']:
                        if not item in self.itemdict:
                            self.itemdict[item] = {game}
                        else: self.itemdict[item].add(game)

        self.search()
        return self.found


    def search(self):
        rootnum = 0
        for directory, data in self.dircache.items():
            self.match_directory(directory, data['profile'])    # Check matches with dirs in cache   
        for path in self.searchpaths:
            path = os.path.normpath(path)
            for root, dirs, files in os.walk(path):  
                rootnum += 1          
                rel = os.path.relpath(root, path)
                if rel.count(os.sep) >= 3: del dirs[:]     # Only 3 folders deep  
                   
                for item in self.excl:
                    if item in dirs: del dirs[dirs.index(item)]
                    
                if (self.dircache and root in self.dircache and not     # If we've searched before
                        self.dircache[root]['hasgames']):               # and not found any games
                    for d in reversed(dirs):
                        droot = os.path.join(root, d)                   # Stop searching all folders
                        if droot in self.dircache: dirs.remove(d)       # that aren't new
                            
                dirprofile = set([e.lower() for e in files+dirs])
                self.dircache[root] = {'profile': dirprofile, 'hasgames': False}    # Add to cache
                if rel=='.': self.has_games(root)

                if self.match_directory(root, dirprofile): del dirs[:]  # Stop searching if match
    
                for item in self.deep:
                    if fnmatch.fnmatch(root, os.path.normpath(item)) and not rel=='.':
                        self.searchpaths.append(root)
                        self.has_games(root)
                        
                #print(root)
        
        logging.debug('Search paths: {}'.format(', '.join(self.searchpaths)))                    
        logging.debug('Root count: {}'.format(rootnum))


                        
