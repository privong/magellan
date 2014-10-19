# magellan library

import math,ConfigParser,MySQLdb

# load configuration file and connect to the database
def initdb():
  # load information from the configuration file
  config=ConfigParser.RawConfigParser()
  config.read('.magellan')
  if not(config.get('Server Config','server')) or not(config.get('Server Config','user')) or not(config.get('Server Config','password')) or not(config.get('Server Config','db')):
    sys.stderr.write('Configuration file error. Please check the configuration file.\n')
    sys.exit(-1)
  else:
    Mserver=config.get('Server Config','server')
    Muser=config.get('Server Config','user')
    Mpw=config.get('Server Config','password')
    Mdb=config.get('Server Config','db')
  # create a catabase connection
  scon=MySQLdb.connect(host=Mserver,user=Muser,passwd=Mpw,db=Mdb)
  scur=scon.cursor()
  return scur

# compute the great circle distance using the haversine formula
def GreatCircDist(loc1,loc2):
  dlat=loc2[0]-loc1[0]
  dlong=loc2[1]-loc1[1]
  rdlat=math.radians(dlat)
  rdlong=math.radians(dlong)
  ha=math.sin(rdlat/2) * math.sin(rdlat/2) + math.cos(math.radians(loc1[1])) * math.cos(math.radians(loc1[1]))*math.sin(rdlong/2) * math.sin(rdlong/2)
  hc= 2 * math.atan2(math.sqrt(ha), math.sqrt(1-ha))
  return 6378.1*hc

def yearid(year,other):
  return int(str(year)+str(other).zfill(2))
