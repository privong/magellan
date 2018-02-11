# magellan

Tools for analyzing logged GPS location data. Includes determining if a GPS location is consistent with being "home", "away" (greater than specified distance from "home"), and "traveling" (average speed betweeen it and the previous point being above some threshold).

Possible outputs include histograms of time spent each week/month in the above states and a map of unique "away" locations visited.

## Requirements

* MySQL
* python-mysqldb
* matplotlib (for histogram plotting)
* numpy
* cartopy (for map generation)

## Documentation

* `README.md` This file.
* `magellan.sql` MySQL database structure
* `TIPBOARD.md` Information on sending magellan analysis information to a [Tipboard](http://tipboard.readthedocs.org) dashboard instance.
* [Autumn 2011 Article in 2600](https://github.com/privong/magellan/wiki/2600-Article), which resulted from my early work on what would become **magellan**

## Scripts

* `map_locations.py` Generate a png thumbnail from OSM or GMaps of all "away" locations visited in a given week, month, or year.
* `loc_analyze.py` Determine if a given location qualifies as "home", "away", or "traveling"
* `plot_histogram.py` Make plots of week home/away/travel fractions for the past 10 weeks or the past year.
* `sql_import.py` import a CSV table of GPS locations to the database.
* `magellan_dashboard.py` Upload histogram location information to a [tipboard](https://github.com/allegro/tipboard) dashboard

## Other

* `magellan.cfg.example` Example configuration file. Rename to ```magellan.cfg``` after entering your particular values.
* `magellan/` magellan python library
