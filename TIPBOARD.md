# Tipboard Integration

Magellan can optionally interface with a [Tipboard](http://tipboard.readthedocs.org) dashboard instance, using the magellan_dashboard.py script.
This requires a working Tipboard instance and the associated API URL and API key, which can be entered into the magellan.cfg configuration file.

## Types of Tiles

Currently, only one tile output is possible:

* home/away/travel stacked histogram. This requires a tileid of 'magellan' and a tiletype of 'cumulative_flow'.
