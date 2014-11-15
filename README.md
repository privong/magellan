magellan
========

Tools for analyzing logged GPS location data. Includes determining if a GPS location is consistent with being "home", "away" (greater than specified distance from "home"), and "traveling" (average speed betweeen it and the previous point being above some threshold).

Outputs include histograms of time spent each week/month in the above states and a map of unique "away" locations visited each week.

Documentation
-------------
* README.md - This file.
* magellan.sql - MySQL database structure
* [Autumn 2011 Article in 2600](https://github.com/privong/magellan/wiki/2600-Article), which resulted from my early work on what would become **magellan**

Scripts
-------
* map_weekly.py	- Generate a png thumbnail from googlemaps of all "away" locations visited in the last week.
* loc_analyze.py - Determine if a given location qualifies as "home", "away", or "traveling"
* plot_histogram.py - Make plots of week totals for the past 10 weeks or the past year.
* sql_import.py - import a CSV table of GPS locations to the database.

Other
-----
* magellan.cfg.example - Example configuration file. Rename to '.magellan' after entering your particular values.
* magellan/	- magellan python library
