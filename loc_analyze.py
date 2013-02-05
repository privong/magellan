#!/usr/bin/python2
#
# loc_analyze.py
#
# Provide a (weekly/monthly) analysis of Palm Pre tracking information.
# The information will be retreived from an SQL database
#
# USAGE: loc_anaylze.py week/month [week#/month#] [year]
# week/month must be selected to specify weekly or monthly analysis
# If neither is specified, the most recent full week/month will be used.
# If only week/month is specified, the current year is assumed.

import MySQLdb
import sys
import time
import math
import ConfigParser

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

from datetime import date

TABLENAME="locations"

TRAVELTHRESH=13.5 # speed threshold which determines if you're "traveling" or "away" (in m/s)

htime=0		# home time in minutes
atime=0		# away time in minutes
ttime=0		# travel time in minutes

# process arguments, decide which week and year we are using.
# how many arguments do we have?
today=date.today()
nargs=len(sys.argv)
if nargs==1:
  # default to week mode, and use the previous week
  mode='week'
  week=(today.isocalendar())[1]-1
  year=(today.isocalendar())[0]
if nargs>1:
  # we've specified a mode
  if sys.argv[1]=='week':
    mode='week'
    if nargs==2:
      week=(today.isocalendar())[1]-1
      year=(today.isocalendar())[0]
      if week<1:
        # we need to figure out what the last week of the past year was
        year=year-1
        week=(date(year,12,31).isocalendar())[0]
    elif nargs==3:
      week=int(sys.argv[2])
      year=(today.isocalendar())[0]
    elif nargs==4:
      week=int(sys.argv[2])
      year=int(sys.argv[3])
  elif sys.argv[1]=='month':
    mode='month'
    if nargs==2:
      month=today.month-1
      year=(today.isocalendar())[0]
      if month<1:
        month=12
        year=year-1
    elif nargs==3:
      month=int(sys.argv[2])
      year=(today.isocalendar())[0]
    elif nargs==4:
      month=int(sys.argv[2])
      year=int(sys.argv[3])

scon=MySQLdb.connect(host=Mserver,user=Muser,passwd=Mpw,db=Mdb)
cursor=scon.cursor()

# get home location from the 'homeloc' database
# there should be a better way to select this...
if mode=='week':
  print "Loading home location for week %i of %i..." % (week,year)
  command='SELECT * FROM homeloc where (YEAR(STARTDATE) < %i AND (YEAR(ENDDATE) > %i OR YEAR(ENDDATE)=0000)) OR (YEAR(STARTDATE)=%i AND WEEK(STARTDATE,1)<%i AND (YEAR(ENDDATE)>%i or YEAR(ENDDATE)=0000)) OR (YEAR(STARTDATE)=%i AND WEEK(STARTDATE,1)<%i AND YEAR(ENDDATE)=%i AND WEEK(ENDDATE,1)>%i) OR (YEAR(STARTDATE)=%i and WEEK(STARTDATE,1)=%i) OR (YEAR(ENDDATE)=%i and WEEK(ENDDATE,1)=%i)' % (year,year,year,week,year,year,week,year,week,year,week,year,week)
  cursor.execute(command)
  recs=cursor.fetchall()
elif mode=='month':
  print "Loading home location for month %i of %i..." % (month,year)
  command='SELECT * FROM homeloc where (YEAR(STARTDATE) < %i AND (YEAR(ENDDATE) > %i OR YEAR(ENDDATE)=0000)) OR (YEAR(STARTDATE)=%i AND MONTH(STARTDATE)<%i AND (YEAR(ENDDATE)>%i or YEAR(ENDDATE)=0000)) OR (YEAR(STARTDATE)=%i AND MONTH(STARTDATE)<%i AND YEAR(ENDDATE)=%i AND MONTH(ENDDATE)>%i) OR (YEAR(ENDDATE)=%i and MONTH(ENDDATE)=%i) or (YEAR(STARTDATE)=%i AND MONTH(STARTDATE)=%i)' % (year,year,year,month,year,year,month,year,month,year,month,year,month)
  cursor.execute(command)
  recs=cursor.fetchall()

