#!/usr/bin/python2
#
# gmaps-weekly.py
#
# The information will be retreived from an SQL database
#
# USAGE: gmaps-weekly.py [week#] [year]
# If neither is specified, the most recent full week will be used.
# If only week is specified, the current year is assumed.

import MySQLdb
import sys
import time
import math
import pycurl
import numpy
import ConfigParser
import magellan

from datetime import date

cursor=magellan.initdb()

UAWAY=60.	# 'unique' locations are 30 km apart

# set up base URL from Google Static Maps API
# https://code.google.com/apis/maps/documentation/staticmaps/
mapurl="http://maps.google.com/maps/api/staticmap?size=800x800&maptype=roadmap"

# process arguments, decide which week and year we are using.
# how many arguments do we have?
today=date.today()
nargs=len(sys.argv)
if nargs==1:
    # use the previous week
    week=(today.isocalendar())[1]-1
    year=(today.isocalendar())[0]
elif nargs==2:
    # use the specified week of the current year
    week=int(sys.argv[1])
    year=(today.isocalendar())[0]
elif nargs>2:
    # use the specified week of the specified year. ignore everything else
    week=int(sys.argv[1])
    year=int(sys.argv[2])

print "Loading home location for week %i of %i..." % (week,year)

command='SELECT * FROM locations_spec WHERE WEEK(UTC,1)=%i AND YEAR(UTC)=%i AND TYPE=\'away\' ORDER by locations_spec.UTC' % (week,year)
cursor.execute(command)

# retrieve rows from the database within that timerange.
recs=cursor.fetchall()

uniqueaway=[]

# go through the rows sequentially. First, check if the GPS location puts it
# within the "home" tolerance specified above. If it is, add that time to the 
# amount spent at "home".
print "Convering %i records in to unique locations..." % (len(recs))
for rec1 in recs:
    # we're away. see if it's unique
    umatch=0
    if len(uniqueaway)==0:
        # we have no unique away locations
        command='SELECT lat,lon FROM locations WHERE UTC=\'%s\'' % (rec1[0])
        cursor.execute(command)
        thisloc=cursor.fetchall()
        uniqueaway=[thisloc[0][0],thisloc[0][1]]
        mapurl=mapurl + "&markers=color:red|label:A|%f,%f" % (thisloc[0][0],thisloc[0][1])
    else:
        # have unique away locations defined, see if they match
        for i in range(0,int(len(uniqueaway)/2)):
            command='SELECT lat,lon FROM locations WHERE UTC=\'%s\'' % (rec1[0])
            cursor.execute(command)
            thisloc=cursor.fetchall()
            # compute distances from that array location
            tlat=uniqueaway[i]
            tlong=uniqueaway[i+1]
            tdist=magellan.GreatCircDist([tlat,tlong],thisloc[0])
            # check for distance
            if tdist < UAWAY:
                # within an existing unique location, set a flag that it matches
                umatch=1
        if not(umatch):
            # no match, add this location to the unique locations list
            uniqueaway=numpy.concatenate((uniqueaway,[thisloc[0][0],thisloc[0][1]]),axis=0)
            mapurl=mapurl + "&markers=color:red|label:A|%f,%f" % (thisloc[0][0],thisloc[0][1])

mapurl=mapurl + "&sensor=false"	

if len(uniqueaway)!=0:
    print "Requesting google maps file of %i unique locations..." % (len(uniqueaway)/2)
    if len(uniqueaway)==2:
        mapurl=mapurl+'&zoom=10'

    if len(mapurl) < 2000:
        fname='/srv/http/local/location/%i-%i.png' % (year,week)
        fp=open(fname,"wb")

        curl=pycurl.Curl()
        curl.setopt(pycurl.URL,mapurl)
        curl.setopt(pycurl.WRITEDATA,fp)
        curl.perform()
        curl.close()
        fp.close()
    else:
        print "ERROR: request url exceeds google static maps API limit. Exiting."
else:
    print "ERROR: no away locations found. Exiting."

# close SQL
cursor.close()
#scon.close()
