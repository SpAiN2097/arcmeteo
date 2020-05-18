#!/bin/bash

dd=$(date +"%d")
mm=$(date +"%m")
yy=$(date +"%Y")
day=$yy$mm$dd
export HOMEPROJ=~/arcmeteo

cd $HOMEPROJ/bin
./gfsdownload.sh -d $day -h 00 -r 0p25 -s 9 -e 81
