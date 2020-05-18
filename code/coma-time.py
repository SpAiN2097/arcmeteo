# ejecutar cmd como 
# "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" C:\Proyecto\DatosMeteo\netCDFaFGDB_y_publicarv2.py
# necesitamos Spatial 
# entrada sscc

import arcpy
import os, sys
from arcgis.gis import GIS
import time

# CONFIGURAR---------------------------
# configurar espacio de trabajo
base = r'D:\arcgis\projects\ArcMeteo-forge'
# netcdf de entrada
netCDF = base+r'\netcdf\iberiav2.nc'
#nombre de la variable
#lista = ['temp',"tp","rh","tavg","rhavg","tpacc"]
lista = ['temp',"tp","rh"]
lista = ['temp']
lista = ['tp']
listaalias = ['Temperatura','Precipitación total','Humedad relativa']
listaalias = ['Temperatura']
listaalias = ['Precipitación total']

# FGDB con la capa de sscc generalizada
sscc = base +r"\ArcMeteo-forge.gdb\ComarcasAgrarias"
clave = "CO_COMARCA"
# FGDB de salida
FGDB = "MeteoByComarcas.gdb"
FGDB = "PrecByComarcas.gdb"
muniCopy = base + r"/"+FGDB+ "/muni"
# credenciales de ArcGIS Online
sd_fs_name_slide = "Slide2_WFL1"
portal = "http://www.arcgis.com" 
user = "jlnavarro_plataformacovid"
password = "TWP_COVID19_"

# Set sharing options
shrOrg = True
shrEveryone = True
shrGroups = ""
#proyecto de Pro
prjPath = base+ "/ArcMeteo-forge.aprx"
# Fin de configuracion ---------------------------

print(time.strftime("%H:%M:%S") )
arcpy.CheckOutExtension("Spatial")
arcpy.gp.logHistory = False
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference ("WGS 1984 Web Mercator (auxiliary sphere)")
arcpy.env.overwriteOutput = True
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.cellSize = 1000
arcpy.env.resamplingMethod = "BILINEAR"
multicrf =  base + "/"+ FGDB+r"\multidimensional"
zonal_tabla = base + "/"+ FGDB+r"\zonal_tabla"
SalidaFinal = base + r"/"+FGDB +r"\PrecByComarcas"

# comprueba si existe la FGDB de trabajo
if arcpy.Exists(FGDB):
    arcpy.Delete_management (FGDB)    
arcpy.CreateFileGDB_management(base, FGDB)
print ("creada FGDB")
##########################################
arcpy.md.MakeMultidimensionalRasterLayer (netCDF, multicrf, lista, "ALL")
arcpy.sa.ZonalStatisticsAsTable(sscc, clave, multicrf, zonal_tabla, "DATA", "MEAN", "ALL_SLICES")

arcpy.CopyFeatures_management (sscc,muniCopy)
# para hacer el join multiple las capas y tablas deben estar en la misma FGDB
#join multiple, la salida es en memoria
arcpy.management.MakeQueryTable(muniCopy+";"+zonal_tabla, "SalidaFinal" , "USE_KEY_FIELDS", None, None, "muni.CO_COMARCA = zonal_tabla.CO_COMARCA")
arcpy.CopyFeatures_management ("SalidaFinal",SalidaFinal)


####################################################
###################################################################

print (time.strftime("%H:%M:%S"))
