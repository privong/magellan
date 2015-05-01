#!/usr/bin/env python2
#
# plot_histogram.py
#
# Plot already computed weekly analysis.
#
# Copyright (C) 2014 George C. Privon
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


import sys
import time
import math
import numpy
import MySQLdb
import argparse
import ConfigParser
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
from datetime import date
import magellan


parser = argparse.ArgumentParser(description='Plot information on \
            home/away/travel based on different time intervals.')
parser.add_argument('-w', '--week', action='store_true', default=False,
                    help='Plot analyitics for the past 10 weeks.')
parser.add_argument('-y', '--year', action='store_true', default=False,
                    help='Plot analyitics for the current year.')
parser.add_argument('-p', '--plotfile', default=None,
                    help='Location to save figure.')
parser.add_argument('-t', '--type', default='bar',
                    choices=['points', 'bar'],
                    help='Plot type. points: points showing the fraction of \
                          time spent in each setting. bar: stacked bar chart.')
parser.add_argument('--scaling', default='days',
                    choices=['week', 'days', 'hours'],
                    help='Show the y-axis scale as days in the week or as a \
                          fraction of the total week?')
args = parser.parse_args()

TABLENAME = "analyze_weekly"

trinidad = magellan.magellan()
cursor = trinidad.initdb()

if args.week:
    print "Retreiving analyzed weekly data for the past 10 weeks...\n"

    # get the previous iso week (to use as the end of the plot)
    today = date.today()
    week = (today.isocalendar())[1]-1
    year = (today.isocalendar())[0]

    # here, retreive all the data from the past 10 weeks
    if week <= 10:
        # get the number of weeks last year
        lyweeks = date.isocalendar(date(year-1, 12, 31))[1]
        command = 'SELECT year,week,homefrac,awayfrac,travelfrac from \
                  analysis_weekly where (YEAR=%i) OR (YEAR=%i AND WEEK > %i) \
                  ORDER BY year,week' % (year, year-1, lyweeks-10+week)
    else:
        # it's far enough into the year we can just grab the last 10
        command = 'SELECT year,week,homefrac,awayfrac,travelfrac from \
                  analysis_weekly where WEEK > %i AND YEAR=%i ORDER BY week' \
                  % (week-10, year)
    filen = 'latest.png'
elif args.year:
    print "Retreiving analyzed weekly data for the current year...\n"
    today = date.today()
    year = (today.isocalendar())[0]
    command = 'SELECT year,week,homefrac,awayfrac,travelfrac from \
              analysis_weekly where YEAR=%i ORDER BY week' % (year)
    filen = 'year.png'

# run the command
cursor.execute(command)
recs = cursor.fetchall()

if len(recs) == 0:
    print "ERROR: no analysis data found."
    sys.exit

print "Retreived %i results" % (len(recs))

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

plt.ioff()
plotsym = ['bo', 'go', 'ro']
plotlabel = ['Home', 'Away', 'Travel']
if args.type == 'points':
    for i in range(2, 5):
        plt.plot(results[:, 1],
                 results[:, i],
                 plotsym[i-2],
                 label=plotlabel[i-2])
    plt.ylim([-0.01, 1.1*ylimscale])
elif args.type == 'bar':
    plt.bar(results[:, 1] - 0.5,
            results[:, 2],
            width=1,
            color=plotsym[0][0],
            label=plotlabel[0])
    plt.bar(results[:, 1] - 0.5,
            results[:, 3],
            width=1,
            bottom=results[:, 2],
            color=plotsym[1][0],
            label=plotlabel[1])
    plt.bar(results[:, 1] - 0.5,
            results[:, 4],
            width=1,
            bottom=results[:, 2] + results[:, 3],
            color=plotsym[2][0],
            label=plotlabel[2])
    plt.ylim([0, 1 * ylimscale])
    plt.tick_params(direction='inout')
plt.legend(fontsize='x-small', numpoints=1, frameon=True)
(x1, x2) = plt.xlim()
plt.xlim(x1-1, x2+3)
plt.ylabel(ylabel)
plt.xlabel('Week Number')
plt.minorticks_on()

if args.plotfile is None:
    plt.savefig('/srv/http/local/location/'+filen, transparent=True)
else:
    plt.savefig(args.plotfile, transparent=True)

# close SQL
cursor.close()
trinidad.closedb()
