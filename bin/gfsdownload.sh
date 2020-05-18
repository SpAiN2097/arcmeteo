#!/bin/bash 

#----------------------------------------------------------------------------------
#-- Download GFS datafiles
#----------------------------------------------------------------------------------

echo $(date +"%T") $0 …

function usage() { 
	echo "Usage: $0 -d YYYYmmdd 
	                -h {00,06,12,18} 
			-r {1p00,0p50,0p25} 
			-s tini {0,1,2...}
			-e tend {1,2,3...}" 
			1>&2; exit 1; }

while getopts "d:h:r:s:e:" OPTION; do
	case $OPTION in
		d) #- forecast run day in format $(date +"%Y%m%d")
			stamp=$OPTARG ;;
		h) #- forecast run hour in {00, 06, 12, 18}
			hh=$OPTARG ;;
		r) #- horizontal resolution in {1p00, 0p50, 0p25}
			res=$OPTARG ;;
		s) #- start timesteps {0,1,2,3...}
			tini=$OPTARG ;;
		e) #- end timesteps {1,2,3...}
			tend=$OPTARG ;;
		*) usage ;;
	esac
done

for (( t=$tini; t<=$tend; t=t+3)); do 
	ii=$(printf "%.3d " $t)
	echo gfs.t${hh}z.pgrb2.${res}.f$ii
	#echo Would do \
	curl --disable-epsv --create-dirs --connect-timeout 30 -m 3600 \
		-u anonymous:USER_ID@INSTITUTION \
		-o ~/data/gfs/gfs.${stamp}/${hh}/gfs.t${hh}z.pgrb2.${res}.f$ii \
		ftp://ftpprd.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/gfs.${stamp}/${hh}/gfs.t${hh}z.pgrb2.${res}.f$ii
done

echo $(date +"%T") $0 finished!
