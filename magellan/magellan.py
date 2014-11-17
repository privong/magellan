# magellan library

import math as _math
import ConfigParser as _ConfigParser
import MySQLdb as _MySQLdb
import sys as _sys

class magellan:
    # load configuration file and connect to the database
    def initdb(self):
        """
        initdb()
    
        Connect to the MySQL server and return an interface to the server
        """
    
        # load information from the configuration file
        config = _ConfigParser.RawConfigParser()
        config.read('.magellan')
        if not(config.get('Server Config', 'server')) or \
            not(config.get('Server Config', 'user')) or \
            not(config.get('Server Config', 'password')) or \
            not(config.get('Server Config', 'db')):
                _sys.stderr.write('Configuration file error. Please check the \
                                   configuration file.\n')
                _sys.exit(-1)
        else:
            Mserver = config.get('Server Config', 'server')
            Muser = config.get('Server Config', 'user')
            Mpw = config.get('Server Config', 'password')
            Mdb = config.get('Server Config', 'db')
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
