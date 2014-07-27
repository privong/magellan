#!/usr/bin/python2
#
# loc_analyze.py
#
# Provide a (weekly/monthly) analysis of Palm Pre tracking information.
# The information will be retreived from an SQL database
#
# USAGE: loc_anaylze.py week/month [week#/month#] [year]
# week/month must be selected to specify weekly or monthly analysis
# If neither is specified, the most recent full week/month will be used.
# If only week/month is specified, the current year is assumed.

import MySQLdb
import sys
import time
import math
import ConfigParser
import magellan
from datetime import date

cursor=magellan.initdb()

TABLENAME="locations_spec"

TRAVELTHRESH=13.5 # speed threshold which determines if you're "traveling" or "away" (in m/s)

htime=0		# home time in minutes
atime=0		# away time in minutes
ttime=0		# travel time in minutes

# process arguments, decide which week and year we are using.
# how many arguments do we have?
today=date.today()
nargs=len(sys.argv)
if nargs==1:
    # default to week mode, and use the previous week
    mode='week'
    week=(today.isocalendar())[1]-1
    year=(today.isocalendar())[0]
if nargs>1:
    # we've specified a mode
    if sys.argv[1]=='week':
        mode='week'
        if nargs==2:
            week=(today.isocalendar())[1]-1
            year=(today.isocalendar())[0]
            if week<1:
                # we need to figure out what the last week of the past year was
                year=year-1
                week=(date(year,12,31).isocalendar())[0]
        elif nargs==3:
            week=int(sys.argv[2])
            year=(today.isocalendar())[0]
        elif nargs==4:
            week=int(sys.argv[2])
            year=int(sys.argv[3])
    elif sys.argv[1]=='month':
        mode='month'
        if nargs==2:
            month=today.month-1
            year=(today.isocalendar())[0]
            if month<1:
                month=12
                year=year-1
        elif nargs==3:
            month=int(sys.argv[2])
            year=(today.isocalendar())[0]
        elif nargs==4:
            month=int(sys.argv[2])
            year=int(sys.argv[3])

# get home location from the 'homeloc' database
# there should be a better way to select this...
if mode=='week':
    print "Loading home location for week %i of %i..." % (week,year)
    command='SELECT * FROM homeloc where (YEAR(STARTDATE) < %i AND (YEAR(ENDDATE) > %i OR YEAR(ENDDATE)=0000)) OR (YEAR(STARTDATE)=%i AND WEEK(STARTDATE,1)<%i AND (YEAR(ENDDATE)>%i or YEAR(ENDDATE)=0000)) OR (YEAR(STARTDATE)=%i AND WEEK(STARTDATE,1)<%i AND YEAR(ENDDATE)=%i AND WEEK(ENDDATE,1)>%i) OR (YEAR(STARTDATE)=%i and WEEK(STARTDATE,1)=%i) OR (YEAR(ENDDATE)=%i and WEEK(ENDDATE,1)=%i)' % (year,year,year,week,year,year,week,year,week,year,week,year,week)
elif mode=='month':
    print "Loading home location for month %i of %i..." % (month,year)
    command='SELECT * FROM homeloc where (YEAR(STARTDATE) < %i AND (YEAR(ENDDATE) > %i OR YEAR(ENDDATE)=0000)) OR (YEAR(STARTDATE)=%i AND MONTH(STARTDATE)<%i AND (YEAR(ENDDATE)>%i or YEAR(ENDDATE)=0000)) OR (YEAR(STARTDATE)=%i AND MONTH(STARTDATE)<%i AND YEAR(ENDDATE)=%i AND MONTH(ENDDATE)>%i) OR (YEAR(ENDDATE)=%i and MONTH(ENDDATE)=%i) or (YEAR(STARTDATE)=%i AND MONTH(STARTDATE)=%i)' % (year,year,year,month,year,year,month,year,month,year,month,year,month)
cursor.execute(command)
recs=cursor.fetchall()

mhlocs=0
if len(recs) > 1:
    print "More than one home location for the specified time."
    mhlocs=1
    hlocs=recs
elif len(recs)==0:
    print "WARNING: no home location records found for the specified time. Assuming all records are 'away' or 'traveling'."
    hlat=-1
    hlong=-1
    hradius=-1
    hlocs=0
else:
    hlat=(recs[0])[2]
    hlong=(recs[0])[3]
    hradius=(recs[0])[4]
    hlocs=0

if mode=='week':
    command='SELECT * FROM locations WHERE WEEK(UTC,1)=%i AND YEAR(UTC)=%i ORDER by locations.UTC' % (week,year)
    command2='SELECT * FROM locations WHERE WEEK(UTC,1)=%i AND YEAR(UTC)=%i ORDER by locations.UTC DESC' % ((52,year-1),(week-1,year))[week > 1]
    #command3='SELECT * FROM locations WHERE WEEK(UTC,1)=%i AND YEAR(UTC)=%i ORDER by locations.UTC' % ((0,year+1),(week+1,year))[week < 53]
elif mode=='month':
    command='SELECT * FROM locations WHERE MONTH(UTC)=%i AND YEAR(UTC)=%i ORDER by locations.UTC' % (month,year)
    command2='SELECT * FROM locations WHERE MONTH(UTC)=%i AND YEAR(UTC)=%i ORDER by locations.UTC DESC' % ((12,year-1),(month-1,year))[month > 1]
    #command3='SELECT * FROM locations WHERE MONTH(UTC)=%i AND YEAR(UTC)=%i ORDER by locations.UTC' % ((1,year+1),(month+1,year))[month < 12]
