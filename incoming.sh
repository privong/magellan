#!/bin/sh
if [ -a ~/magellan/incoming/*.txt ]
  then
    echo "Found a file"
    for f in ~/magellan/incoming/*.txt
      do
        echo $f
        ~/magellan/sql_import.py $f
        rm $f
    done
fi
