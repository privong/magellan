#!/usr/bin/python2
#
# sql_import.py
#
# Load a textfile (CSV) of GPS data from palm pre, put it into a SQL database
#
# UTC time,lat,long,horiz accuracy,alt,vert accuracy,speed,heading,battery

import MySQLdb
import time,sys,re,ConfigParser
import gpxpy
import magellan

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

TABLENAME="locations"

# create a catabase connection
scon=MySQLdb.connect(host=Mserver,user=Muser,passwd=Mpw,db=Mdb)
scur=scon.cursor()

i=0
d=0
filename=sys.argv[1]
infile=open(filename,"r")
if re.search('gpx',filename):
  gpx=gpxpy.parse(infile)
  for track in gpx.tracks:
    for segment in track.segments:
      for loc in segment.points:
        # set some default values we don't expect to get :(
        elev=-1
        hacc=2000 # default/conservative value
        vacc=-1
        speed=0
        heading=-1
        batt=-1
        # do we have elevation?
        if loc.has_elevation():
          elev=loc.elevation
        # make sure we don't already have an entry for this time
        scur.execute('SELECT * FROM location WHERE UTC = \'%s\'',loc.time.strftime("%Y-%m-%d %H:%M:%S"))
        recs=cursor.fetchall()
        if len(recs)>0
          # default to automatically replacing. this should be given as a user
          # switch, when everything is integrated into magellan.py
          command='DELETE FROM %s WHERE UTC = \'%s\'' % (TABLENAME,loc.time.strftime("%Y-%m-%d %H:%M:%S"))
          scur.execute(command)
          d=d+1
        # INSERT INTO location VALUES (datetime,lat,long,horizacc,alt,vertacc,speed,heading,battery)
        command='INSERT INTO %s VALUES (\'%s\',%f,%f,%f,%f,%f,%f,%f,%i)' % (TABLENAME,loc.time.strftime("%Y-%m-%d %H:%M:%S"),loc.latitude,loc.longitude,hacc,elev,vacc,speed,heading,batt)
        scur.execute(command)
        i=i+1
else:
  while infile:
    line=infile.readline()
    n=len(line)
    if n==0:
      break
    if i>0:
      s=line.split(',')
      batt=-1
      vacc=-1
      # make sure we don't already have an entry for this time
      scur.execute('SELECT * FROM location WHERE UTC = \'%s\'',loc.time.strftime("%Y-%m-%d %H:%M:%S"))
      recs=cursor.fetchall()
      if len(recs)>0
        # default to automatically replacing. this should be given as a user
        # switch, when everything is integrated into magellan.py
        command='DELETE FROM %s WHERE UTC = \'%s\'' % (TABLENAME,loc.time.strftime("%Y-%m-%d %H:%M:%S"))
        scur.execute(command)
        d=d+1
      # INSERT INTO location VALUES (datetime,lat,long,horizacc,alt,vertacc,speed,heading,battery)
      command='INSERT INTO %s VALUES (\'%s\',%f,%f,%f,%f,%f,%f,%f,%i)' % (TABLENAME,s[0].split('Z')[0],float(s[1]),float(s[2]),float(s[4]),float(s[3]),vacc,float(s[6]),float(s[5].rstrip('%\n')),batt)
      scur.execute(command)
      i=i+1
    else:
      i=1
  i=i-1 # to correct for the counting of the first row


infile.close()
# close SQL
scur.close()
scon.close()

print "%i unique records imported from %s.\n" % (i-d,sys.argv[1])
print "%i duplicate records replaced." % (d)

# rename the log file to the archive
#today=date.today()
#nn='/home/george/Documents/Projects/PalmPreTrack/logs/mygpsdata-%i%i%i.log' % (today.year,today.month,today.day)
#os.rename(filename,nn)
