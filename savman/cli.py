'''A utility for backing up and restoring saved games.

Usage:
  savman list [--backups]
  savman scan [--nocache]
  savman update
  savman load <directory>
  savman backup <directory> [<game>] [options]  
  savman restore <game> [<directory>] [options]
  savman -h | --help
  
Commands:
  list              Show a list of games or backups
  scan              Perform a scan for games
  update            Check for a database update
  load              Load backups from directory
  backup            Backup all games to directory, or single game if specified
  restore           Restore game to either save location or specified directory

Options:
  -h --help         Display this screen 
  --scan            Perform a scan for games
  --nocache         Scan without cache, slower but can find games the
                    regular scan missed
  --update          Check for database update
  --max <count>     Maximum number of versions to keep (default: 10)
  --min <count>     Number of versions to trim to when max is exceeded (default: 5)
  --source <num>    Game location to restore or backup from
  --target <num>    Game location to restore to
'''
from savman import databaseman, gameman, datapath, __version__
import sys
import os
import logging
import time
from docopt import docopt
from threading import Thread

def run():
    print('savman', __version__)

    if '--debug' in sys.argv:
        sys.argv.remove('--debug')
        log = logging.getLogger()
        log.setLevel(logging.DEBUG)

    args = docopt(__doc__, version='savman {}'.format(__version__))

    if args['backup'] and args['<directory>'] and not os.path.isdir(args['<directory>']):
        try:
            os.mkdir(args['<directory>'])
        except FileNotFoundError:
            path = os.path.normpath(args['<directory>'])
            parser.error("Could not create '{}' as directory '{}' does not exist".format(
                path, os.path.dirname(path)
            ))
            sys.exit(1)
    
    dbman = databaseman.Manager()
    dbman.latesturl = 'http://strata.me/latestdb.json'
    dbname = datapath('gamedata')
    #dbname = datapath('dummydataz')
    if not os.path.isfile(dbname) and hasattr(sys, 'frozen'):
        shutil.copy(os.path.join(sys._MEIPASS, 'gamedata'), dbname)
    dbman.load(dbname)

    if args['update'] or args['--update']: dbman.check_update()
    if dbman.update: dbman.download(dbname) 

    gman = gameman.GameMan(dbman.db)
    gman.cachefile = datapath('cache')
    gman.customfile = datapath('custom.txt')

    gman.load_custom()
    gman.load_cache(dircache=not args['--nocache'], cleargames=dbman.update)
    # Clear cache and rescan when database updated
    if args['scan'] or args['--scan'] or dbman.update: gman.find_games() 

    if args['load']:
        gman.load_backups(args['<directory>'])

    if args['restore']:
        try:
            gman.restore_game(args['<game>'], args['<directory>'], args['--source'],
                args['--target'])
        except gameman.InvalidIdError as e:
            logging.error("Could not restore '{}': {}".format(args['<game>'], e))
            sys.exit(1)
    
    gman.save_cache()
    
    if args['list'] and gman.games:
        maxname = max([len(game.name) for game in gman.games.values()])
        maxid = max([len(game.id) for game in gman.games.values()])
        print('\nName', ' '*(maxname-4), 'ID', ' '*(maxid-2), 'Locations')
        print('-'*(maxname)+' ', '-'*(maxid)+' ', '-'*(maxid))
        for item, data in sorted(gman.games.items()):   
            locnum = len(data.locations)
            for index, location in enumerate(data.locations):
                #bak = Backup()
                #bak.build(location.path, location.include, location.exclude) 
                #size = bak.curver.size/1000
                #if size < 1000: sizet = ' ({} KB)'.format(round(size))
                #else: sizet = ' ({} MB)'.format(round((size/1000), 1))

                namelen = len(data.name)
                idlen = len(data.id)
                if locnum > 1: prefix = '[{}] '.format(index+1)
                else: prefix = ''
                if index == 0:
                    print(data.name, ' '*((maxname-namelen)+2), data.id, 
                        ' '*((maxid-idlen)+2), prefix, location.path, sep='')    
                else: print(' '*(maxname+2), ' '*(maxid+2), prefix, location.path, sep='')
                
                #print('*', location.path, sizet)
        print('\n{} games in total.\n'.format(len(gman.games)))
    
    if args['backup'] and args['<directory>']: 
        if args['<game>']: game = [args['<game>']]
        else: game = None
        minver = 5
        maxver = 10
        try:
            if args['--min']: minver = int(args['--min'])
            if args['--max']: maxver = int(args['--max'])
        except ValueError:
            logging.error("Argument for '--max' and '--min' must be a number")
            sys.exit(1)
        if minver >= maxver: 
            logging.error("Value for '--min' must be under '--max' (min: {}, max: {})".format(
                minver, maxver
            ))
            sys.exit(1)
        gman.backup_games(args['<directory>'], games=game, trim_min=minver, trim_max=maxver)
        
    logging.info('Finished!')