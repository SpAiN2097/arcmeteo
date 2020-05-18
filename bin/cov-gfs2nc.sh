#!/bin/bash

echo $(date +"%T") Starting $0 …

function usage() { i
	echo "Usage: $0 -d YYYYmmdd 
	                -h {00,06,12,18} 
			-r {1p00,0p50,0p25} 
			-s tini {0,3,6...}
			-e tend {3,6,9...} 
			-o ofile" 
			1>&2; exit 1; }

while getopts "d:h:r:s:e:o:" OPTION; do
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
		o) #- output file
			ofile=$OPTARG ;;
		*) usage ;;
	esac
done

export HOMEPROJ=~/arcmeteo
cd $HOMEPROJ/work
export CDI_INVENTORY_MODE=time

for (( t=$tini; t<=$tend; t=t+3 )); do 
	ii=$(printf "%.3d " $t)
	#-- No se puede empezar en T+0 porque el T+0 tiene estructura diferente...
	echo Processing gfs.t${hh}z.pgrb2.${res}.f$ii...
	ln -s ~/data/gfs/gfs.${stamp}/${hh}/gfs.t${hh}z.pgrb2.${res}.f$ii tmp01.gfs
	#-- If NetCDF then ncks -d lat,35.5,44.0 -d lon,350.,4.5 
	#-- Iberia box (-10,35) --> (5,44)  
	[ $ofile == "iberia" ] && cdo sellonlatbox,-10,5,35,44 tmp01.gfs tmp02.gfs
	[ $ofile == "canarias" ] && cdo sellonlatbox,-18.8,-12.6,26.8,29.8 tmp01.gfs tmp02.gfs
	cat tmp02.gfs >> all.gfs
	rm tmp01.gfs tmp02.gfs
done

#-- Aquí tenemos todo en all.gfs

#-----------------------------------------------------------------------------------
#--  Variables selection
#-----------------------------------------------------------------------------------
#--  Antes de la conversión de formato porque nos ahorramos tiempo y conflictos
#--  Ifn netCDF then ncks -v 2t,2r,10u,10v,sp,prate 
#--
mv all.gfs tmp.gfs
#-- cdo selname,10u,10v,vis,2t,2r,tp,SUNSD tmp.gfs all.gfs
cdo selname,10u,10v,2t,2r,tp tmp.gfs all.gfs
rm tmp.gfs

#-----------------------------------------------------------------------------------
#--  Format conversion: from GRIB2 to NetCDF
#-----------------------------------------------------------------------------------
#--
rm all.nc
cdo -f nc copy all.gfs all.nc
rm all.gfs

#-----------------------------------------------------------------------------------
#--  Variables and dimensions cleaning
#-----------------------------------------------------------------------------------
#--  Imprescindible hacerlo porque si las variables comienzan por un número...
#--  ...las nco tools se quejan
#--
mv all.nc tmp.nc
ncrename -v 2t,temp -v 2r,rh -v 10u,u10 -v 10v,v10 tmp.nc all.nc

#--  Eliminación de dimensiones degeneradas
mv all.nc tmp.nc
ncwa -a height tmp.nc all.nc
mv all.nc tmp.nc
ncwa -a height_2 tmp.nc all.nc
mv all.nc tmp.nc
ncks -x -v height,height_2 tmp.nc all.nc
rm tmp.nc


#-----------------------------------------------------------------------------------
#--  Variables units
#-----------------------------------------------------------------------------------
#--

#-- ArcGIS necesita longitudes referidas a Greenwhich (positivas y negativas)
mv all.nc tmp.nc
ncap2 -O -s 'where(lon>180) lon=lon-360' tmp.nc all.nc

#-- temp: Kelvin -> Celsius
mv all.nc tmp.nc
ncap2 -O -s 'temp=temp-273.15f' tmp.nc all.nc
ncatted -O -a units,temp,o,c,"C" all.nc

#-- SUNSD: seconds -> hours
#-- mv all.nc tmp.nc
#-- ncap2 -O -s 'SUNSD=SUNSD/3600f' tmp.nc all.nc
#-- ncatted -O -a units,SUNSD,o,c,"h" all.nc

#-- vis: m -> km
#-- mv all.nc tmp.nc
#-- ncap2 -O -s 'vis=vis/1000f' tmp.nc all.nc
#-- ncatted -O -a units,vis,o,c,"km" all.nc

#-- tp: kg m**-2 --> l m**-2
#-- 1 kg of rain water spread over 1 square meter of surface is 1 mm in thickness
ncatted -O -a units,tp,o,c,"l m**-2" all.nc