cursor.execute(command)
recs=cursor.fetchall()
cursor.execute(command2)
preloc=cursor.fetchone()
#cursor.execute(command3)
#postloc=cursor.fetchone()


if len(recs)<1:
    sys.stderr.write('ERROR: no records found for the requested time interval. Exiting.\n')
    sys.exit()

# go through the rows sequentially. First, check if the GPS location puts it
# within the "home" tolerance specified above. If it is, add that time to the 
# amount spent at "home".
rec0=preloc
nrecs=len(recs)
loctype='away'
d=0
print "Processing GPS records.."
for rec1 in recs:
    if mhlocs:
        # figure out which homeloc is appropriate for this datestamp
        hradius=-1	# failsafe: treat everything as 'away' if there's no matching
                                # homeloc
        i=0
        for hopt in hlocs:
            if hopt[0] <= rec1[0].date() and hopt[1] >= rec1[0].date():
                # have our home location
                hlat=hopt[2]
                hlong=hopt[3]
                hradius=hopt[4]
            i=i+1
    if rec1==rec0:
        if hradius==-1:
            # it's all away
            atime+=dechrs*60.
            if mode=='week':
                loctype='away'
        else:
            # first check if the rec is within the home distance
            dist=magellan.GreatCircDist([hlat,hlong],rec0[1:])
            if dist > hradius:
                # we're outside the home radius. chock this up as away
                #atime+=dechrs*60.
                loctype='away'
            else:
                # inside the home radius. we're in town
                #htime+=dechrs*60.
                loctype='home'
    else: 
        if hradius!=-1:
            # first check if the rec is within the home distance
            dist=magellan.GreatCircDist([hlat,hlong],rec1[1:])
            tdiff=rec1[0]-rec0[0]
            dechrs=tdiff.days*24+tdiff.seconds/3600.
            if dist > hradius:
                # we're outside the home radius. see if we're traveling or not
                travdist=magellan.GreatCircDist(rec1[1:],rec0[1:])
                # now compute the average speed, see if we're traveling or not
                speed=travdist/dechrs	# this is in km/hr
                msspeed=speed/3.6
                if msspeed > TRAVELTHRESH:
                    # we're traveling!
                    ttime+=dechrs*60.
                    loctype='travel'
                else:
                    # we're away
                    atime+=dechrs*60.
                    loctype='away'
            else:
                tdiff=rec1[0]-rec0[0]
                dechrs=tdiff.days*24+tdiff.seconds/3600.
                # inside the home radius. we're in town
                htime+=dechrs*60.
                loctype='home'
        else:
            # no home radius. see if we're traveling or not
            travdist=magellan.GreatCircDist(rec1[1:],rec0[1:])
            # now compute the average speed, see if we're traveling or not
            speed=travdist/dechrs     # this is in km/hr
            msspeed=speed/3.6
            if msspeed > TRAVELTHRESH:
                # we're traveling!
                ttime+=dechrs*60.
                loctype='travel'
            else:
                # we're away
                atime+=dechrs*60.
                loctype='away'
    # reset the 'new' rec to the old rec
    rec0=rec1
    # check for existing record
    cursor.execute('SELECT * FROM %s WHERE UTC = \'%s\'' % (TABLENAME,rec0[0].strftime("%Y-%m-%d %H:%M:%S")))
    recs=cursor.fetchall()
    if len(recs)>0:
        # default to automatically replacing. this should be given as a user
        # switch, when everything is integrated into magellan.py
        command='DELETE FROM %s WHERE UTC = \'%s\'' % (TABLENAME,rec0[0].strftime("%Y-%m-%d %H:%M:%S"))
        cursor.execute(command)
        d=d+1
    # now insert the record (this currently works for all records)
    command='INSERT into %s (UTC,Type) values (\'%s\',\'%s\')' % (TABLENAME,rec0[0],loctype)
    cursor.execute(command)
    # and loop to the next record

# after we've iterated over the week write the totals, percentages of the week
# back into the database for that week (check to see that there isn't already
# an entry, ask before overwriting)
totaltime=atime+htime+ttime

print "%s recorded a total time of approximately %f hours from %i records." % (mode,totaltime/60.,nrecs)
print "Replaced %i duplicate entries." % (d)
print "Submitting totals to SQL database.."

# submit to the database
if mode=='week':
    command='REPLACE INTO magellan.analysis_weekly (timeID,year,week,home,homefrac,away,awayfrac,travel,travelfrac) values (%i,%i,%i,%f,%f,%f,%f,%f,%f)' % (magellan.yearid(year,week),year,week,htime,htime/totaltime,atime,atime/totaltime,ttime,ttime/totaltime)
elif mode=='month':
    command='REPLACE INTO magellan.analysis_monthly (timeID,year,month,home,homefrac,away,awayfrac,travel,travelfrac) values (%i,%i,%i,%f,%f,%f,%f,%f,%f)' % (magellan.yearid(year,month),year,month,htime,htime/totaltime,atime,atime/totaltime,ttime,ttime/totaltime)

cursor.execute(command)

# close SQL
cursor.close()
#scon.close()
