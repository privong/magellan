#!/usr/bin/env python2
#
# loc_analyze.py
#
# Provide a (weekly/monthly) analysis of GPS log information.
# The information will be retreived from an SQL database
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
import ConfigParser
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

TABLENAME = "locations_spec"

TRAVELTHRESH = 13.5     # m/s

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
    print "Loading home location for week %i of %i..." % (week, year)
    command = 'SELECT * FROM homeloc WHERE \
              (YEAR(STARTDATE) < %i AND YEAR(ENDDATE) > %i) OR \
              (YEAR(STARTDATE) < %i AND YEAR(ENDDATE) = %i AND WEEK(ENDDATE,1) >= %i) OR \
              (YEAR(STARTDATE) = %i AND WEEK(STARTDATE,1) <= %i AND YEAR(ENDDATE) > %i) OR \
              (YEAR(STARTDATE) = %i AND WEEK(STARTDATE,1) <= %i AND YEAR(ENDDATE) = %i AND WEEK(ENDDATE,1) >= %i)' \
              % (year, year,
                 year, year, week,
                 year, week, year,
                 year, week, year, week)
elif args.period == 'month':
    print "Loading home location for month %i of %i..." % (month, year)
    command = 'SELECT * FROM homeloc WHERE \
             (YEAR(STARTDATE) <= %i AND MONTH(STARTDATE) <= %i AND \
              YEAR(ENDDATE) > %i) OR \
             (YEAR(STARTDATE) <= %i AND MONTH(STARTDATE) <= %i AND \
              YEAR(ENDDATE) = %i AND MONTH(ENDDATE) >= %i) OR \
             (YEAR(STARTDATE) < %i AND YEAR(ENDDATE) > %i) OR \
             (YEAR(STARTDATE) < %i AND YEAR(ENDDATE) >= %i AND \
              MONTH(ENDDATE) >= %i) OR \
             (YEAR(STARTDATE) <= %i AND MONTH(STARTDATE) <= %i AND\
              YEAR(ENDDATE) > %i)' \
             % (year, month, year,
                year, month, year, month,
                year, year,
                year, year, month,
                year, month, year)
elif args.period == 'year':
    print "Loading home location for %i..." % (year)
    command = 'SELECT * FROM homeloc WHERE \
               (YEAR(STARTDATE) <= %i AND YEAR(ENDDATE) >= %i)' \
               % (year, year)
elif args.period == 'all':
    print "Loading all home locations..."
    command = 'SELECT * FROM homeloc ORDER BY STARTDATE'
cursor.execute(command)
recs = cursor.fetchall()

mhlocs = 0
if len(recs) > 1:
    print "More than one home location for the specified time."
    mhlocs = 1
    hlocs = recs
elif len(recs) == 0:
    print "WARNING: no home location records found for the specified time. \
           Assuming all records are 'away' or 'traveling'."
    hlat = -1
    hlong = -1
    hradius = -1
    hlocs = 0
else:
    hlat = (recs[0])[2]
    hlong = (recs[0])[3]
    hradius = (recs[0])[4]
    hlocs = 0

if args.period == 'week':
    command = 'SELECT * FROM locations WHERE WEEK(UTC,1)=%i AND YEAR(UTC)=%i \
              ORDER by locations.UTC' % (week, year)
    command2 = 'SELECT * FROM locations WHERE WEEK(UTC,1)=%i AND YEAR(UTC)=%i \
               ORDER by locations.UTC DESC LIMIT 1' % \
               ((52, year-1), (week-1, year))[week > 1]
    # command3='SELECT * FROM locations WHERE WEEK(UTC,1)=%i AND YEAR(UTC)=%i \
    #          ORDER by locations.UTC' % ((0,year+1),(week+1,year))[week < 53]
elif args.period == 'month':
    command = 'SELECT * FROM locations WHERE MONTH(UTC)=%i AND YEAR(UTC)=%i \
              ORDER by locations.UTC' % (month, year)
    command2 = 'SELECT * FROM locations WHERE MONTH(UTC)=%i AND YEAR(UTC)=%i \
               ORDER by locations.UTC DESC LIMIT 1' % \
               ((12, year-1), (month-1, year))[month > 1]
    # command3='SELECT * FROM locations WHERE MONTH(UTC)=%i AND YEAR(UTC)=%i \
    #          ORDER by locations.UTC' % \
    #          ((1,year+1),(month+1,year))[month < 12]
