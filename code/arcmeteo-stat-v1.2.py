import arcpy
import os, sys
from arcgis.gis import GIS
import time
from datetime import datetime


pyName = "arcmeteo-stat-v1.2.py"
baseDir = r'D:\arcgis\projects\arcmeteo-v1.2'

logformat = "%Y-%m-%d %H:%M:%S"
print("Started {} at {}".format(pyName, datetime.now().strftime(logformat)))

#--
#-- Inputs
#--
netcdf = r'D:\data\gfs\iberiav2.nc'
lstVar=  ['rhavg',"tavg","tpacc"]
lstVarAlias =  ['Humedad relativa',"Temperatura media","Precipitación acumulada"]
vlyZonas = baseDir +r"\Municipios.gdb\MuniIberia"
clave = "codMuni"

#--
#-- Outputs
#--
FGDB = "Stat.gdb"
vlyOutput = baseDir + r"/"+FGDB+ "/vlyStat"


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
tblStat = baseDir + "/"+ FGDB+r"\tblStat"

#-- (Re)create outFGDB
print('Recreating output FGDB...', end='')
if arcpy.Exists(FGDB):
    arcpy.management.Delete(FGDB)    
arcpy.management.CreateFileGDB(baseDir, FGDB)
print ("ok!")


####################################################

arcpy.management.CopyFeatures(vlyZonas,vlyOutput)
numedia=0
for var in lstVar:
    print("Processing "+lstVarAlias[numedia], "...", end='')
    arcpy.md.MakeNetCDFRasterLayer(netcdf, str(var) , "lon", "lat", "rly"+var, '', None, "BY_VALUE", "CENTER")
    arcpy.sa.ZonalStatisticsAsTable(vlyZonas, clave, "rly"+str(var), tblStat+"_"+var, "DATA", "MEAN", "CURRENT_SLICE")
    arcpy.management.AlterField(tblStat+"_"+var,"MEAN",str(var) ,str(lstVarAlias[numedia]))
    arcpy.management.JoinField(vlyOutput, clave,tblStat+"_"+var, clave, lstVar)
    numedia= numedia+1
    print("ok!")


###################################################################
print ("Publishing to ArcGIS Online...")

# credenciales de ArcGIS Online
sdfName = "vlyStat"
portal = "http://www.arcgis.com" 
user = "twp001"
password = "mierda00mierda"

# Set sharing options
shrOrg = True
shrEveryone = True
shrGroups = ""

aprx = baseDir+ "/arcmeteo-v1.2.aprx"

# Local paths to create temporary content
sddraft = os.path.join(baseDir, "vlyStat.sddraft")
sd = os.path.join(baseDir, "vlyStat.sd")

# Create a new SDDraft and stage to SD
print("Creating SD file...", end='')
prj = arcpy.mp.ArcGISProject(aprx)
mp = prj.listMaps()[1]
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