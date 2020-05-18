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
base = r'C:\Proyecto\COVID-19\TWP\automatizacion'
# netcdf de entrada
netCDFIberia = base+r'\necdfFTP\iberiav2.nc'
netCDFCanarias = base+r'\necdfFTP\canariasv2.nc'
#nombre de la variable
#lista = ['temp',"tp","rh","tavg","rhavg","tpacc"]
lista = ['temp',"tp","rh"]
listamedia=  ['rhavg',"tavg","tpacc"]
listamediaAlias =  ['Humedad relativa',"Temperatura media","Precipitación acumulada"]
#listaalias = ['Temperatura','Precipitación total','Humedad relativa',"Temperatura media","Humedad relativa media","Precipitación acumulada"]
listaalias = ['Temperatura','Precipitación total','Humedad relativa']
# FGDB con la capa de sscc generalizada
sscc = base +r"\Municipios\Municipios.gdb\MuniIberiav2"
ssccCanarias = base +r"\Municipios\Municipios.gdb\MuniCanariasv2"
clave = "codMuni"
variable2 = "variable"
transponer = clave+";"+variable2
# FGDB de salida
FGDB = "Salida_slide.gdb"
FGDBcanarias = "Salida_slide_canarias.gdb"
muniCopy = base + r"/"+FGDB+ "/muni"
muniCopyCanarias = base + r"/"+FGDBcanarias+ "/muniCanarias"
muniMerge = base + r"/"+FGDB+ "/muniEspaña"
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
prjPath = base+ "/TWP.aprx"
#prjPathCanarias = base+ "/TWP_canarias.aprx"
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
multicrfCanarias =  base + "/"+ FGDBcanarias+r"\multidimensional"
zonal_tabla = base + "/"+ FGDB+r"\zonal_tabla"
zonal_tablacanarias = base + "/"+ FGDBcanarias+r"\zonal_tabla"
SalidaFinal = base + r"/"+FGDB +r"\MunicipiosMeteo"
SalidaFinalCanarias = base + r"/"+FGDBcanarias +r"\MunicipiosMeteo"
Slide =  base + r"/"+FGDB +r"\Slide"

# comprueba si existe la FGDB de trabajo
if arcpy.Exists(FGDB):
    arcpy.Delete_management (FGDB)    
arcpy.CreateFileGDB_management(base, FGDB)
print ("creada FGDB")
##########################################
#Iberia###
arcpy.md.MakeMultidimensionalRasterLayer (netCDFIberia, multicrf, lista, "ALL")
arcpy.sa.ZonalStatisticsAsTable(sscc, clave, multicrf, zonal_tabla, "DATA", "MEAN", "ALL_SLICES")

arcpy.CopyFeatures_management (sscc,muniCopy)
# para hacer el join multiple las capas y tablas deben estar en la misma FGDB
#join multiple, la salida es en memoria
arcpy.management.MakeQueryTable(muniCopy+";"+zonal_tabla, "SalidaFinal" , "USE_KEY_FIELDS", None, None, "muni.codMuni = zonal_tabla.codMuni")
arcpy.CopyFeatures_management ("SalidaFinal",SalidaFinal)

#############################################
#Canarias
# comprueba si existe la FGDB de trabajo
if arcpy.Exists(FGDBcanarias):
    arcpy.Delete_management (FGDBcanarias)    
arcpy.CreateFileGDB_management(base, FGDBcanarias)
print ("creada FGDB")
##########################################
#Canarias###
arcpy.md.MakeMultidimensionalRasterLayer (netCDFCanarias, multicrfCanarias, lista, "ALL")
arcpy.sa.ZonalStatisticsAsTable(ssccCanarias, clave, multicrfCanarias, zonal_tablacanarias, "DATA", "MEAN", "ALL_SLICES")

arcpy.CopyFeatures_management (ssccCanarias,muniCopyCanarias)
# para hacer el join multiple las capas y tablas deben estar en la misma FGDB
#join multiple, la salida es en memoria
arcpy.management.MakeQueryTable(muniCopyCanarias+";"+zonal_tablacanarias, "SalidaFinal_" , "USE_KEY_FIELDS", None, None, "muniCanarias.codMuni = zonal_tabla.codMuni")
arcpy.CopyFeatures_management ("SalidaFinal_",SalidaFinalCanarias)

#merge
arcpy.Merge_management (SalidaFinal+";"+SalidaFinalCanarias,Slide )

####################################################
###################################################################


print (time.strftime("%H:%M:%S"))