elif args.period == 'year':
    command = 'SELECT * FROM locations WHERE YEAR(UTC)=%i \
              ORDER by locations.UTC' % (year)
    command2 = 'SELECT * FROM locations WHERE MONTH(UTC)=12 AND YEAR(UTC)=%i \
               ORDER by locations.UTC DESC LIMIT 1' % (year - 1)
elif args.period == 'all':
    command = 'SELECT * FROM locations ORDER by locations.UTC'
cursor.execute(command)
recs = cursor.fetchall()
if len(recs) < 1:
    sys.stderr.write('ERROR: no records found for the requested time \
                     interval. Exiting.\n')
    sys.exit()

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
print "Processing GPS records.."
for rec1 in recs:
    if mhlocs:
        # figure out which homeloc is appropriate for this datestamp
        hradius = -1    # treat everything as 'away' if there's no homeloc
        i = 0
        for hopt in hlocs:
            if hopt[0] <= rec1[0].date() and hopt[1] >= rec1[0].date():
                # have our home location
                hlat = hopt[2]
                hlong = hopt[3]
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
            dist = magellan.GreatCircDist([hlat, hlong], rec0[1:])
            if dist > hradius:
                # we're outside the home radius. chock this up as away
                # atime+=dechrs*60.
                loctype = 'away'
            else:
                # inside the home radius. we're in town
                # htime+=dechrs*60.
                loctype = 'home'
    else:
        if hradius != -1:
            # first check if the rec is within the home distance
            dist = magellan.GreatCircDist([hlat, hlong], rec1[1:])
            tdiff = rec1[0]-rec0[0]
            dechrs = tdiff.days*24+tdiff.seconds/3600.
            if dist > hradius:
                # we're outside the home radius. see if we're traveling or not
                travdist = magellan.GreatCircDist(rec1[1:], rec0[1:])
                # now compute the average speed, see if we're traveling or not
                speed = travdist/dechrs # km/hr
                msspeed = speed/3.6 # m/s
                if msspeed > TRAVELTHRESH and dechrs < args.maxtime:
                    # we're traveling!
                    ttime += dechrs*60.
                    loctype = 'travel'
                else:
                    # we're away
                    if dechrs < args.maxtime:
                        atime += dechrs*60.
                    loctype = 'away'
            else:
                tdiff = rec1[0]-rec0[0]
                # inside the home radius. we're in town
                htime += dechrs*60.
                loctype = 'home'
        else:
            # no home radius. see if we're traveling or not
            travdist = magellan.GreatCircDist(rec1[1:], rec0[1:])
            # now compute the average speed, see if we're traveling or not
            speed = travdist/dechrs     # this is in km/hr
            msspeed = speed/3.6
            if msspeed > TRAVELTHRESH and dechrs < args.maxtime:
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
                   (TABLENAME, rec0[0].strftime("%Y-%m-%d %H:%M:%S")))
    recs = cursor.fetchall()
    if len(recs) > 0:
        # default to automatically replacing. this should be given as a user
        # switch, when everything is integrated into magellan.py
        command = 'DELETE FROM %s WHERE UTC = \'%s\'' % \
                  (TABLENAME, rec0[0].strftime("%Y-%m-%d %H:%M:%S"))
        cursor.execute(command)
        d = d+1
    # now insert the record (this currently works for all records)
    command = 'INSERT into %s (UTC,Type) values (\'%s\',\'%s\')' % \
              (TABLENAME, rec0[0], loctype)
    cursor.execute(command)
    # and loop to the next record

# after we've iterated over the week write the totals, percentages of the week
# back into the database for that week (check to see that there isn't already
# an entry, ask before overwriting)
totaltime = atime+htime+ttime

print "%s recorded a total time of approximately %f hours from %i records." % \
      (args.period, totaltime/60., nrecs)
print "Replaced %i duplicate entries." % (d)
if args.period == 'week' or args.period == 'month':
    print "Submitting totals to SQL database.."

# submit to the database
if args.period == 'week':
    command = 'REPLACE INTO magellan.analysis_weekly \
              (timeID,year,week,home,homefrac,away,awayfrac,travel, \
              travelfrac) \
              values (%i,%i,%i,%f,%f,%f,%f,%f,%f)' % \
              (magellan.yearid(year, week), year, week, htime,
               htime/totaltime, atime, atime/totaltime, ttime, ttime/totaltime)
elif args.period == 'month':
    command = 'REPLACE INTO magellan.analysis_monthly \
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
