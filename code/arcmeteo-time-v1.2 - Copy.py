import arcpy
import os, sys
from arcgis.gis import GIS
import time
from arcgis import GIS
#import json
import logging
from datetime import datetime

# CONFIGURAR---------------------------

# configurar espacio de trabajo
base = r'D:\arcgis\projects\arcmeteo-v1.2'
logdir= os.path.join(base,"_logs")
nombreProyecto = "arcmeteo-v1.2"
print("{}_{}{}".format(nombreProyecto,datetime.now().strftime("%d%m%Y_%H%M"),'.log'))
#logging.basicConfig(filename=os.path.join(logdir,"{}_{}{}".format(nombreProyecto,datetime.now().strftime("%d%m%Y_%H%M"),'.log')), filemode='w', format='%(asctime)-15s %(name)s - %(levelname)s - %(message)s',level=logging.INFO)

# netcdf de entrada
netcdf = r'D:\data\gfs\iberiav2.nc'

#nombre de la variable
lstVar = ['temp']
lstVarAlias = ['Temperatura']
lstVar = ['temp',"tp","rh"]
lstVarAlias = ['Temperatura','Precipitación','Humedad Relativa']

# FGDB con la capa de vlyZonas generalizada
vlyZonas = base +r"\ComarcasAgrarias.gdb\ComarcasAgrarias"
clave = "CO_COMARCA"
variable2 = "variable"
transponer = clave+";"+variable2

# FGDB de salida
FGDB = "Time.gdb"
vlyZonasCopy = base + r"/"+FGDB+ "/vlyZonasCopy"



# Fin de configuracion ---------------------------

print(time.strftime("%H:%M:%S") )
arcpy.CheckOutExtension("Spatial")
arcpy.gp.logHistory = False
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference ("WGS 1984 Web Mercator (auxiliary sphere)")
arcpy.env.overwriteOutput = True
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.cellSize = 1000
arcpy.env.resamplingMethod = "BILINEAR"
multicrf = base + "/"+ FGDB +r"\multicrf"
tblZonal = base + "/"+ FGDB +r"\tblZonal"
vlyTime =  base + r"/"+FGDB +r"\vlyTime"

# comprueba si existe la FGDB de trabajo
if arcpy.Exists(base +"\\"+FGDB):
    arcpy.Delete_management (FGDB)    
arcpy.management.CreateFileGDB(base, FGDB)
print ("creada FGDB")

##########################################

print("MakeMultidimensionalRasterLayer...")
arcpy.md.MakeMultidimensionalRasterLayer (netcdf, multicrf, lstVar, "ALL")
print("...done!")
print("ZonalStatisticsAsTable...")
arcpy.sa.ZonalStatisticsAsTable(vlyZonas, clave, multicrf, tblZonal, "DATA", "MEAN", "ALL_SLICES")
print("...done!")

print("MakeQueryTable...")
arcpy.management.CopyFeatures (vlyZonas,vlyZonasCopy)
# para hacer el join multiple las capas y tablas deben estar en la misma FGDB
# join multiple, la salida es en memoria
arcpy.management.MakeQueryTable(vlyZonasCopy+";"+tblZonal, "vlyTime-in-memory" , "USE_KEY_FIELDS", None, None, "vlyZonasCopy.CO_COMARCA = tblZonal.CO_COMARCA")
#logging.info ("Join")
arcpy.management.CopyFeatures ("vlyTime-in-memory", vlyTime)
print("...done!")
#logging.info ("salida")


####################################################



print ("Publishing to ArcGIS Online...")

# credenciales de ArcGIS Online
sdfName = "vlyTime"
portal = "http://www.arcgis.com" 
user = "twp001"
password = "mierda00mierda"

# Set sharing options
shrOrg = True
shrEveryone = False
shrGroups = ""

#proyecto de Pro
prjPath = base+ "/arcmeteo-v1.2.aprx"


# Local paths to create temporary content
sddraft = os.path.join(base, "vlyTime.sddraft")
sd = os.path.join(base, "vlyTime.sd")

# Create a new SDDraft and stage to SD
print("Creating SD file")
arcpy.env.overwriteOutput = True
prj = arcpy.mp.ArcGISProject(prjPath)
mp = prj.listMaps()[0]

arcpy.mp.CreateWebLayerSDDraft(mp, sddraft, sdfName, "MY_HOSTED_SERVICES", "FEATURE_ACCESS",'', True, True)
arcpy.StageService_server(sddraft, sd)

print("Connecting to {}".format(portal))
gis = GIS(portal, user, password)

# Find the SD, update it, publish /w overwrite and set sharing and metadata
print("Search for original SD on portal...")
sdItem = gis.content.search("{} AND owner:{}".format(sdfName, user), item_type="Service Definition")[0]
print("Found SD: {}, ID: {} Uploading...".format(sdItem.title, sdItem.id))
sdItem.update(data=sd)
print("Overwriting existing feature service...")
fs = sdItem.publish(overwrite=True)

if shrOrg or shrEveryone or shrGroups:
    print ("Setting sharing options...")
    fs.share(org=shrOrg, everyone=shrEveryone, groups=shrGroups)

print ("Finished updating: {} ID: {}".format(fs.title, fs.id))


print (time.strftime("%H:%M:%S"))
