#!/usr/bin/env python
"""
sql_import.py

Import GPS logging data into a SQL database. The file can be:
    - CSV (with columns: UTC time,lat,lon,horiz accuracy,
           alt,vert accuracy,speed,heading,[battery])
    - GPX (requires `gpxpy` module)

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
from datetime import datetime
import magellan
import v990_tools


def getargs():
    """
    Get command line arguments
    """
    parser = argparse.ArgumentParser(description='Import a CSV file with GPS \
data into the Magellan database.')
    parser.add_argument('files', type=str, default=False, nargs='+',
                        help='File(s) to import')
    parser.add_argument('--v990', default=False, action='store_true',
                        help='Input CSV file is from a Columbus V-990 GPS \
logger.')
    return parser.parse_args()


def find_dupe(scur, table, time):
    """
    Check if a duplicate entry exists. Return True if it does exist.

    Parameters:
        - time: datetime object
        - table: SQL table name
    """

    command = 'SELECT * FROM %s WHERE UTC = \'%s\'' % \
              (table,
               time.strftime("%Y-%m-%d %H:%M:%S"))
    scur.execute(command)
    recs = scur.fetchall()

    return bool(len(recs))


def delete_record(scur, table, time):
    """
    Delete a single record, referenced by `time`
    """
    command = 'DELETE FROM %s WHERE UTC = \'%s\'' % \
              (table,
               time.strftime("%Y-%m-%d %H:%M:%S"))
    scur.execute(command)


def insert_record(scur, table, entry):
    """
    Add a record to the database
    """

    # INSERT INTO locations VALUES
    # (datetime,lat,long,horizacc,alt,vertacc,speed,
    # heading,battery)
    # NOTE: currently sets vertical accuracy and battery to -1.
    command = 'INSERT INTO %s VALUES \
              (\'%s\',%f,%f,%f,%f,%f,%f,%f,%i)' % \
              (table, entry[0].split('Z')[0], float(entry[1]),
               float(entry[2]), float(entry[4]), float(entry[3]), -1,
               float(entry[6]), float(entry[5].rstrip('%\n')), -1)
    scur.execute(command)


def import_records(scur, table, records):
    """
    Take a numpy array of records and load it into the database, checking for
    duplicates.
    """

    ndel = 0
    ninp = len(records)
    for entry in records:
        if find_dupe(scur, table, entry['time']):
            delete_record(scur, table, entry['time'])
            ndel += 1
        insert_record(scur, table, entry)

    return ninp, ndel


def main():
    """
    Do the main things
    """

    args = getargs()

    # initialize database connection
    trinidad = magellan.magellan()
    scur = trinidad.initdb()

    TABLENAME = "locations"

    e = 0
    f = 0
    # loop over input files
    for filename in args.files:
        i = 0
        d = 0
        if not os.path.isfile(filename):
            continue

        if args.v990:
            # load and import CSV files from a Columbus V990 logger
            recs = v990_tools.load_track(infile, average=True)
            i, d = import_records(scur, TABLENAME, recs)
            sys.stdout.write("%i unique records imported from %s. " %
                             (i-d, filename))
            sys.stdout.write("%i duplicate records replaced.\n" % (d))
            e += i
            f += d
            continue

        # Effectively, if not a V990 file, do the usual thing
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
                        speed = 0
                        heading = -1
                        # do we have elevation?
                        if loc.has_elevation():
                            elev = loc.elevation
                        # check for existing entry in the table
                        # INSERT INTO locations VALUES
                        # (datetime,lat,long,horizacc,alt,vertacc,speed,
                        # heading,battery)
                        command = 'INSERT INTO %s VALUES \
                                  (\'%s\',%f,%f,%f,%f,%f,%f,%f,%i)' % \
                                  (TABLENAME,
                                   loc.time.strftime("%Y-%m-%d %H:%M:%S"),
                                   loc.latitude, loc.longitude, hacc,
                                   elev, -1,
                                   speed, heading, -1)
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
                    import_records(scur, TABLENAME, s)
                    if find_dupe(scur, TABLENAME, loc.time):
                        # default to automatically replacing. this should be
                        # given as a user switch, when everything is integrated
                        # into magellan.py
                        command = 'DELETE FROM %s WHERE UTC = \'%s\'' % \
                                  (TABLENAME, re.sub('T', ' ', s[0].split('Z')[0]))
                        scur.execute(command)
                        d += 1
                    i += 1
                else:
                    i = 1
            i -= 1  # to correct for the counting of the first row
        sys.stdout.write("%i unique records imported from %s. " %
                         (i-d, filename))
        sys.stdout.write("%i duplicate records replaced.\n" % (d))
        e += i
        f += d
        infile.close()
    # close SQL
    scur.close()
    trinidad.closedb()

    sys.stdout.write("%i total records imported. %i new and %i duplicates.\n" %
                     (e, e-f, f))


if __name__ == '__main__':
    main()
