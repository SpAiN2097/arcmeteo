import arcpy
import os, sys
from arcgis.gis import GIS
import time
from datetime import datetime


pyName = "arcmeteo-time-v1.2.py"
baseDir = r'D:\arcgis\projects\arcmeteo-v1.2'

logformat = "%Y-%m-%d %H:%M:%S"
print("Started {} at {}".format(pyName, datetime.now().strftime(logformat)))

#--
#-- Inputs
#--
netcdf = r'D:\data\gfs\iberiav2.nc'
lstVar = ['temp',"tp","rh"]
lstVarAlias = ['Temperatura','Precipitación','Humedad Relativa']
vlyZonas = baseDir +r"\ComarcasAgrarias.gdb\ComarcasAgrarias"
clave = "CO_COMARCA"

#--
#-- Outputs
#--
FGDB = "Time.gdb"
vlyOutput =  baseDir + "/"+FGDB +r"\vlyTime"


#--
#-- Environment
#--

arcpy.CheckOutExtension("Spatial")
arcpy.gp.logHistory = True
arcpy.env.outputCoordinateSystem = arcpy.SpatialReference ("WGS 1984 Web Mercator (auxiliary sphere)")
arcpy.env.overwriteOutput = True
arcpy.env.parallelProcessingFactor = "100%"
arcpy.env.cellSize = 1000
arcpy.env.resamplingMethod = "BILINEAR"
multicrf = baseDir + "/"+ FGDB +r"\multicrf"
tblStats = baseDir + "/"+ FGDB +r"\tblStats"
vlyZonasCopy = baseDir + "/"+FGDB+ "/vlyZonasCopy"


#-- (Re)create outFGDB
print('Recreating output FGDB...', end='')
if arcpy.Exists(baseDir +"\\"+FGDB):
    arcpy.management.Delete(FGDB)    
arcpy.management.CreateFileGDB(baseDir, FGDB)
print ("ok!")


####################################################

print('MakeMultidimensionalRasterLayer()...', end='')
arcpy.md.MakeMultidimensionalRasterLayer (netcdf, multicrf, lstVar, "ALL")
print("ok!")

print('ZonalStatisticsAsTable()..', end='')
arcpy.sa.ZonalStatisticsAsTable(vlyZonas, clave, multicrf, tblStats, "DATA", "MEAN", "ALL_SLICES")
print("ok!")

print('MakeQueryTable()..', end='')
# para hacer el join multiple las capas y tablas deben estar en la misma FGDB
arcpy.management.CopyFeatures (vlyZonas,vlyZonasCopy)
# join multiple, la salida es en memoria
arcpy.management.MakeQueryTable(vlyZonasCopy+";"+tblStats, "vlyTime-in-memory" , "USE_KEY_FIELDS", None, None, "vlyZonasCopy.CO_COMARCA = tblStats.CO_COMARCA")
arcpy.management.CopyFeatures ("vlyTime-in-memory", vlyOutput)
print("ok!")


####################################################
print ("Publishing to ArcGIS Online...")

# credenciales de ArcGIS Online
sdfName = "vlyTime"
portal = "http://www.arcgis.com" 
user = "twp001"
password = "mierda00mierda"

# Set sharing options
shrOrg = True
shrEveryone = True
shrGroups = ""

aprx = baseDir+ "/arcmeteo-v1.2.aprx"

# Local paths to create temporary content
sddraft = os.path.join(baseDir, "vlyTime.sddraft")
sd = os.path.join(baseDir, "vlyTime.sd")

# Create a new SDDraft and stage to SD

prj = arcpy.mp.ArcGISProject(aprx)
mp = prj.listMaps()[0]
print("Creating SD file...", end='')
arcpy.mp.CreateWebLayerSDDraft(mp, sddraft, sdfName, "MY_HOSTED_SERVICES", "FEATURE_ACCESS",'', True, True)
arcpy.server.StageService(sddraft, sd)
print("ok!")

print("Connecting to {}...".format(portal), end='')
gis = GIS(portal, user, password)
print("ok!")

# Find the SD, update it, publish /w overwrite and set sharing and metadata
print("Search for original SD on portal...", end='')
sdItem = gis.content.search("{} AND owner:{}".format(sdfName, user), item_type="Service Definition")[0]
print("ok!")
print("Overwriting SD: {}, ID: {}...".format(sdItem.title, sdItem.id), end='')
sdItem.update(data=sd)
print("ok!")
print("Uploading...", end='')
fs = sdItem.publish(overwrite=True)
print("ok!")

if shrOrg or shrEveryone or shrGroups:
    fs.share(org=shrOrg, everyone=shrEveryone, groups=shrGroups)

print ("Published {} ID: {}".format(fs.title, fs.id))

print("Finished {} at {}".format(pyName, datetime.now().strftime(logformat)))