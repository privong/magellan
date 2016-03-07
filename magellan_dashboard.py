#!/usr/bin/env python2
#
# magellan_dashboard.py
#
# Copyright (C) 2015-2016 George C. Privon
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
import ConfigParser
from datetime import date
import sys
import os
import requests
import numpy
import magellan
import argparse


parser = argparse.ArgumentParser(description='Push away stats to tipboard.')
parser.add_argument('--scaling', default='days',
                    choices=['week', 'days', 'hours'],
                    help='Show the y-axis scale as days in the week, as a \
                          fraction of the total week, or number of hours? \
                          Default is days in the week.')
args = parser.parse_args()

# dashboard information
config = ConfigParser.RawConfigParser()
if os.path.isfile('magellan.cfg'):
    config.read('magellan.cfg')
APIkey = config.get('Tipboard', 'apikey')
BASEURL = config.get('Tipboard', 'baseurl')
if not(APIkey) or not(BASEURL):
    sys.stderr.write('Cannot load tipboard info from configuration. Exiting.\n')
    sys.exit(-1)
tileid = 'magellan'
tiletype = 'cumulative_flow'

# magellan setup
TABLENAME = "analyze_weekly"
trinidad = magellan.magellan()
cursor = trinidad.initdb()
plotlabel = ['Home', 'Away', 'Travel']

today = date.today()
year, week, day = today.isocalendar()
command = 'SELECT timeID,year,week,homefrac,awayfrac,travelfrac from \
          analysis_weekly where (YEAR=%i) or \
          (YEAR=%i and WEEK>%i) ORDER BY timeID' \
          % (year, year-1, week)

# run the command
cursor.execute(command)
recs = cursor.fetchall()

# close SQL
cursor.close()
trinidad.closedb()

if len(recs) == 0:
    sys.stderr.write("ERROR: no analysis data found.")
    sys.exit

results = numpy.array(recs)
if args.scaling == 'days':
    for i in range(3, 6):
        results[:, i] *= 7
    ylabel = 'Days'
    ylimscale = 7
elif args.scaling == 'hours':
    for i in range(3, 6):
        results[:, i] *= 7 * 24
    ylabel = 'Hours'
    ylimscale = 7 * 24
else:
    ylabel = 'Fraction'
    ylimscale = 1

payload = {'tile':tiletype,
           'key':tileid}

# set up and send the plot data
datastr = '{"title":"Currently week '+str(week)+'.<br>Week ' + str(week-1) + \
' stats:", '
datastr += '"series_list": ['
for i in range(3, 6):
    datastr += '{"label": "'+plotlabel[i-3]+'", "series": ['
    for entry in results[:, i]:
        datastr += ' {0:1.4f},'.format(entry)
    datastr = datastr + ' ' + datastr.rsplit(' ',1)[-1]
    datastr = datastr[:-1]
    datastr += ']},'
payload['data'] = datastr[:-1] + ']}'

r = requests.post(BASEURL+APIkey+'/push', data=payload)

# set up and send the locations of tick marks on the plot
# if more than 16 weeks don't show all the ticks, because that would be too
# crowded
valuestr = '{"ticks": ['
if len(results[:,1]) > 16:
    step = 2
    start = 1
    valuestr += '["1", " "],'
else:
    step = 1
    start = 0
i = 1
for entry in results[start::step, 0]:
    valuestr += '[{0:d}, "{1:1.0f}"], '.format(i, entry)
    i += 2
valuestr = valuestr + '[{0:d}, "{1:1.0f}"], '.format(i, entry)
valuestr = valuestr[:-2]
valuestr += ']}'
payload = {'value':valuestr}

r = requests.post(BASEURL+APIkey+'/tileconfig/'+tileid, data=payload)
