#!/bin/bash

echo $(date +"%T") Starting $0 …

function usage() { i
	echo "Usage: $0 
			-d YYYYmmdd 
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
export INDIR=~/data/gfs
export OUTDIR=~/data/twp/gfs

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

#-- Este código sería el más lógico, pero no acaba de funcionar...
#-- mv all.gfs tmp.gfs ; cdo selname,prmsl,10u,10v,vis,2t,2r,tp,SUNSD tmp.gfs all.gfs
#-- grib_copy -w levtype!=pl,stepTypeInternal=instant,shortName=prate tmp.gfs prate.gfs
#-- grib_copy -w levtype!=pl,stepTypeInternal=instant,shortName=tcc tmp.gfs tcc.gfs
#-- cat prate.gfs >> all.gfs
#-- cat tcc.gfs >> all.gfs
#-- rm -f tmp.gfs prate.gfs tcc.gfs
#-- 

mv all.gfs tmp.gfs ; cdo selname,prmsl,10u,10v,vis,2t,2r,tp,tcc,prate tmp.gfs all.gfs
mv all.gfs tmp.gfs ; grib_copy -w levtype!=pl,stepTypeInternal=instant/accum tmp.gfs all.gfs
rm -f tmp.gfs

#-----------------------------------------------------------------------------------
#--  Format conversion: from GRIB2 to NetCDF
#-----------------------------------------------------------------------------------
#--
rm -f all.nc
cdo -f nc copy all.gfs all.nc
rm all.gfs

#-----------------------------------------------------------------------------------
#--  Variables and dimensions cleaning
#-----------------------------------------------------------------------------------
#--  Imprescindible hacerlo porque si las variables comienzan por un número...
#--  ...las nco tools se quejan
#--
mv all.nc tmp.nc; ncrename -v 2r,r2 tmp.nc all.nc
mv all.nc tmp.nc; ncrename -v 2t,t2m tmp.nc all.nc
mv all.nc tmp.nc; ncrename -v 10u,u10  tmp.nc all.nc
mv all.nc tmp.nc; ncrename -v 10v,v10 tmp.nc all.nc

#--  Eliminación de dimensiones degeneradas
mv all.nc tmp.nc; ncwa -a height tmp.nc all.nc
mv all.nc tmp.nc; ncwa -a height_2 tmp.nc all.nc
mv all.nc tmp.nc; ncwa -a lev tmp.nc all.nc
mv all.nc tmp.nc; ncks -x -v height,height_2,lev tmp.nc all.nc
rm tmp.nc


#-----------------------------------------------------------------------------------
#--  Variables units
#-----------------------------------------------------------------------------------
#--

#-- ArcGIS necesita longitudes referidas a Greenwhich (positivas y negativas)
mv all.nc tmp.nc; ncap2 -O -s 'where(lon>180) lon=lon-360' tmp.nc all.nc

#-- temp: Kelvin -> Celsius
mv all.nc tmp.nc; ncap2 -O -s 't2m=t2m-273.15f' tmp.nc all.nc
ncatted -O -a units,t2m,o,c,"C" all.nc

#-- SUNSD: seconds -> hours
#--mv all.nc tmp.nc; ncap2 -O -s 'SUNSD=SUNSD/3600f' tmp.nc all.nc
#--ncatted -O -a units,SUNSD,o,c,"h" all.nc

#-- vis: m -> km
mv all.nc tmp.nc; ncap2 -O -s 'vis=vis/1000f' tmp.nc all.nc
ncatted -O -a units,vis,o,c,"km" all.nc

#-- tp: kg m**-2 --> l m**-2
#-- 1 kg of rain water spread over 1 square meter of surface is 1 mm in thickness
ncatted -O -a units,tp,o,c,"l m**-2" all.nc

#-- prate: kg m**-2 s**-1 --> l m**-2 hour**-1
#-- 1 kg of rain water spread over 1 square meter of surface is 1 mm in thickness
mv all.nc tmp.nc; ncap2 -O -s 'prate=prate*3600f' tmp.nc all.nc
ncatted -O -a units,prate,o,c,"l m**-2 h**-1" all.nc

#-- 
mv all.nc tmp.nc; ncap2 -O -s 'prmsl=prmsl/100f' tmp.nc all.nc
ncatted -O -a units,prmsl,o,c,"hPa" all.nc

#-- wind
mv all.nc tmp.nc; ncap2 -A -s 'ws=sqrt(u10^2+v10^2)' tmp.nc all.nc
ncatted -O -a units,ws,o,c,"m s**-1" all.nc
ncatted -O -a long_name,ws,o,c,"wind speed" all.nc
ncatted -O -a standard_name,ws,o,c,"wind_speed" all.nc
mv all.nc tmp.nc; ncap2 -A -s 'wd=57.29578f*(atan2(u10,v10))+180f' tmp.nc all.nc
ncatted -O -a units,wd,o,c,"grados (N=0º)" all.nc
ncatted -O -a long_name,wd,o,c,"wind direction" all.nc
ncatted -O -a standard_name,wd,o,c,"wind_direction" all.nc


#-----------------------------------------------------------------------------------
#--  Optional 
#-----------------------------------------------------------------------------------
#-- Time interpolation: from 3h to 1h
#-- cdo -intntime,3 all all-1h

#-- Clean
rm tmp.nc


#-----------------------------------------------------------------------------------
#--  Cell (grid) statistics
#-----------------------------------------------------------------------------------

#-- Temperatura máxima
ncwa -A -y max -a time -v t2m all.nc stat.nc
mv stat.nc tmp.nc; ncrename -v t2m,t2mmax tmp.nc stat.nc

#-- Temperatura mínima
ncwa -A -y min -a time -v t2m all.nc stat.nc
mv stat.nc tmp.nc; ncrename -v t2m,t2mmin tmp.nc stat.nc

#-- Temperatura media
ncwa -A -y avg -a time -v t2m all.nc stat.nc
mv stat.nc tmp.nc; ncrename -v t2m,t2mavg tmp.nc stat.nc

#-- Humedad máxima
ncwa -A -y max -a time -v r2 all.nc stat.nc
mv stat.nc tmp.nc; ncrename -v r2,r2max tmp.nc stat.nc

#-- Humedad mínima
ncwa -A -y min -a time -v r2 all.nc stat.nc
mv stat.nc tmp.nc; ncrename -v r2,r2min tmp.nc stat.nc

#-- Humedad media
ncwa -A -y avg -a time -v r2 all.nc stat.nc
mv stat.nc tmp.nc; ncrename -v r2,r2avg tmp.nc stat.nc

#-- Precipitación acumulada
ncwa -A -y max -a time -v tp all.nc stat.nc
mv stat.nc tmp.nc; ncrename -v tp,tpacc tmp.nc stat.nc

#-- Intensidad de precipitación
ncwa -A -y max -a time -v prate all.nc stat.nc
mv stat.nc tmp.nc; ncrename -v prate,pratemax tmp.nc stat.nc

#-- Velocidad del viento
ncwa -A -y max -a time -v ws all.nc stat.nc
mv stat.nc tmp.nc; ncrename -v ws,wsmax tmp.nc stat.nc

#-- attibutes
ncatted -O -a long_name,t2mmax,o,c,"2 metre temperature max" stat.nc
ncatted -O -a standard_name,t2mmax,o,c,"temperature_max" stat.nc
ncatted -O -a long_name,t2mmin,o,c,"2 metre temperature min" stat.nc
ncatted -O -a standard_name,t2mmin,o,c,"temperature_min" stat.nc
ncatted -O -a long_name,t2mavg,o,c,"2 metre temperature avg" stat.nc
ncatted -O -a standard_name,t2mavg,o,c,"temperature_avg" stat.nc
ncatted -O -a long_name,r2max,o,c,"2 metre relative humidity max" stat.nc
ncatted -O -a standard_name,r2max,o,c,"relative_humidity_max" stat.nc
ncatted -O -a long_name,r2min,o,c,"2 metre relative humidity min" stat.nc
ncatted -O -a standard_name,r2min,o,c,"relative_humidity_min" stat.nc
ncatted -O -a long_name,r2avg,o,c,"2 metre relative humidity avg" stat.nc
ncatted -O -a standard_name,r2avg,o,c,"relative_humidity_avg" stat.nc
ncatted -O -a long_name,tpacc,o,c,"total precipitation accumulated" stat.nc
ncatted -O -a standard_name,tpacc,o,c,"precipitation_acc" stat.nc
ncatted -O -a long_name,pratemax,o,c,"prate max" stat.nc
ncatted -O -a standard_name,pratemax,o,c,"prate max" stat.nc
ncatted -O -a long_name,wsmax,o,c,"wind speed max" stat.nc
ncatted -O -a standard_name,wsmax,o,c,"wind_speed_max" stat.nc
ncatted -O -a history,global,d,, stat.nc
ncatted -O -a history_of_appended_files,global,d,, stat.nc

#-- Clean
rm tmp.nc

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

ncatted -O -a institution,global,o,c,"The Weather Partner" stat.nc
ncatted -O -a history,global,d,, stat.nc

#-- time
#-- ArcGIS necesita que el dia y el mes tengan dos dígitos
caca=$(date -d "$stamp + $hh hours" +"%Y-%m-%d %H:00:00")
ncatted -O -a units,time,o,c,"hours since ${caca}" all.nc
ncatted -O -a units,time,o,c,"hours since ${caca}" stat.nc

#-----------------------------------------------------------------------------------
#--  Renaming and Cleaning
#-----------------------------------------------------------------------------------
#--
mkdir -p $OUTDIR/${stamp}/${hh}
mv all.nc $OUTDIR/${stamp}/${hh}/${ofile}-s$(printf %03d $tini)-e$(printf %03d $tend).nc
mv stat.nc $OUTDIR/${stamp}/${hh}/${ofile}-s$(printf %03d $tini)-e$(printf %03d $tend)-stat.nc

rm -f tmp.nc stat.nc

echo $(date +"%T") $0 finished!.
