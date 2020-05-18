#!/usr/bin/python

import arcpy
import os, sys
from arcgis.gis import GIS
import time
import sys
from datetime import datetime
import logging



# CONFIGURAR---------------------------

# configurar espacio de trabajo
base = r'D:\arcgis\projects\arcmeteo-v1.2'
logdir= os.path.join(base,"_logs")
#Configuracion de log, por si hiciera falta
nombreProyecto = "arcmeteo-v1.2"
logging.basicConfig(filename=os.path.join(logdir,"{}_{}{}".format(nombreProyecto,datetime.now().strftime("%d%m%Y_%H%M"),'.log')), filemode='w', format='%(asctime)-15s %(name)s - %(levelname)s - %(message)s',level=logging.INFO)


##########################

# netcdf de entrada
netcdf = r'D:\data\gfs\iberiav2.nc'

#nombre de la variable
lstVar=  ['rhavg',"tavg","tpacc"]
lstVarAlias =  ['Humedad relativa',"Temperatura media","Precipitación acumulada"]


# FGDB con la capa de zonas generalizada (vlyZonas = municipios here)
vlyZonas = base +r"\Municipios.gdb\MuniIberia"
clave = "codMuni"


# FGDB de salida
FGDB = "Stat.gdb"
vlyStat = base + r"/"+FGDB+ "/vlyStat"




########################################################

print(time.strftime("%H:%M:%S") )
arcpy.CheckOutExtension("Spatial")
arcpy.gp.logHistory = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference ("WGS 1984 Web Mercator (auxiliary sphere)")
arcpy.env.overwriteOutput = True
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.cellSize = 1000
arcpy.env.resamplingMethod = "BILINEAR"
tblStat = base + "/"+ FGDB+r"\tblStat"

# comprueba si existe la FGDB de trabajo
if arcpy.Exists(FGDB):
    arcpy.Delete_management (FGDB)    
arcpy.CreateFileGDB_management(base, FGDB)
print ("creada FGDB")


####################################################
print ("Empezamos el procesado de las variables...")
arcpy.management.CopyFeatures(vlyZonas,vlyStat)
numedia=0
for var in lstVar:
    print(lstVarAlias[numedia])
    arcpy.md.MakeNetCDFRasterLayer(netcdf, str(var) , "lon", "lat", "rly"+var, '', None, "BY_VALUE", "CENTER")
    arcpy.sa.ZonalStatisticsAsTable(vlyZonas, clave, "rly"+str(var), tblStat+"_"+var, "DATA", "MEAN", "CURRENT_SLICE")
    arcpy.management.AlterField(tblStat+"_"+var,"MEAN",str(var) ,str(lstVarAlias[numedia]))
    arcpy.management.JoinField(vlyStat, clave,tblStat+"_"+var, clave, lstVar)
    numedia= numedia+1

print ("..done!")

###################################################################

print ("Comenzamos la publicación en ArcGIS Online...")

# credenciales de ArcGIS Online
sd_fs_name = "vlyStat"
portal = "http://www.arcgis.com" 
user = "twp001"
password = "mierda00mierda"

# Set sharing options
shrOrg = True
shrEveryone = True
shrGroups = ""

#proyecto de Pro
aprx = base+ "/arcmeteo-v1.2.aprx"

# Local paths to create temporary content
sddraft = os.path.join(base, "vlyStat.sddraft")
sd = os.path.join(base, "vlyStat.sd")

# Create a new SDDraft and stage to SD
print("Creating SD file")
arcpy.env.overwriteOutput = True
prj = arcpy.mp.ArcGISProject(aprx)
mp = prj.listMaps()[1]
print("Found ArcGIS Pro Map: "+ str(mp))
arcpy.mp.CreateWebLayerSDDraft(mp, sddraft, sd_fs_name, "MY_HOSTED_SERVICES", "FEATURE_ACCESS",'', True, True)
arcpy.server.StageService(sddraft, sd)

print("Connecting to {}".format(portal))
gis = GIS(portal, user, password)

# Find the SD, update it, publish /w overwrite and set sharing and metadata
print("Search for original SD on portal")
sdItem = gis.content.search("{} AND owner:{}".format(sd_fs_name, user), item_type="Service Definition")[0]
print("Found SD: {}, ID: {} Overwriting...".format(sdItem.title, sdItem.id))
sdItem.update(data=sd)
print("Uploading and overwriting existing feature service...")
fs = sdItem.publish(overwrite=True)

if shrOrg or shrEveryone or shrGroups:
    print ("Setting sharing options...")
    fs.share(org=shrOrg, everyone=shrEveryone, groups=shrGroups)

print ("Finished updating: {}  ID: {}".format(fs.title, fs.id))

print (time.strftime("%H:%M:%S"))

