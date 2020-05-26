#!/bin/bash

PRJNAME=arcmeteo
cd $HOME/$PRJNAME/work
fname=bas-canarias-stat.nc
fname=bas-iberia-stat.nc

cat > ncap2.in << EOF
// Alert on t2mavg
t2mavg_alert = 0*(t2mavg <= 23) + 1*(t2mavg > 23 && t2mavg < 25) + 2*(t2mavg >= 25);
EOF

mv $fname caca.nc
ncap2 -F -S ncap2.in caca.nc $fname
rm caca.nc ncap2.in
