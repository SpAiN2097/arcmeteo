#!/bin/bash

dd=$(date +"%d")
mm=$(date +"%m")
yy=$(date +"%Y")
day=$yy$mm$dd

export HOMEPROJ=~/arcmeteo
export OUTDIR=~/data/twp/gfs

cd $HOMEPROJ/bin
./bas-gfs2nc.sh -d $day -h 00 -r 0p25 -s 9 -e 33 -o iberia
./bas-gfs2nc.sh -d $day -h 00 -r 0p25 -s 33 -e 57 -o iberia
./bas-gfs2nc.sh -d $day -h 00 -r 0p25 -s 57 -e 81 -o iberia
./bas-gfs2nc.sh -d $day -h 00 -r 0p25 -s 9 -e 33 -o canarias
./bas-gfs2nc.sh -d $day -h 00 -r 0p25 -s 33 -e 57 -o canarias
./bas-gfs2nc.sh -d $day -h 00 -r 0p25 -s 57 -e 81 -o canarias
./bas-gfs2nc.sh -d $day -h 00 -r 0p25 -s 9 -e 33 -o colombia
./bas-gfs2nc.sh -d $day -h 00 -r 0p25 -s 33 -e 57 -o colombia
./bas-gfs2nc.sh -d $day -h 00 -r 0p25 -s 57 -e 81 -o colombia


#-----------------------------------------------------------------
#--  Montage & Concatenation
#-----------------------------------------------------------------

cd $OUTDIR/$day/00
ncrcat iberia-s???-e???.nc bas-iberia-time.nc
ncecat -u time iberia-s???-e???-stat.nc bas-iberia-stat.nc
ncrcat canarias-s???-e???.nc bas-canarias-time.nc
ncecat -u time canarias-s???-e???-stat.nc bas-canarias-stat.nc
ncrcat colombia-s???-e???.nc bas-colombia-time.nc
ncecat -u time colombia-s???-e???-stat.nc bas-colombia-stat.nc


#-----------------------------------------------------------------
#--  Uploading
#-----------------------------------------------------------------

curl -v --connect-timeout 30 -u TWP:'COVID-TWP_3$r1' -T bas-iberia-time.nc ftp://188.87.202.154/TWP_basic/
curl -v --connect-timeout 30 -u TWP:'COVID-TWP_3$r1' -T bas-iberia-stat.nc ftp://188.87.202.154/TWP_basic/
curl -v --connect-timeout 30 -u TWP:'COVID-TWP_3$r1' -T bas-canarias-time.nc ftp://188.87.202.154/TWP_basic/
curl -v --connect-timeout 30 -u TWP:'COVID-TWP_3$r1' -T bas-canarias-stat.nc ftp://188.87.202.154/TWP_basic/
