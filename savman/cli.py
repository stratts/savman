from savman import databaseman, gamefind, gameman, stopwatch, datapath
from savman.vbackup import Backup
import sys
import os
import logging
import time
import argparse
from threading import Thread


def main():
    parser = argparse.ArgumentParser(
        description='Find and backup save games')
    
    parser.add_argument('-l', '--list', dest='list', action='store_true',
        help='''List found games''')
    parser.add_argument('-b', '--backupall', dest='backup_dir', type=str, 
        metavar='DIR', default=None, help='Backup saves to this directory')
    parser.add_argument('-t', '--trim', metavar=('MIN','MAX'), nargs=2, 
        type=int, default=[0,0], help='''Trim backup to MIN versions 
        when number exceeds MAX''')
    parser.add_argument('-s', '--scan', dest='scan', action='store_true',
        help='''Perform scan for new games''')
    parser.add_argument('-n', '--nocache', dest='nocache', action='store_true',
        help='''Don't use cache when scanning for games. Slower but can catch 
            games the normal scan missed''')
    parser.add_argument('-u', '--update', dest='update', action='store_true',
        help='''Check online for updated games database''')
    parser.add_argument('--debug', action='store_true', help=argparse.SUPPRESS)
    
    #sys.argv.extend('--debug'.split())

    args = parser.parse_args()
    if args.debug:
        fil.delta = True
        log.setLevel(logging.DEBUG)
    if not len(sys.argv) > 1:
        parser.print_help()
        sys.exit()
    if args.trim[0] > args.trim[1]:
            parser.error('Trim MIN must be lower than MAX')
            sys.exit(1)
    if args.backup_dir and not os.path.isdir(args.backup_dir):
        try:
            os.mkdir(args.backup_dir)
        except FileNotFoundError:
            path = os.path.normpath(args.backup_dir)
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

    if args.update:
        if dbman.check_update(): dbman.download(dbname)  

    gman = gameman.GameMan(dbman.db)
    gman.cachefile = datapath('cache')
    gman.customfile = datapath('custom.txt')
    gman.load_custom()
    if not args.nocache: gman.load_cache()
    elif not args.scan: 
        logging.error('--nocache specified without --scan')
        sys.exit(1)

    if args.scan: gman.find_games() 
    
    gman.save_cache()
    
    if args.list and gman.games:
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
    
    if args.backup_dir: 
        gman.backup_games(args.backup_dir, trim_min=args.trim[0], trim_max=args.trim[1])
        
    logging.info('Finished!')