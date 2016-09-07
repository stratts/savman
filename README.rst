===============================
Savman
===============================

A utility for backing up and restoring saved games


Licensed under the MIT license

Features
--------

* Fast scanning (< 0.1s) 
* Incremental backup with versioning
* Automatic save restore
* Supports multiple game locations (WIP) 

Installation
------------
::

  python setup.py install

**OR**

::

  pip install <path-to-zip>

**Dependencies**

* pyyaml
* requests
* pypiwin32
* tqdm
* docopt

Usage
-----

Scan for games::

  savman scan

Backup all saves::

  savman backup C:\SaveBackup

Backup specific save::

  savman backup C:\SaveBackup MyAwesomeGame

Load backups from directory::

  savman load C:\SaveBackup

Restore save::
   
   savman restore MyAwesomeGame

Contributing
------------

There are various ways you can help out - anything is appreciated!

* Add a bug report or feature request under 'Issues'
* Add a new game to the `game database <https://github.com/strata8/savman-db>`_ 
* Fork the repository and help fix bugs or add features


Credits
-------

* GameSave.Info - Provided the majority of the save location data