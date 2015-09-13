#!/usr/bin/env python2

import MySQLdb
import ConfigParser
from datetime import date
import sys
import requests
import numpy
import magellan
import argparse

parser = argparse.ArgumentParser(description='Push away stats to tipboard.')
parser.add_argument('--scaling', default='days',
                    choices=['week', 'days', 'hours'],
                    help='Show the y-axis scale as days in the week or as a \
                          fraction of the total week?')
args = parser.parse_args()

# dashboard information
config = ConfigParser.RawConfigParser()
if os.path.isfile('magellan.cfg'):
    config.read('magellan.cfg')
APIkey = config.get('Tipboard', 'key')
BASEURL = config.get('Tipboard', 'baseurl')
tileid = 'magellan'
tiletype = 'cumulative_flow'

# magellan setup
TABLENAME = "analyze_weekly"
trinidad = magellan.magellan()
cursor = trinidad.initdb()
plotlabel = ['Home', 'Away', 'Travel']

today = date.today()
year = (today.isocalendar())[0]
command = 'SELECT year,week,homefrac,awayfrac,travelfrac from \
          analysis_weekly where YEAR=%i ORDER BY week' % (year)

# run the command
cursor.execute(command)
recs = cursor.fetchall()

# close SQL
cursor.close()
trinidad.closedb()

if len(recs) == 0:
    print "ERROR: no analysis data found."
    sys.exit

results = numpy.array(recs)
if args.scaling == 'days':
    for i in range(2, 5):
        results[:, i] *= 7
    ylabel = 'Days'
    ylimscale = 7
elif args.scaling == 'hours':
    for i in range(2, 5):
        results[:, i] *= 7 * 24
    ylabel = 'Hours'
    ylimscale = 7 * 24
else:
    ylabel = 'Fraction'
    ylimscale = 1

payload = {'tile':tiletype,
           'key':tileid}

datastr = '{"title":"'+str(year)+'", '
datastr += '"series_list": ['
for i in range(2, 5):
    datastr += '{"label": "'+plotlabel[i-2]+'", "series": ['
    for entry in results[:, i]:
        datastr += ' {0:1.4f},'.format(entry)
    datastr = datastr[:-1]
    datastr += ']},'
payload['data'] = datastr[:-1] + ']}'

r = requests.post(BASEURL+APIkey+'/push', data=payload)

valuestr = '{"ticks": ['
for entry in results[:, 1]:
    valuestr += '[{0:1.0f}, "{0:1.0f}"], '.format(entry, entry)
valuestr = valuestr[:-2]
valuestr += ']}'
payload = {'value':valuestr}

r = requests.post(BASEURL+APIkey+'/tileconfig/'+tileid, data=payload)
