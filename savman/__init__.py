# -*- coding: utf-8 -*-

__author__ = 'strata8'
__email__ = 'strata8@outlook.com'
__version__ = '0.0.1'

import os
import sys

def datapath(*paths):
    return os.path.join(datadir, *paths)

if hasattr(sys, 'frozen'): 
    frozen = True
    curdir = os.path.dirname(sys.executable)
    #datadir = os.path.join(os.environ['LOCALAPPDATA'], 'Savman')
    datadir = os.path.normpath(os.path.join(curdir, '..', 'data'))
else: 
    frozen = False
    localappdata = os.getenv('LOCALAPPDATA')
    datadir = os.path.join(localappdata, 'Savman')

if not os.path.isdir(datadir): os.mkdir(datadir)