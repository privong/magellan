#!/usr/bin/env python2
#
# gmaps-weekly.py
#
# The information will be retreived from an SQL database

import MySQLdb
import sys
import time
import math
import pycurl
import numpy as np
import ConfigParser
import magellan
from datetime import date
import argparse


parser = argparse.ArgumentParser(description='Generate a map of unique away \
                                 locations.')
parser.add_argument('-w', '--week', type=int, default=False, action='store',
                    help='Week number to use. If left blank, most recent \
                         week will be used.')
parser.add_argument('-m', '--month', type=int, default=None, action='store',
                    help='Month number to use. If omitted, week default will \
                          be used. Note that the week switch will override \
                          this.')
parser.add_argument('-y', '--year', type=int, default=False, action='store',
                    help='Year to use. If left blank, the current year will \
                         be used.')
parser.add_argument('-u', '--uniquedist', default=60, action='store',
                    help='Approximate distance (in km) points must be to be \
                         considered "unique".')
parser.add_argument('-p', '--plotfile', default=None, action='store',
                    help='Name of file to save map.')
args = parser.parse_args()

trinidad = magellan.magellan()
cursor = trinidad.initdb()

# set up base URL from Google Static Maps API
# https://code.google.com/apis/maps/documentation/staticmaps/
mapurl = "http://maps.google.com/maps/api/staticmap?size=800x800&maptype=roadmap"

# process arguments, decide which week and year we are using.
# how many arguments do we have?
today = date.today()
mode = 'week'
if args.month is not None:
    month = args.month
    mode = 'month'
if not(args.week):
    week = (today.isocalendar())[1]-1
else:
    week = args.week
    mode = 'week'
if not(args.year):
    year = (today.isocalendar())[0]
else:
    year = args.year

if week < 1:    # make sure we don't default to nonsense
    year = year-1
    week = (date(year, 12, 31).isocalendar())[0]

if mode == 'week':
    print "Loading home location for week %i of %i..." % (week, year)
    command = 'SELECT * FROM locations_spec WHERE WEEK(UTC,1)=%i AND \
               YEAR(UTC)=%i AND TYPE=\'away\' ORDER by locations_spec.UTC' % \
              (week, year)
    cursor.execute(command)
elif mode == 'month':
    print "Loading home location for month %i of %i..." % (month, year)
    command = 'SELECT * FROM locations_spec WHERE MONTH(UTC)=%i AND \
               YEAR(UTC)=%i AND TYPE=\'away\' ORDER by locations_spec.UTC' % \
              (month, year)
    cursor.execute(command)

# retrieve rows from the database within that timerange.
recs = cursor.fetchall()

# arrange away locations by geographic proximity
print "Convering %i records into a list of unique locations..." % (len(recs))
command = 'SELECT lat,lon FROM locations WHERE UTC=\'%s\'' % (recs[0][0])
cursor.execute(command)
thisloc = cursor.fetchall()
awaylocs = [[[thisloc[0][0], thisloc[0][1]]]]
for rec1 in recs[1:]:
    umatch = False
    for i in range(0, np.array(awaylocs).shape[0]):
        command = 'SELECT lat,lon FROM locations WHERE UTC=\'%s\'' % \
                  (rec1[0])
        cursor.execute(command)
        thisloc = cursor.fetchall()
        # compute distance of current location from avg matched locations
        tlat = np.mean([awaylocs[i][j][0] for j in range(len(awaylocs[i]))])
        tlong = np.mean([awaylocs[i][j][1] for j in range(len(awaylocs[i]))])
        tdist = magellan.GreatCircDist([tlat, tlong], thisloc[0])
        # check for distance
        if tdist < args.uniquedist:
            # within an existing unique location
            umatch = True
            awaylocs[i].append([thisloc[0][0], thisloc[0][1]])
    if not(umatch):
        # no match, add this location to the unique locations list
        awaylocs.append([[thisloc[0][0], thisloc[0][1]]])

uniqueaway = [[np.mean([awaylocs[0][0][0] for i in range(len(awaylocs[0]))]),
              np.mean([awaylocs[0][0][1] for i in range(len(awaylocs[0]))])]]
mapurl = mapurl + "&markers=color:red|label:A|%f,%f" % \
         (uniqueaway[0][0], uniqueaway[0][1])
for place in awaylocs[1:]:
    tempaway = [np.mean([place[i][0] for i in range(len(place))]),
                  np.mean([place[i][1] for i in range(len(place))])]
    mapurl = mapurl + "&markers=color:red|label:A|%f,%f" % \
            (tempaway[0], tempaway[1])
    uniqueaway.append(tempaway)

mapurl = mapurl + "&sensor=false"

if len(uniqueaway) != 0:
    print "Requesting google maps file of %i unique locations..." % \
          (len(uniqueaway))
    if len(uniqueaway) == 2:
        mapurl = mapurl+'&zoom=10'

    if len(mapurl) < 2000:
        if args.plotfile is None:
            fname = '/srv/http/local/location/%i-%i.png' % (year, week)
        else:
            fname = args.plotfile
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