#-----------------------------------------------------------------------------------
#--  Optional 
#-----------------------------------------------------------------------------------
#-- Time interpolation: from 3h to 1h
#-- cdo -intntime,3 all all-1h

#-----------------------------------------------------------------------------------
#--  Cell (grid) statistics
#-----------------------------------------------------------------------------------

#-- Temperatura máxima
ncwa -A -y max -a time -v temp all.nc out.nc
mv out.nc tmp.nc; ncrename -v temp,tmax tmp.nc out.nc

#-- Temperatura mínima
ncwa -A -y min -a time -v temp all.nc out.nc
mv out.nc tmp.nc; ncrename -v temp,tmin tmp.nc out.nc

#-- Temperatura media
ncwa -A -y avg -a time -v temp all.nc out.nc
mv out.nc tmp.nc; ncrename -v temp,tavg tmp.nc out.nc

#-- Precipitación acumulada (l/(m**2·dia))
ncwa -A -y sum -a time -v tp all.nc out.nc
mv out.nc tmp.nc; ncrename -v tp,tpacc tmp.nc out.nc

#-- Humedad máxima
ncwa -A -y max -a time -v rh all.nc out.nc
mv out.nc tmp.nc; ncrename -v rh,rhmax tmp.nc out.nc

#-- Humedad mínima
ncwa -A -y min -a time -v rh all.nc out.nc
mv out.nc tmp.nc; ncrename -v rh,rhmin tmp.nc out.nc

#-- Humedad media
ncwa -A -y avg -a time -v rh all.nc out.nc
mv out.nc tmp.nc; ncrename -v rh,rhavg tmp.nc out.nc

#-- attibutes
ncatted -O -a long_name,tmax,o,c,"2 metre temperature max" out.nc
ncatted -O -a standard_name,tmax,o,c,"temperature_max" out.nc
ncatted -O -a long_name,tmin,o,c,"2 metre temperature min" out.nc
ncatted -O -a standard_name,tmin,o,c,"temperature_min" out.nc
ncatted -O -a long_name,tavg,o,c,"2 metre temperature avg" out.nc
ncatted -O -a standard_name,tavg,o,c,"temperature_avg" out.nc
ncatted -O -a long_name,rhmax,o,c,"2 metre relative humidity max" out.nc
ncatted -O -a standard_name,rhmax,o,c,"relative_humidity_max" out.nc
ncatted -O -a long_name,rhmin,o,c,"2 metre relative humidity min" out.nc
ncatted -O -a standard_name,rhmin,o,c,"relative_humidity_min" out.nc
ncatted -O -a long_name,rhavg,o,c,"2 metre relative humidity avg" out.nc
ncatted -O -a standard_name,rhavg,o,c,"relative_humidity_avg" out.nc
ncatted -O -a long_name,tpacc,o,c,"total precipitation accumulated" out.nc
ncatted -O -a standard_name,tpacc,o,c,"precipitation_acc" out.nc
ncatted -O -a history,global,d,, out.nc
ncatted -O -a history_of_appended_files,global,d,, out.nc

#-- Clean
rm tmp.nc

#-- Y si lo queremos unir todo
#
#-- Eliminamos time de out.nc
mv out.nc tmp.nc; ncks -x -v time tmp.nc out.nc
#-- Append netcdfs
ncks -A out.nc all.nc



#-----------------------------------------------------------------------------------
#-- Global attributes 
#-----------------------------------------------------------------------------------
#--
ncatted -O -a institution,global,o,c,"The Weather Partner" all.nc
ncatted -O -a CDO,global,d,, all.nc
ncatted -O -a CDI,global,d,, all.nc
ncatted -O -a NCO,global,d,, all.nc
ncatted -O -a nco_openmp_thread_number,global,d,, all.nc
ncatted -O -a history_of_appended_files,global,d,, all.nc
ncatted -O -a history,global,d,, all.nc

#-- time
#-- ArcGIS necesita que el dia y el mes tengan dos dígitos
stamp=$(date -d "$stamp + $hh hours" +"%Y-%m-%d %H:00:00")
ncatted -O -a units,time,o,c,"hours since ${stamp}" all.nc

#-----------------------------------------------------------------------------------
#--  Renaming and Cleaning
#-----------------------------------------------------------------------------------
#--
mv all.nc ${ofile}v2.nc
rm tmp.nc out.nc

echo $(date +"%T") $0 finished!.
