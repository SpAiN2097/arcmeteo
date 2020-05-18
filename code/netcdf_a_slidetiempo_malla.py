# ejecutar cmd como 
# "C:\Program Files\ArcGIS\Pro\bin\Python\envs\arcgispro-py3\python.exe" C:\Proyecto\DatosMeteo\netCDFaFGDB_y_publicarv2.py
# necesitamos Spatial 
# entrada sscc

import arcpy
import os, sys
from arcgis.gis import GIS
import time
from arcgis import GIS
import json
#import descargarFicherosFTP
import logging
from datetime import datetime

# CONFIGURAR---------------------------
# configurar espacio de trabajo
base = r'C:\trabajo\TWP'
logdir= os.path.join(base,"_logs")
nombreProyecto = "Slide"
logging.basicConfig(filename=os.path.join(logdir,"{}_{}{}".format(nombreProyecto,datetime.now().strftime("%d%m%Y_%H%M"),'.log')), filemode='w', format='%(asctime)-15s %(name)s - %(levelname)s - %(message)s',level=logging.INFO)
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
sscc = base +r"\Municipios\Comarcas.gdb\Comarcas_iberia"
ssccCanarias = base +r"\Municipios\Comarcas.gdb\Comarcas_canarias"
clave = "CO_COMARCA"
variable2 = "variable"
transponer = clave+";"+variable2
# FGDB de salida
FGDB = "Salida_slide.gdb"
FGDBcanarias = "Salida_slide_canarias.gdb"
muniCopy = base + r"/"+FGDB+ "/comarcas"
muniCopyCanarias = base + r"/"+FGDBcanarias+ "/ComarcasCanarias"
muniMerge = base + r"/"+FGDB+ "/ComarcasEspaña"
# credenciales de ArcGIS Online
sd_fs_name_slide = "Slide2_WFL1"
portal = "http://www.arcgis.com" 
user = "jlnavarro_plataformacovid"
password = "TWP_COVID19_"

# Set sharing options
shrOrg = True
shrEveryone = False
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
SalidaFinal = base + r"/"+FGDB +r"\ComarcasIberia_Meteo"
SalidaFinalCanarias = base + r"/"+FGDBcanarias +r"\ComarcasCanarias_Meteo"
Slide =  base + r"/"+FGDB +r"\Slide"
##

# comprueba si existe la FGDB de trabajo
if arcpy.Exists(base +"\\"+FGDB):
    arcpy.Delete_management (FGDB)    
arcpy.CreateFileGDB_management(base, FGDB)
print ("creada FGDB")
logging.info ("creada FGDB")
##########################################
#Iberia###
arcpy.md.MakeMultidimensionalRasterLayer (netCDFIberia, multicrf, lista, "ALL")
arcpy.sa.ZonalStatisticsAsTable(sscc, clave, multicrf, zonal_tabla, "DATA", "MEAN", "ALL_SLICES")

arcpy.CopyFeatures_management (sscc,muniCopy)
# para hacer el join multiple las capas y tablas deben estar en la misma FGDB
#join multiple, la salida es en memoria
arcpy.management.MakeQueryTable(muniCopy+";"+zonal_tabla, "SalidaFinal" , "USE_KEY_FIELDS", None, None, "comarcas.CO_COMARCA = zonal_tabla.CO_COMARCA")
logging.info ("Join")
arcpy.CopyFeatures_management ("SalidaFinal",SalidaFinal)
logging.info ("salida iberia")

#############################################
#Canarias
# comprueba si existe la FGDB de trabajo
if arcpy.Exists(base +"\\"+FGDBcanarias):
    arcpy.Delete_management (FGDBcanarias)    
arcpy.CreateFileGDB_management(base, FGDBcanarias)
print ("creada FGDB")
logging.info ("creada FGDB CAnarias")
##########################################
#Canarias###
arcpy.md.MakeMultidimensionalRasterLayer (netCDFCanarias, multicrfCanarias, lista, "ALL")
arcpy.sa.ZonalStatisticsAsTable(ssccCanarias, clave, multicrfCanarias, zonal_tablacanarias, "DATA", "MEAN", "ALL_SLICES")

arcpy.CopyFeatures_management (ssccCanarias,muniCopyCanarias)
# para hacer el join multiple las capas y tablas deben estar en la misma FGDB
#join multiple, la salida es en memoria
arcpy.management.MakeQueryTable(muniCopyCanarias+";"+zonal_tablacanarias, "SalidaFinal_" , "USE_KEY_FIELDS", None, None, "ComarcasCanarias.CO_COMARCA = zonal_tabla.CO_COMARCA")
# "muniCanarias.codMuni = zonal_tabla.codMuni")
arcpy.CopyFeatures_management ("SalidaFinal_",SalidaFinalCanarias)

#merge
arcpy.Merge_management (SalidaFinal+";"+SalidaFinalCanarias,Slide )
arcpy.management.DeleteField(Slide, "Dimensions;AREA;COUNT;ZONE_CODE;OBJECTID_1")
arcpy.management.AddSpatialIndex(Slide, 0, 0, 0)

####################################################
###################################################################
print ("comenzamos publicación")
logging.info ("comenzamos publicación")
# Local paths to create temporary content
relPath = sys.path[0]
sddraft = os.path.join(relPath, "Slide.sddraft")
sd = os.path.join(relPath, "Slide.sd")

# Create a new SDDraft and stage to SD
print("Creating SD file")
logging.info ("Creating SD file")
arcpy.env.overwriteOutput = True
prj = arcpy.mp.ArcGISProject(prjPath)
mp = prj.listMaps()[2]

arcpy.mp.CreateWebLayerSDDraft(mp, sddraft, sd_fs_name_slide, "MY_HOSTED_SERVICES", "FEATURE_ACCESS",'', True, True)
arcpy.StageService_server(sddraft, sd)

print("Connecting to {}".format(portal))
gis = GIS(portal, user, password)

# Find the SD, update it, publish /w overwrite and set sharing and metadata
print("Search for original SD on portal…")
sdItem = gis.content.search("{} AND owner:{}".format(sd_fs_name_slide, user), item_type="Service Definition")[0]
print("Found SD: {}, ID: {} n Uploading and overwriting…".format(sdItem.title, sdItem.id))
sdItem.update(data=sd)
print("Overwriting existing feature service…")
logging.info ("Overwriting existing feature service…")
fs = sdItem.publish(overwrite=True)

if shrOrg or shrEveryone or shrGroups:
    print ("Setting sharing options…")
    fs.share(org=shrOrg, everyone=shrEveryone, groups=shrGroups)

print ("Finished updating: {} – ID: {}".format(fs.title, fs.id))
logging.info  ("Finished updating: {} – ID: {}".format(fs.title, fs.id))
##Actualizar time
"""
item = gis.content.get ('c756b08e13974acba99c8e8dde28195b')
data = item.get_data()
del data['widgets']['timeSlider']['properties']['startTime']
del data['widgets']['timeSlider']['properties']['endTime']
item.update(data=json.dumps(data))
"""

print (time.strftime("%H:%M:%S"))