# magellan library
#
# Copyright (C) 2014, 2015 George C. Privon
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import math as _math
import ConfigParser as _ConfigParser
import MySQLdb as _MySQLdb
import sys as _sys
import os as _os


class magellan:
    def __init__(self):
        self.config = _ConfigParser.RawConfigParser()
        if _os.path.isfile('magellan.cfg'):
            self.config.read('magellan.cfg')
        else:
            _sys.stderr.write('Could not load configuration file.\n')
            _sys.exit(-1)

    # load configuration file and connect to the database
    def initdb(self):
        """
        initdb()

        Connect to the MySQL server and return an interface to the server
        """

        # load information from the configuration file
        if not(self.config.get('Server Config', 'server')) or \
           not(self.config.get('Server Config', 'user')) or \
           not(self.config.get('Server Config', 'password')) or \
           not(self.config.get('Server Config', 'db')):
            _sys.stderr.write('Configuration file error. Please check the \
                               configuration file.\n')
            _sys.exit(-1)
        else:
            Mserver = self.config.get('Server Config', 'server')
            Muser = self.config.get('Server Config', 'user')
            Mpw = self.config.get('Server Config', 'password')
            Mdb = self.config.get('Server Config', 'db')
        # create a catabase connection
        try:
            self.scon = _MySQLdb.connect(host=Mserver, user=Muser, passwd=Mpw,
                                         db=Mdb)
            scur = self.scon.cursor()
            return scur
        except _MySQLdb.OperationalError, e:
            _sys.stderr.write(e.args[1]+'\n')
            _sys.exit(1)

    def closedb(self):
        """
        closedb()

        Gracefully disconnect from the database.
        """
        try:
            self.scon.close()
        except:
            _sys.stderr.write('Error closing MySQL database connection.\n')
            _sys.exit(1)

    def loadanalysis(self):
        """
        loadanalysis()

        Load various analysis settings from the config file
        """
        try:
            self.travelspeed = self.config.get('Analysis', 'travelspeed')
        except:
            sys.stderr.write('Travel threshold not defined in config file.\
                              Using default of 13.5 m/s.\n')
            self.travelspeed = 13.5

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