if len(recs) > 1:
  print "More than one home location for the specified time."
  print "This feature not yet implemented. Exiting. Sorry!"
  hlocs=recs
  sys.exit()
elif len(recs)==0:
  print "ERROR: no home location records found for the specified time. Assuming all records are 'away' or 'traveling'."
  hlat=-1
  hlong=-1
  hradius=-1
else:
  hlat=(recs[0])[2]
  hlong=(recs[0])[3]
  hradius=(recs[0])[4]

if mode=='week':
  command='SELECT * FROM locations WHERE WEEK(UTC,1)=%i AND YEAR(UTC)=%i ORDER by locations.UTC' % (week,year)
  cursor.execute(command)
  recs=cursor.fetchall()
elif mode=='month':
  command='SELECT * FROM locations WHERE MONTH(UTC)=%i AND YEAR(UTC)=%i ORDER by locations.UTC' % (month,year)
  cursor.execute(command)
  recs=cursor.fetchall()

if len(recs)<1:
  sys.stderr.write('ERROR: no records found for the requested time interval. Exiting.\n')
  sys.exit()

# go through the rows sequentially. First, check if the GPS location puts it
# within the "home" tolerance specified above. If it is, add that time to the 
# amount spent at "home".
rec0=recs[0]
nrecs=len(recs)
print "Processing GPS records.."
for rec1 in recs:
  if rec1==rec0:
    if hradius==-1:
      # it's all away
      atime+=dechrs*60.
      if mode=='week':
        command='INSERT into magellan.locations_spec (UTC,Type) values (\'%s\',\'away\')' % (rec1[0])
        cursor.execute(command)  
    else:
      # here, really need to get the time at the start of the week, then compute the time until the first record
      # first check if the rec is within the home distance
      if hlocs:
        # gotta get fancy, we have multiple home locations!
        # figure out when the current timestamp is, then make that the new hlat/hlong values
        # duplicate this below, too
      else: 
        dlat=rec0[1]-hlat
        dlong=rec0[2]-hlong
        rdlat=math.radians(dlat)
        rdlong=math.radians(dlong)
        # use the haversine formula to calculate the distance
        ha=math.sin(rdlat/2) * math.sin(rdlat/2) + math.cos(math.radians(rec0[1])) * math.cos(math.radians(rec1[1]))*math.sin(rdlong/2) * math.sin(rdlong/2);
        hc= 2 * math.atan2(math.sqrt(ha), math.sqrt(1-ha))
        dist=6378.1*hc
        if dist > hradius:
          # we're outside the home radius. chock this up as away
          #atime+=dechrs*60.
          if mode=='week':
            command='INSERT into magellan.locations_spec (UTC,Type) values (\'%s\',\'away\')' % (rec0[0])
            cursor.execute(command)
        else:
          # inside the home radius. we're in town
          #htime+=dechrs*60.
          if mode=='week':
            command='INSERT into magellan.locations_spec (UTC,Type) values (\'%s\',\'home\')' % (rec0[0])
            cursor.execute(command)
  else: 
    if hradius!=-1:
      # first check if the rec is within the home distance
      dlat=rec1[1]-hlat
      dlong=rec1[2]-hlong
      rdlat=math.radians(dlat)
      rdlong=math.radians(dlong)
      # use the haversine formula to calculate the distance
      ha=math.sin(rdlat/2) * math.sin(rdlat/2) + math.cos(math.radians(rec0[1])) * math.cos(math.radians(rec1[1]))*math.sin(rdlong/2) * math.sin(rdlong/2);
      hc= 2 * math.atan2(math.sqrt(ha), math.sqrt(1-ha))
      dist=6378.1*hc
      tdiff=rec1[0]-rec0[0]
      dechrs=tdiff.days*24+tdiff.seconds/3600.
      if dist > hradius:
        # we're outside the home radius. see if we're traveling or not
        dlat=rec0[1]-rec1[1]
        dlong=rec0[2]-rec1[2]
        rdlat=math.radians(dlat)
        rdlong=math.radians(dlong)
        # use the haversine formula to calculate the distance
        ha=math.sin(rdlat/2) * math.sin(rdlat/2) + math.cos(math.radians(rec0[1])) * math.cos(math.radians(rec1[1]))*math.sin(rdlong/2) * math.sin(rdlong/2);
        hc= 2 * math.atan2(math.sqrt(ha), math.sqrt(1-ha))
        travdist=6378.1*hc
        # now compute the average speed, see if we're traveling or not
        speed=travdist/dechrs	# this is in km/hr
        msspeed=speed/3.6
        if msspeed > TRAVELTHRESH:
          # we're traveling!
          ttime+=dechrs*60.
          if mode=='week':
            command='INSERT into magellan.locations_spec (UTC,Type) values (\'%s\',\'travel\')' % (rec1[0])
            cursor.execute(command)
        else:
          # we're away
          atime+=dechrs*60.
          if mode=='week':
            command='INSERT into magellan.locations_spec (UTC,Type) values (\'%s\',\'away\')' % (rec1[0])
            cursor.execute(command)
      else:
        tdiff=rec1[0]-rec0[0]
        dechrs=tdiff.days*24+tdiff.seconds/3600.
        # inside the home radius. we're in town
        htime+=dechrs*60.
        if mode=='week':
          command='INSERT into magellan.locations_spec (UTC,Type) values (\'%s\',\'home\')' % (rec1[0])
          cursor.execute(command)
    else:
      # no home radius. see if we're traveling or not
      dlat=rec0[1]-rec1[1]
      dlong=rec0[2]-rec1[2]
      rdlat=math.radians(dlat)
      rdlong=math.radians(dlong)
      # use the haversine formula to calculate the distance
      ha=math.sin(rdlat/2) * math.sin(rdlat/2) + math.cos(math.radians(rec0[1])) * math.cos(math.radians(rec1[1]))*math.sin(rdlong/2) * math.sin(rdlong/2);
      hc= 2 * math.atan2(math.sqrt(ha), math.sqrt(1-ha))
      travdist=6378.1*hc
      # now compute the average speed, see if we're traveling or not
      speed=travdist/dechrs   # this is in km/hr
      msspeed=speed/3.6
      if msspeed > TRAVELTHRESH:
        # we're traveling!
        ttime+=dechrs*60.
        if mode=='week':
          command='INSERT into magellan.locations_spec (UTC,Type) values (\'%s\',\'travel\')' % (rec1[0])
          cursor.execute(command)
      else:
        # we're away
        atime+=dechrs*60.
        if mode=='week':
          command='INSERT into magellan.locations_spec (UTC,Type) values (\'%s\',\'away\')' % (rec1[0])
          cursor.execute(command)
  # reset the 'new' rec to the old rec
  rec0=rec1
  # and loop to the next record

# after we've iterated over the week write the totals, percentages of the week
# back into the database for that week (check to see that there isn't already
# an entry, ask before overwriting)
totaltime=atime+htime+ttime

print "%s recorded a total time of approximately %f hours from %i records." % (mode,totaltime/60.,nrecs)
print "Submitting totals to SQL database.."

# submit to the database
if mode=='week':
  command='INSERT INTO magellan.analysis_weekly (year,week,home,homefrac,away,awayfrac,travel,travelfrac) values (%i,%i,%f,%f,%f,%f,%f,%f)' % (year,week,htime,htime/totaltime,atime,atime/totaltime,ttime,ttime/totaltime)
  cursor.execute(command)
elif mode=='month':
  command='INSERT INTO magellan.analysis_monthly (year,month,home,homefrac,away,awayfrac,travel,travelfrac) values (%i,%i,%f,%f,%f,%f,%f,%f)' % (year,month,htime,htime/totaltime,atime,atime/totaltime,ttime,ttime/totaltime)
  cursor.execute(command)

# close SQL
cursor.close()
scon.close()
