#!/usr/bin/python2
#
# gmaps-weekly.py
#
# The information will be retreived from an SQL database

import MySQLdb
import sys
import time
import math
import pycurl
import numpy
import ConfigParser
import magellan
from datetime import date
import argparser


parser = argparse.ArgumentParser(description='Generate a map of unique away \
                                 locations.')
parser.add_argument('week', type=int, default=False, action='store',
                    help='Week number to use. If left blank, most recent \
                         week will be used.')
parser.add_argument('year', type=int, default=False, action='store',
                    help='Year to use. If left blank, the current year will \
                         be used.')
parser.add_argument('-u', '--uniquedist', default=60, action='store',
                    help='Approximate distance (in km) points must be to be \
                         considered "unique".')
args = parse.parse_args()

trinidad = magellan.magellan()
cursor = trinidad.initdb()

# set up base URL from Google Static Maps API
# https://code.google.com/apis/maps/documentation/staticmaps/
mapurl = "http://maps.google.com/maps/api/staticmap?size=800x800&maptype=roadmap"

# process arguments, decide which week and year we are using.
# how many arguments do we have?
today = date.today()
if not(args.week):
    week = (today.isocalendar())[1]-1
if not(args.year):
    year = (today.isocalendar())[0]

if week < 1:    # make sure we don't default to nonsense
    year = year-1
    week = (date(year, 12, 31).isocalendar())[0]

print "Loading home location for week %i of %i..." % (week, year)

command = 'SELECT * FROM locations_spec WHERE WEEK(UTC,1)=%i AND \
          YEAR(UTC)=%i AND TYPE=\'away\' ORDER by locations_spec.UTC' % \
          (week, year)
cursor.execute(command)

# retrieve rows from the database within that timerange.
recs = cursor.fetchall()

awaylocs = []

# arrange away locations by geographic proximity
print "Convering %i records into a list of unique locations..." % (len(recs))
for rec1 in recs:
    umatch = False
    if len(awaylocs) == 0:
        command = 'SELECT lat,lon FROM locations WHERE UTC=\'%s\'' % (rec1[0])
        cursor.execute(command)
        thisloc = cursor.fetchall()
        awaylocs = [[[thisloc[0][0], thisloc[0][1]]]]
    else:
        for i in range(0, len(awaylocs)):
            command = 'SELECT lat,lon FROM locations WHERE UTC=\'%s\'' % \
                      (rec1[0])
            cursor.execute(command)
            thisloc = cursor.fetchall()
            # compute distance of current location from avg matched locations
            tlat = np.mean([awaylocs[i][j][0] for j in range(2)])
            tlong = np.mean([awaylocs[i][j][1] for j in range(2)])
            tdist = trinidad.GreatCircDist([tlat, tlong], thisloc[0])
            # check for distance
            if tdist < args.u:
                # within an existing unique location
                umatch = True
                awaylocs[i].append(thisloc[0])
        if not(umatch):
            # no match, add this location to the unique locations list
            awaylocs.append([[thisloc[0][0], thisloc[0][1]]])

for place in awaylocs:
    uniqueaway = [np.mean([place[i][0] for i in range(len(place))]),
                  np.mean([place[i][1] for i in range(len(place))])]
    mapurl = mapurl + "&markers=color:red|label:A|%f,%f" % \
            (uniqueaway[0], uniqueaway[1])

mapurl = mapurl + "&sensor=false"

if len(uniqueaway) != 0:
    print "Requesting google maps file of %i unique locations..." % \
          (len(uniqueaway)/2)
    if len(uniqueaway) == 2:
        mapurl = mapurl+'&zoom=10'

    if len(mapurl) < 2000:
        fname = '/srv/http/local/location/%i-%i.png' % (year, week)
        fp = open(fname, "wb")

        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, mapurl)
        curl.setopt(pycurl.WRITEDATA, fp)
        curl.perform()
        curl.close()
        fp.close()
    else:
        print "ERROR: request url exceeds google static maps API limit. \
              Exiting."
else:
    print "ERROR: no away locations found. Exiting."

# close SQL
cursor.close()
trinidad.closedb()
