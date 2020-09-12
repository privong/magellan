#!/usr/bin/env python
"""
sql_import.py

Load a textfile (CSV) of GPS data and store it into a SQL database.
The log file should have the following format:
UTC time,lat,long,horiz accuracy,alt,vert accuracy,speed,heading,battery

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
import os
import re
import argparse
import magellan


parser = argparse.ArgumentParser(description='Import a CSV file with GPS data \
        into the Magellan database.')
parser.add_argument('files', type=str, default=False, nargs='+',
                    help='File(s) to import')
args = parser.parse_args()

trinidad = magellan.magellan()
scur = trinidad.initdb()

TABLENAME = "locations"

e = 0
f = 0
for filename in args.files:
    i = 0
    d = 0
    if not os.path.isfile(filename):
        sys.stderr.write(filename + " not found. Skipping.\n")
        continue
    infile = open(filename, "r")
    if re.search('gpx', filename):
        import gpxpy
        gpx = gpxpy.parse(infile)
        for track in gpx.tracks:
            for segment in track.segments:
                for loc in segment.points:
                    # set some default values we don't expect to get :(
                    elev = -1
                    hacc = 2000     # default/conservative value
                    vacc = -1
                    speed = 0
                    heading = -1
                    batt = -1
                    # do we have elevation?
                    if loc.has_elevation():
                        elev = loc.elevation
                    # make sure we don't already have an entry for this time
                    command = 'SELECT * FROM %s WHERE UTC = \'%s\'' % \
                              (TABLENAME,
                               loc.time.strftime("%Y-%m-%d %H:%M:%S"))
                    scur.execute(command)
                    recs = scur.fetchall()
                    if len(recs) > 0:
                        # default to automatically replacing. this should be
                        # given as a user switch, when everything is integrated
                        # into magellan.py
                        command = 'DELETE FROM %s WHERE UTC = \'%s\'' % \
                                  (TABLENAME,
                                   loc.time.strftime("%Y-%m-%d %H:%M:%S"))
                        scur.execute(command)
                        d += 1
                    # INSERT INTO locations VALUES
                    # (datetime,lat,long,horizacc,alt,vertacc,speed,
                    # heading,battery)
                    command = 'INSERT INTO %s VALUES \
                              (\'%s\',%f,%f,%f,%f,%f,%f,%f,%i)' % \
                              (TABLENAME,
                               loc.time.strftime("%Y-%m-%d %H:%M:%S"),
                               loc.latitude, loc.longitude, hacc, elev, vacc,
                               speed, heading, batt)
                    scur.execute(command)
                    i += 1
    else:
        while infile:
            line = infile.readline()
            n = len(line)
            if n == 0:
                break
            if i > 0:
                s = line.split(',')
                batt = -1
                vacc = -1
                # make sure we don't already have an entry for this time
                command = 'SELECT * FROM %s WHERE UTC = \'%s\'' % \
                          (TABLENAME, re.sub('T', ' ', s[0].split('Z')[0]))
                scur.execute(command)
                recs = scur.fetchall()
                if len(recs) > 0:
                    # default to automatically replacing. this should be given
                    # as a user switch, when everything is integrated into
                    # magellan.py
                    command = 'DELETE FROM %s WHERE UTC = \'%s\'' % \
                              (TABLENAME, re.sub('T', ' ', s[0].split('Z')[0]))
                    scur.execute(command)
                    d += 1
                # INSERT INTO locations VALUES
                # (datetime,lat,long,horizacc,alt,vertacc,speed,
                # heading,battery)
                command = 'INSERT INTO %s VALUES \
                          (\'%s\',%f,%f,%f,%f,%f,%f,%f,%i)' % \
                          (TABLENAME, s[0].split('Z')[0], float(s[1]),
                           float(s[2]), float(s[4]), float(s[3]), vacc,
                           float(s[6]), float(s[5].rstrip('%\n')), batt)
                scur.execute(command)
                i += 1
            else:
                i = 1
        i -= 1  # to correct for the counting of the first row
    sys.stdout.write("%i unique records imported from %s. " % (i-d, filename))
    sys.stdout.write("%i duplicate records replaced.\n" % (d))
    e += i
    f += d
    infile.close()
# close SQL
scur.close()
trinidad.closedb()

sys.stdout.write("%i total records imported. %i new and %i duplicates.\n" %
                 (e, e-f, f))
