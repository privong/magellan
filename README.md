# magellan

Tools for analyzing logged GPS location data. Includes determining if a GPS location is consistent with being "home", "away" (greater than specified distance from "home"), and "traveling" (average speed betweeen it and the previous point being above some threshold).

As of v0.5.0, data are stored in a sqlite3 database.

Possible outputs include histograms of time spent each week/month in the above states and a map of unique "away" locations visited.

## Requirements

* python3
* numpy
* matplotlib (for histogram plotting)
* cartopy (for map generation)
* gpxpy (for importing gpx files)

## Documentation

* `README.md` This file.
* `magellan.sql` sqlite3 database structure
* [Autumn 2011 Article in 2600](https://github.com/privong/magellan/wiki/2600-Article), which resulted from my early work on what would become **magellan**

## Scripts

* `map_locations.py` Generate a png thumbnail from OSM or GMaps of all "away" locations visited in a given week, month, or year.
* `loc_analyze.py` Determine if a given location qualifies as "home", "away", or "traveling"
* `plot_histogram.py` Make plots of week home/away/travel fractions for the past 10 weeks or the past year.
* `sql_import.py` import a CSV table of GPS locations to the database.

## Other

* `magellan.cfg.example` Example configuration file. Rename to ```magellan.cfg``` after entering your particular values.
* `magellan.py` magellan python library
