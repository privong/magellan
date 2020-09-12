#!/usr/bin/env python
"""
loc_analyze.py

Provide a (weekly/monthly) analysis of GPS log information.
The information will be retreived from an SQL database

Copyright (C) 2014-2018, 2020 George C. Privon

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

import sys
from datetime import datetime
import math
import magellan
from datetime import date
import argparse


parser = argparse.ArgumentParser(description='Analyze stored location \
                                 information.')
parser.add_argument('-p', '--period', action='store', type=str, default='week',
                    choices=['week', 'month', 'year', 'all'],
                    help='Desired analysis period.')
parser.add_argument('-w', '--week', action='store', type=int,
                    default=None, help='Week to analyze (default, uses most \
recent week)')
parser.add_argument('-m', '--month', action='store', type=int,
                    default=None, help='Month to analyze')
parser.add_argument('-y', '--year', action='store', type=int,
                    default=None, help='Year. If not given, the current year \
is used.')
parser.add_argument('--maxtime', action='store', type=float, default=840.,
                    help="Maximum time separation (in hours) between adjacent \
location points. Points separated by a larger value \
will not be considered as connected (for the \
purpose of determining if a point counts as travel).")
args = parser.parse_args()

trinidad = magellan.magellan()
cursor = trinidad.initdb()

trinidad.loadanalysis()

TABLENAME = "locations_spec"

htime = 0		# home time in minutes
atime = 0		# away time in minutes
ttime = 0		# travel time in minutes

today = date.today()
if args.period == 'week':
    if args.week is None:
        week = (today.isocalendar())[1]-1
    else:
        week = args.week
elif args.period == 'month':
    if args.month is None:
        month = today.month-1
    else:
        month = args.month
    if month == 0:
        month = 12
if args.year is None:
    year = (today.isocalendar())[0]
else:
    year = args.year

if args.period == 'month' and month == 0:
    year -= 1
    month += 1

if args.period == 'week' and week < 0:
    year = year-1
    week = (date(year, 12, 31).isocalendar())[0]

# get home location from the 'homeloc' database
# there should be a better way to select this...
if args.period == 'week':
    sys.stdout.write("Loading home location for week %i of %i...\n" %
                     (week, year))
    command = 'SELECT startdate,enddate,lat,lon,homeradius, \
(strftime("%j", date(startdate, "-3 days", "weekday 4")) - 1) / 7 as isoweek_s, \
(strftime("%j", date(enddate, "-3 days", "weekday 4")) - 1) / 7 as isoweek_e, \
CAST(strftime("%Y", startdate) as INTEGER) as year_s, \
CAST(strftime("%Y", enddate) as INTEGER) as year_e \
FROM homeloc WHERE \
(year_s < {0:d} AND year_e = {0:d} AND isoweek_e >= {1:d}) OR \
(year_s = {0:d} AND isoweek_s <= {1:d} AND year_e > {0:d}) OR \
(year_s = {0:d} AND isoweek_s <= {1:d} AND year_e = {0:d} AND isoweek_e >= {1:d})'.format(year, week)
elif args.period == 'month':
    sys.stdout.write("Loading home location for month %i of %i...\n" %
                     (month, year))
    command = 'SELECT startdate,enddate,lat,lon,homeradius, \
CAST(strftime("%Y", startdate) as INTEGER) as year_s, \
CAST(strftime("%Y", enddate) as INTEGER) as year_e, \
CAST(strftime("%m", startdate) as INTEGER) as month_s, \
CAST(strftime("%m", enddate) as INTEGER) as month_e \
FROM homeloc WHERE \
(year_s <= {0:d} AND month_s <= {1:d} AND year_e > {0:d}) OR \
(year_s <= {0:d} AND month_s <= {1:d} AND year_e = {0:d} AND month_e >= {1:d}) OR \
(year_s < {0:d} AND year_e > {0:d}) OR \
(year_s < {0:d} AND year_e >= {0:d} AND month_e >= {1:d}) OR \
(year_s <= {0:d} AND month_s <= {1:d} AND year_e > {0:d})'.format(year, month)
elif args.period == 'year':
    sys.stdout.write("Loading home location for %i...\n" % (year))
    command = 'SELECT startdate,enddate,lat,lon,homeradius, \
CAST(strftime("%Y", startdate) AS INTEGER) as year_s, \
CAST(strftime("%Y", enddate) AS INTEGER) as year_e \
FROM homeloc WHERE (year_s <= {0:d} AND year_e >= {0:d})'.format(year)
elif args.period == 'all':
    sys.stdout.write("Loading all home locations...\n")
    command = 'SELECT startdate,enddate,lat,lon,homeradius FROM homeloc ORDER BY STARTDATE'
cursor.execute(command)
recs = cursor.fetchall()

mhlocs = 0
if len(recs) > 1:
    sys.stdout.write("More than one home location for the specified time.\n")
    mhlocs = 1
    hlocs = recs
elif len(recs) == 0:
    sys.stdout.write("WARNING: no home location records found for the \
specified time. Assuming all records are 'away' or 'traveling'.\n")
    hlat = -1
    hlon = -1
    hradius = -1
    hlocs = 0
else:
    hlat = (recs[0])[2]
    hlon = (recs[0])[3]
    hradius = (recs[0])[4]
    hlocs = 0

# 'command' selects the records from the period of interest
# 'command2' selects the final record from the previous period, so we can
#   correctly tag the first point of the current period
if args.period == 'week':
    command = 'SELECT *, \
(strftime("%j", date(UTC, "-3 days", "weekday 4")) - 1) / 7  as isoweek, \
CAST(strftime("%Y", UTC) AS INTEGER) as year \
FROM locations WHERE isoweek={0:d} AND year={1:d} \
ORDER by locations.UTC'.format(week, year)
    if week > 1:
        wsel = week - 1
        ysel = year
    else:
        wsel = 52
        ysel = year - 1
    command2 = 'SELECT *, \
(strftime("%j", date(UTC, "-3 days", "weekday 4")) - 1) / 7 as isoweek, \
CAST(strftime("%Y", UTC) AS INTEGER) as year \
FROM locations WHERE isoweek={0:d} AND year={1:d} \
ORDER by locations.UTC DESC LIMIT 1'.format(wsel, ysel)
elif args.period == 'month':
    command = 'SELECT *, \
CAST(strftime("%Y", UTC) AS INTEGER) as year, \
CAST(strftime("%m", UTC) AS INTEGER) as month \
FROM locations WHERE month={0:d} AND year={1:d} \
ORDER by locations.UTC'.format(month, year)
    if month > 1:
        msel = month - 1
        ysel = year
    else:
        msel = 12
        ysel = year - 1
    command2 = 'SELECT *, \
CAST(strftime("%Y", UTC) AS INTEGER) as year, \
CAST(strftime("%m", UTC) AS INTEGER) as month \
FROM locations WHERE month={0:d} AND year={1:d} \
ORDER by locations.UTC DESC LIMIT 1'.format(msel, ysel)
elif args.period == 'year':
    command = 'SELECT *, \
CAST(strftime("%Y", UTC) AS INTEGER) as year \
FROM locations WHERE year={0:d} ORDER by locations.UTC'.format(year)
    command2 = 'SELECT *, \
CAST(strftime("%Y", UTC) AS INTEGER) as year, \
CAST(strftime("%m", UTC) AS INTEGER) as month \
FROM locations WHERE month=12 AND year={0:d} \
ORDER by locations.UTC DESC LIMIT 1'.format(year - 1)
elif args.period == 'all':
    command = 'SELECT * FROM locations ORDER by locations.UTC'
cursor.execute(command)
recs = cursor.fetchall()
if len(recs) < 1:
    sys.stderr.write('ERROR: no records found for the requested time \
interval. Exiting.\n')
    sys.exit()

# fetch the final location from the previous time period, so we can properly
# analyze/tag the first datapoint of this time period
if args.period != 'all':
    cursor.execute(command2)
    preloc = cursor.fetchone()
    rec0 = preloc
else:
    rec0 = recs[0]

# go through the rows sequentially. First, check if the GPS location puts it
# within the "home" tolerance specified above. If it is, add that time to the
# amount spent at "home".
nrecs = len(recs)
loctype = 'away'
d = 0
sys.stdout.write("Processing GPS records...\n")
for rec1 in recs:
    if mhlocs:
        # figure out which homeloc is appropriate for this datestamp
        hradius = -1    # treat everything as 'away' if there's no homeloc
        i = 0
        for hopt in hlocs:
            if datetime.strptime(hopt[0], "%Y-%m-%d") <= datetime.strptime(rec1[0], "%Y-%m-%d %H:%M:%S") and datetime.strptime(hopt[1], "%Y-%m-%d") >= datetime.strptime(rec1[0], "%Y-%m-%d %H:%M:%S"):
                # have our home location
                hlat = hopt[2]
                hlon = hopt[3]
                hradius = hopt[4]
            i = i+1
    if rec1 == rec0:
        if hradius == -1:
            # it's all away
            atime += 0.
            if args.period == 'week':
                loctype = 'away'
        else:
            # first check if the rec is within the home distance
            dist = magellan.GreatCircDist([hlat, hlon], rec0[1:])
            if dist > hradius:
                # we're outside the home radius. chock this up as away
                # atime+=dechrs*60.
                loctype = 'away'
            else:
                # inside the home radius. we're in town
                # htime+=dechrs*60.
                loctype = 'home'
    else:
        tdiff = datetime.strptime(rec1[0], "%Y-%m-%d %H:%M:%S") - \
                datetime.strptime(rec0[0], "%Y-%m-%d %H:%M:%S")
        dechrs = tdiff.days*24+tdiff.seconds/3600.
        if hradius != -1:
            # first check if the rec is within the home distance
            dist = magellan.GreatCircDist([hlat, hlon], rec1[1:])
            if dist > hradius:
                # we're outside the home radius. see if we're traveling or not
                travdist = magellan.GreatCircDist(rec1[1:], rec0[1:])
                # now compute the average speed, see if we're traveling or not
                speed = travdist/dechrs # km/hr
                msspeed = speed/3.6 # m/s
                if msspeed > trinidad.travelspeed and dechrs < args.maxtime:
                    # we're traveling!
                    ttime += dechrs*60.
                    loctype = 'travel'
                else:
                    # we're away
                    if dechrs < args.maxtime:
                        atime += dechrs*60.
                    loctype = 'away'
            else:
                # inside the home radius. we're in town
                htime += dechrs*60.
                loctype = 'home'
        else:
            # no home radius. see if we're traveling or not
            travdist = magellan.GreatCircDist(rec1[1:], rec0[1:])
            # now compute the average speed, see if we're traveling or not
            speed = travdist/dechrs     # this is in km/hr
            msspeed = speed/3.6
            if msspeed > trinidad.travelspeed and dechrs < args.maxtime:
                # we're traveling!
                ttime += dechrs*60.
                loctype = 'travel'
            else:
                # we're away
                if dechrs < args.maxtime:
                    atime += dechrs*60.
                loctype = 'away'
    # reset the 'new' rec to the old rec
    rec0 = rec1
    # check for existing record
    cursor.execute('SELECT * FROM %s WHERE UTC = \'%s\'' %
                   (TABLENAME, rec0[0]))
    recs = cursor.fetchall()
    if len(recs) > 0:
        # default to automatically replacing. this should be given as a user
        # switch, when everything is integrated into magellan.py
        command = 'DELETE FROM %s WHERE UTC = \'%s\'' % \
                  (TABLENAME, rec0[0])
        cursor.execute(command)
        d = d+1
    # now insert the record (this currently works for all records)
    command = 'INSERT into %s (UTC,Type) values (\'%s\',\'%s\')' % \
              (TABLENAME, rec0[0], loctype)
    cursor.execute(command)
    # and loop to the next record

# after we've iterated over the time period, write the totals and percentages
# back into the database for that period (overwriting existing entries)
totaltime = atime+htime+ttime

sys.stdout.write("%s recorded a total time of approximately %f hours from %i \
records.\n" % (args.period, totaltime/60., nrecs))
sys.stdout.write("Replaced %i duplicate entries.\n" % (d))
if args.period == 'week' or args.period == 'month':
    sys.stdout.write("Submitting totals to SQL database...\n")
sys.stdout.write("Summary:\n\n")
sys.stdout.write("\tHours\tFraction\n")
sys.stdout.write("Home:\t{0:1.0f}\t{1:0.2f}\n".format(htime/60., htime/totaltime))
sys.stdout.write("Away:\t{0:1.0f}\t{1:0.2f}\n".format(atime/60., atime/totaltime))
sys.stdout.write("Travel:\t{0:1.0f}\t{1:0.2f}\n".format(ttime/60., ttime/totaltime))

# submit to the database
if args.period == 'week':
    command = 'REPLACE INTO analysis_weekly \
              (timeID,year,week,home,homefrac,away,awayfrac,travel, \
              travelfrac) \
              values (%i,%i,%i,%f,%f,%f,%f,%f,%f)' % \
              (magellan.yearid(year, week), year, week, htime,
               htime/totaltime, atime, atime/totaltime, ttime, ttime/totaltime)
elif args.period == 'month':
    command = 'REPLACE INTO analysis_monthly \
              (timeID,year,month,home,homefrac,away,awayfrac,travel, \
              travelfrac) \
              values (%i,%i,%i,%f,%f,%f,%f,%f,%f)' % \
              (magellan.yearid(year, month), year, month, htime,
               htime/totaltime, atime, atime/totaltime, ttime, ttime/totaltime)

if args.period == 'week' or args.period == 'month':
    cursor.execute(command)

# close SQL
cursor.close()
trinidad.closedb()
