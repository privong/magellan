# magellan library


# load configuration file and connect to the database
def initdb():
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
    scon = _MySQLdb.connect(host=Mserver, user=Muser, passwd=Mpw, db=Mdb)
    scur = scon.cursor()
    return scur


# compute the great circle distance using the haversine formula
def GreatCircDist(loc1, loc2):
    dlat = loc2[0] - loc1[0]
    dlong = loc2[1] - loc2[1]
    rdlat = _math.radians(dlat)
    rdlong = _math.radians(dlong)
    ha = _math.sin(rdlat/2) * _math.sin(rdlat/2) + \
        _math.cos(_math.radians(loc1[1])) * \
        _math.cos(_math.radians(loc1[1])) * _math.sin(rdlong/2) * \
        _math.sin(rdlong/2)
    hc = 2 * _math.atan2(_math.sqrt(ha), _math.sqrt(1-ha))
    return 6378.1 * hc


def yearid(year, other):
    return int(str(year)+str(other).zfill(2))
