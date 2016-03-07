#!/usr/bin/env python2
#
# map_locations.py
#
# Generate and save a map of locations visited, based on GPS logs.
#
# Copyright (C) 2014-2015 George C. Privon
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
parser.add_argument('-w', '--week', type=int, default=None, action='store',
                    help='Week number to use. If left blank, most recent \
                         week will be used.')
parser.add_argument('-m', '--month', type=int, default=None, action='store',
                    help='Month number to use. If omitted, week default will \
                          be used. Note that the week switch will override \
                          this.')
parser.add_argument('-y', '--year', type=int, default=None, action='store',
                    help='Year to use. If left blank, the current year will \
                         be used. If this is the only item specified, a map \
                         will be made of all away points during that year.')
parser.add_argument('-u', '--uniquedist', default=60, action='store',
                    help='Approximate distance (in km) points must be to be \
                         considered "unique".')
parser.add_argument('-s', '--service', default='osm', action='store',
                    choices=['google', 'osm'],
                    help='Mapping service to use for generating static maps. \
                          Defaults to \'osm\'. Other option: \'google\' for \
                          Google Maps.')
parser.add_argument('-i', '--imgsize', default=800, action='store', type=int,
                    help='Number of pixels on a side for the maps image.')
parser.add_argument('-p', '--plotfile', default=None, action='store',
                    help='Name of file to save map.')
args = parser.parse_args()

trinidad = magellan.magellan()
cursor = trinidad.initdb()

# process arguments, decide which week and year we are using.
# how many arguments do we have?
today = date.today()
mode = 'week'
if args.month is not None:
    month = args.month
    mode = 'month'
if args.week is None:
    week = (today.isocalendar())[1]-1
else:
    week = args.week
    mode = 'week'
if args.year is None:
    year = (today.isocalendar())[0]
else:
    year = args.year
    if args.month is None and args.week is None:
        mode = 'year'

if week < 1 and mode == 'week':
    year = year-1
    week = (date(year, 12, 31).isocalendar())[0]

if mode == 'week':
    sys.stdout.write("Loading home location for week %i of %i..." % (week, year))
    command = 'SELECT * FROM locations_spec WHERE WEEK(UTC,1)=%i AND \
               YEAR(UTC)=%i AND TYPE=\'away\' ORDER by locations_spec.UTC' % \
              (week, year)
elif mode == 'month':
    sys.stdout.write("Loading home location for month %i of %i..." % (month, year))
    command = 'SELECT * FROM locations_spec WHERE MONTH(UTC)=%i AND \
               YEAR(UTC)=%i AND TYPE=\'away\' ORDER by locations_spec.UTC' % \
              (month, year)
elif mode == 'year':
    sys.stdout.write("Loading home location for %i..." % (year))
    command = 'SELECT * FROM locations_spec WHERE YEAR(UTC)=%i \
               AND TYPE=\'away\' ORDER by locations_spec.UTC' % \
              (year)
cursor.execute(command)

# retrieve rows from the database within that timerange.
recs = cursor.fetchall()

# arrange away locations by geographic proximity
if len(recs) == 0:
    sys.stderr.write("No away records found for the specified time.\n")
    sys.exit(1)
sys.stdout.write("Converting %i records into a list of unique locations..." % (len(recs)))
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
#mapurl = mapurl + "&markers=color:red|label:A|%f,%f" % \
#         (uniqueaway[0][0], uniqueaway[0][1])
for place in awaylocs[1:]:
    tempaway = [np.mean([place[i][0] for i in range(len(place))]),
                  np.mean([place[i][1] for i in range(len(place))])]
    #mapurl = mapurl + "&markers=color:red|label:A|%f,%f" % \
    #        (tempaway[0], tempaway[1])
    uniqueaway.append(tempaway)

naway = 1
if args.service == 'google':
    # https://code.google.com/apis/maps/documentation/staticmaps/
    mapurl = "http://maps.google.com/maps/api/staticmap?size=%ix%i&maptype=roadmap" % \
             (args.imgsize, args.imgsize)
    for loc in uniqueaway:
        mapurl = mapurl + "&markers=color:red|label:%i|%f,%f" % \
                          (naway, loc[0], loc[1])
        naway += 1
    if len(uniqueaway) == 2:
        mapurl = mapurl+'&zoom=10'
    mapurl = mapurl + "&sensor=false"
elif args.service == 'osm':
    # see http://staticmap.openstreetmap.de/
    mapurl = "http://staticmap.openstreetmap.de/staticmap.php?maptype=osmarenderer&size=%ix%i&markers=" % \
             (args.imgsize, args.imgsize)
    for loc in uniqueaway:
        mapurl = mapurl + "%f,%f,lightblue%i|" % (loc[0], loc[1], naway)
        naway += 1
    mapurl = mapurl[:-1]    # remove trailing '|' to avoid an extra marker
    maxdist = [0]
    for loc in uniqueaway:  # compute the distance between pairs of away pts
        for loc2 in uniqueaway:
            newdist = (np.sqrt((loc[0] - loc2[0])**2 +
                       (loc[1] - loc2[1])**2))
            if newdist > maxdist[0]:
                maxdist = [newdist, [(loc[0] + loc2[0]) / 2., 
                                     (loc[1] + loc2[1]) / 2.]]
    if maxdist == [0]:
        # likely happens because there was only 1 uniqueaway
        maxdist = [1, uniqueaway[0]]
    mapurl = mapurl + "&center=%f,%f" % (maxdist[1][0], maxdist[1][1])
    mapurl = mapurl + "&zoom=%i" % \
             (np.floor(np.log((args.imgsize / 256.) * 
                              360. / maxdist[0]) / np.log(2)))

if len(uniqueaway) != 0:
    sys.stdout.write("Requesting map of %i unique locations..." % (len(uniqueaway)))
    if (args.service == 'google' and len(mapurl) < 2000) or \
       args.service == 'osm':
        if args.plotfile is None:
            fname = '/srv/http/local/location/{0:04d}-{1:02d}.png'.format(year, week)
        else:
            fname = args.plotfile
        fp = open(fname, "wb")

        curl = pycurl.Curl()
        curl.setopt(pycurl.URL, mapurl)
        curl.setopt(pycurl.WRITEDATA, fp)
        curl.perform()
        curl.close()
        fp.close()
        sys.stdout.write("Map saved to " + fname + "\n")
    else:
        sys.stderr.write("ERROR: request url exceeds google static maps API limit Exiting.")
else:
    sys.stdout.write("No away locations found. Exiting.")

# close SQL
cursor.close()
trinidad.closedb()
