# Changelog

## 0.3.x Series

### 0.3.x (in progress)

#### Enhancements

* loc_anlayze.py now prints a summary of the time period

#### Bug Fixes

* loc_analyze.py no longer claims data is being saved to the SQL database unless it actually is
* loc_analyze.py input handling fix that was causing default analysis to occur for a year earlier than desired

### 0.3.4 (2016 January 21)

* bugfix: week=0 now correctly interpreted as the 0th week of the year, rather than as a non-specified parameter
* bugfix: running ./loc_analyze.py in January with default options (or month=0) now correctly selects month 12 of the previous year

### 0.3.3 (2015 June 28)

* fix bug in map_location.py, introduced in 0.3.2

### 0.3.2 (2015 June 28)

* add "comment" column to homeloc table. This is not currently used in the processing, but may be used in the future, to annotate magellan output.
* fix single away location bug
* improved screen output in map_locations.py

### 0.3.1 (2015 May 01)

* bugfixes in sql_import.py
* improved error handling for configuration file
* fix bug in loc_analyze which could collect too many homelocs for a given week

#### plot_histogram

* add stacked bar chart for the histogram, now default
* histogram y-scale can be shown in fraction of a week (previous default), equivalent number of days in a week (new default), or hours in a week

### 0.3.0 (2014 November 17)

* Ability to re-analyze all locations in a single go (may require lots of memory for large datasets)
* Add some error-handling for the database connection
* license code under GPLv3

## 0.2.x Series

Note: Changelog is incomplete for the 0.2.x series.

### 0.2.1 (2014 November 16)

* bugfix in GreatCircDist()

### 0.2.0 (2014 November 16)

* Openstreemaps is now the default mapping service for creating away maps.

## 0.1.x Series

Note: Changelog is incomplete for the 0.1.x series.

### 0.1.2 (2014 November 15)

* Add monthly location maps
* Use time weighted average position for away maps
