#!/usr/bin/python2
#
# plot_histogram.py
#
# Plot already computed weekly analysis.

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


cursor = magellan.initdb()

parser = argparse.ArgumentParser(description='Plot information on \
            home/away/travel based on different time intervals.')
parser.add_argument('-w', '--week', action='store_true', default=False,
                    help='Plot analyitics for the past 10 weeks.')
parser.add_argument('-y', '--year', action='store_true', default=False,
                    help='Plot analyitics for the current year.')
parser.add_argument('--plotfile', default=None,
                    help='Location to save figure.')
args = parser.parse_args()

TABLENAME = "analyze_weekly"

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

plt.ioff()
# plot home, away, travel
plotsym = ['bo', 'go', 'ro']
plotlabel = ['Home', 'Away', 'Travel']
for i in range(2, 5):
    plt.plot(results[:, 1], results[:, i], plotsym[i-2], label=plotlabel[i-2])
plt.legend(fontsize='x-small', numpoints=1, frameon=True)
plt.ylim([-0.01, 1.1])
(x1, x2) = plt.xlim()
plt.xlim(x1-1, x2+1)
plt.ylabel('Fraction')
plt.xlabel('Week Number')
plt.minorticks_on()

if args.plotfile is None:
    plt.savefig('/srv/http/local/location/'+filen, transparent=True)
else:
    plt.savefig(args.plotfile, transparent=True)

# close SQL
cursor.close()
magellan.closedb()
