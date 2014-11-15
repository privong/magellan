#!/usr/bin/python2
# populate the new timeID field in the analysis tables, based on the existing
# year and week/month columns.

import MySQLdb
import sys
import time
import math
import ConfigParser
import magellan
from datetime import date


cursor = magellan.initdb()
if sys.argv[1] == 'week':
    TABLENAME = "analysis_weekly"
    cursor.execute('SELECT year,week from %s' % (TABLENAME))
    recs = cursor.fetchall()
    for rec in recs:
        command = 'UPDATE %s set timeID = %s WHERE (year=%i and week=%i)' \
            % (TABLENAME, magellan.yearid(rec[0], rec[1]), rec[0], rec[1])
        cursor.execute(command)
if sys.argv[1] == 'month':
    TABLENAME = "analysis_monthly"
    cursor.execute('SELECT year,month from %s' % (TABLENAME))
    recs = cursor.fetchall()
    for rec in recs:
        command = 'UPDATE %s set timeID = %s WHERE (year=%i and month=%i)' \
            % (TABLENAME, magellan.yearid(rec[0], rec[1]), rec[0], rec[1])
        cursor.execute(command)
cursor.close()

magellan.closedb()
