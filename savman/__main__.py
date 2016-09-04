from savman import databaseman, gamefind, gameman, cli, datapath
import timeit
import sys
import os
import logging
from logging.handlers import TimedRotatingFileHandler
import time
import argparse
import shutil
from threading import Thread
from savman.vbackup import Backup

class Ticker():
    def __init__(self):
        self.stime = time.time()
    def reset(self):
        self.stime = time.time()
    def get(self):
        elapsed = time.time()-self.stime
        return round(elapsed*1000)
        
class ContextFilter(logging.Filter):
    def __init__(self, name=""):
        super().__init__(name)
        self.tick = Ticker()
        self.dtick = Ticker()
        self.delta = False
    def filter(self, record):   
        #elapsed = round(time.process_time()*1000)      
        if self.delta:
            total = str(self.tick.get()).ljust(5)
            delta = str(self.dtick.get()).ljust(4)
            record.tick = '{} {}'.format(total, delta) 
            self.dtick.reset()
        else: record.tick = str(self.tick.get()).ljust(5)
        return True
    
        
class StreamToLogger(object):
   def __init__(self, logger, log_level=logging.INFO):
      self.logger = logger
      self.log_level = log_level
      self.linebuf = ''
 
   def write(self, buf):
      for line in buf.rstrip().splitlines():
         self.logger.log(self.log_level, line.rstrip())     

def run():
    # Copy included files to data directory
    data = os.path.join(os.path.dirname(__file__), 'data')

    if not os.path.isfile(datapath('custom.txt')):
        shutil.copy( os.path.join(data, 'custom.txt'), datapath() )
    if not os.path.isfile(datapath('gamedata')):
        shutil.copy( os.path.join(data, 'gamedata'), datapath() )

    logfile = datapath('savman.log')

    logging.getLogger("requests").setLevel(logging.WARNING)

    log = logging.getLogger()
    log.setLevel(logging.INFO)
    log.name = 'main'

    tick = Ticker()

    formatter = logging.Formatter('%(tick)s %(levelname)s: %(message)s', datefmt='%H:%M:%S')
    conformatter = logging.Formatter('%(levelname)s: %(message)s', datefmt='%H:%M:%S')

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(conformatter)
    #ch.level = logging.INFO
    fil = ContextFilter()
    ch.addFilter(fil)
    log.addHandler(ch)

    fh = logging.FileHandler(logfile, mode='a')
    fh.setFormatter(formatter)
    #fh.level = logging.INFO
    log.addHandler(fh)

    stderr_logger = logging.getLogger('STDERR')
    sl = StreamToLogger(stderr_logger, logging.ERROR)
    sys.stderr = sl

    with open(logfile, 'w') as lfile:
        start_time = time.strftime('%Y/%m/%d %H:%M:%S', time.gmtime())
        lfile.write('Started new log at {}\n'.format(start_time))
        
    cli.main()

if __name__ == '__main__':
    run()
    