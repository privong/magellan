#!/usr/bin/env python
"""
map_locations.py

Generate and save a map of locations visited, based on GPS logs.

Copyright (C) 2014-2018 George C. Privon

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""


import MySQLdb
import sys
import time
import math
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import magellan
from datetime import date
import argparse
import matplotlib.pyplot as plt


def plot_map(positions, plotfile):
    """
    Map the locations of recorded GPS positions.
    """

    fig = plt.figure(figsize=(16, 12))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.coastlines()
    ax.set_global()

    countries = cfeature.NaturalEarthFeature(category='cultural',
                                             name='admin_0_countries',
                                             scale='50m',
                                             facecolor='none')

    states_provinces = cfeature.NaturalEarthFeature(category='cultural',
                                                    name='admin_1_states_provinces_lines',
                                                    scale='50m',
                                                    facecolor='none')

    MAP_SOURCE = 'Natural Earth'
    MAP_LICENSE = 'public domain'

    ax.add_feature(cfeature.LAND)
    ax.add_feature(cfeature.OCEAN)
    ax.add_feature(cfeature.LAKES)
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(countries, edgecolor='gray')
    ax.add_feature(states_provinces, edgecolor='gray')

    ax.gridlines(draw_labels=True)

    if positions.shape:
        ax.scatter(positions['lon'],
                   positions['lat'],
                   marker='o',
                   color='green',
                   transform=ccrs.PlateCarree(),
                   zorder=20)

    fig.savefig(plotfile,
                bbox_inches='tight')



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
parser.add_argument('-u', '--uniquedist', default=None, action='store',
                    help='Approximate distance (in km) points must be to be \
                         considered "unique". If provided, will override \
                         value in magellan.cfg.')
parser.add_argument('-i', '--imgsize', default=800, action='store', type=int,
                    help='Number of pixels on a side for the maps image.')
parser.add_argument('-p', '--plotfile', default=None, action='store',
                    help='Name of file to save map.')
args = parser.parse_args()

trinidad = magellan.magellan()
trinidad.loadanalysis()
cursor = trinidad.initdb()

if args.uniquedist is not None:
    trinidad.uniquedist = args.uniquedist

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
    if args.plotfile is None:
        args.plotfile = "{0:1.0f}-{1:02.0f}.png".format(year, week)
    sys.stdout.write("Loading away locations for week %i of %i...\n" % (week, year))
    command = 'SELECT * FROM locations_spec WHERE WEEK(UTC,3)=%i AND \
               YEAR(UTC)=%i AND TYPE=\'away\' ORDER by locations_spec.UTC' % \
              (week, year)
elif mode == 'month':
    if args.plotfile is None:
        args.plotfile = "{0:1.0f}-M_{1:02.0f}.png".format(year, month)
    sys.stdout.write("Loading away locations for month %i of %i...\n" % (month, year))
    command = 'SELECT * FROM locations_spec WHERE MONTH(UTC)=%i AND \
               YEAR(UTC)=%i AND TYPE=\'away\' ORDER by locations_spec.UTC' % \
              (month, year)
elif mode == 'year':
    if args.plotfile is None:
        args.plotfile = "{0:1.0f}.png".format(year)
    sys.stdout.write("Loading away locations for %i...\n" % (year))
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
sys.stdout.write("Converting %i records into a list of unique locations...\n" % (len(recs)))
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
        if tdist < trinidad.uniquedist:
            # within an existing unique location
            umatch = True
            awaylocs[i].append([thisloc[0][0], thisloc[0][1]])
    if not(umatch):
        # no match, add this location to the unique locations list
        awaylocs.append([[thisloc[0][0], thisloc[0][1]]])

uniqueaway = []
for place in awaylocs:
    meanlat = np.mean([place[i][0] for i in range(len(place))])
    meanlon = np.mean([place[i][1] for i in range(len(place))])
    uniqueaway.append((meanlat, meanlon))

uniqueaway = np.array(uniqueaway,
                      dtype=[('lat', float),
                             ('lon', float)])

latrange = (np.min(uniqueaway['lat']), np.max(uniqueaway['lat']))
lonrange = (np.min(uniqueaway['lon']), np.max(uniqueaway['lon']))
"""
2. Do a gaussian smoothing of all the positions.
    - use the positional accuracy as the sigma for the gaussian ofg
      each point.
    - be sure to appropriately translate the distance uncertainty with the
      corresponding longitude uncertainty (i.e., the gaussian should be
      elliptical).
3. Plot gaussian field below the border lines but above any other coloring

Eventually enable some fine-grained control by the user of what should be
shown on the maps.
"""

if len(uniqueaway) != 0:
    sys.stdout.write("Generating map of %i unique locations...\n" % (len(uniqueaway)))
    plot_map(uniqueaway, args.plotfile)
    sys.stdout.write("Map saved to " + args.plotfile + "\n")
else:
    sys.stdout.write("No away locations found. Exiting.\n")

# close SQL
cursor.close()
trinidad.closedb()
