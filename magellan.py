"""
magellan library

Copyright (C) 2014-2018, 2020 George C. Privon

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys as _sys
import os as _os
import math as _math
import configparser as _configparser
import sqlite3 as _sqlite3


class magellan:
    def __init__(self):
        self.config = _configparser.RawConfigParser()
        if _os.path.isfile('magellan.cfg'):
            self.config.read('magellan.cfg')
        else:
            _sys.stderr.write('Could not load configuration file.\n')
            _sys.exit(-1)

        # sql db connection
        self.scon = None
        # analysis parameters
        self.travelspeed = None
        self.uniquedist = None

    # load configuration file and connect to the database
    def initdb(self):
        """
        initdb()

        Connect to the sqlite database and return an interface
        """

        # load information from the configuration file
        if not self.config.get('database', 'db_file'):
            _sys.stderr.write('Configuration file error. Please check the \
                               configuration file.\n')
            _sys.exit(-1)
        else:
            Mdb = self.config.get('database', 'db_file')
            # make sure the file exists
            assert _os.path.isfile(Mdb), "Database file does not exist."
        # create a catabase connection
        try:
            self.scon = _sqlite3.connect(Mdb)
            scur = self.scon.cursor()
            return scur
        except _sqlite3.OperationalError as e:
            _sys.stderr.write(e.args[1]+'\n')
            _sys.exit(1)

    def closedb(self):
        """
        closedb()

        Gracefully disconnect from the database.
        """
        try:
            self.scon.commit()
            self.scon.close()
        except:
            _sys.stderr.write('Error closing sqlite database.\n')
            _sys.exit(1)

    def loadanalysis(self):
        """
        loadanalysis()

        Load various analysis settings from the config file
        """
        try:
            self.travelspeed = self.config.getfloat('Analysis', 'travelspeed')
        except:
            _sys.stderr.write('Travel threshold not defined in config file.\
                              Using default of 13.5 m/s.\n')
            self.travelspeed = 13.5
        try:
            self.uniquedist = self.config.getfloat('Analysis', 'uniquedist')
        except:
            _sys.stderr.write('Distance for unique away points not defined in\
                             config file. Using default value of 60 km.\n')
            self.uniquedist = 60.

def GreatCircDist(loc1, loc2):
    """
    GreatCircDist()

    compute the great circle distance using the haversine formula
    """
    dlat = loc2[0] - loc1[0]
    dlong = loc2[1] - loc1[1]
    rdlat = _math.radians(dlat)
    rdlong = _math.radians(dlong)
    ha = _math.sin(rdlat/2)**2 + \
        _math.cos(_math.radians(loc1[0])) * \
        _math.cos(_math.radians(loc2[0])) * _math.sin(rdlong/2)**2
    hc = 2 * _math.atan2(_math.sqrt(ha), _math.sqrt(1-ha))
    return 6378.1 * hc


def yearid(year, other):
    """
    yearid()

    Generate unique yearIDs by concatenating the year with another value
    """
    return int(str(year)+str(other).zfill(2))


if __name__ == "__main__":
    _sys.stderr.write("This is a library of functions, not an interface. ")
    _sys.stderr.write("Please see the documentation.\n")
