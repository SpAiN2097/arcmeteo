#!/bin/bash

dd=$(date +"%d")
mm=$(date +"%m")
yy=$(date +"%Y")
day=$yy$mm$dd
export HOMEPROJ=~/arcmeteo

cd $HOMEPROJ/bin
./cov-gfs2nc.sh -d $day -h 00 -r 0p25 -s 9 -e 33 -o iberia
./cov-gfs2nc.sh -d $day -h 00 -r 0p25 -s 9 -e 33 -o canarias

cd $HOMEPROJ/work
curl -v --connect-timeout 30 -u TWP:'COVID-TWP_3$r1' -T iberiav2.nc ftp://188.87.202.154/TWP/
curl -v --connect-timeout 30 -u TWP:'COVID-TWP_3$r1' -T canariasv2.nc ftp://188.87.202.154/TWP/

#cp *v2.nc /mnt/d/arcgis/projects/COVID-19/TWP/automatizacion/necdfFTP
