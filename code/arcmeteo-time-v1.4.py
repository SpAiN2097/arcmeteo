import arcpy
import os, sys
from arcgis.gis import GIS
import time
from datetime import datetime


pyName = "arcmeteo-time-v1.4.py"
baseDir = r'D:\arcgis\projects\arcmeteo-v1.4'
baseDir = r'D:\arcgis\projects\colombiana'

logformat = "%Y-%m-%d %H:%M:%S"
print("Started {} at {}".format(pyName, datetime.now().strftime(logformat)))

#--
#-- Inputs
#--
netcdf = r'D:\data\gfs\iberiav2.nc'
netcdf = r'D:\data\twp\gfs\20200526\00\bas-colombia-stat.nc'
lstVar = ['temp',"tp","rh"]
lstVar = ['t2mavg','tpacc','r2avg']
lstVar = ['t2mavg','t2mmin', 't2mmax','tpacc','pratemax','wsmax','r2avg']
#- lstVarAlias = ['Temperatura','Precipitación','Humedad Relativa']
vlyZonas = baseDir +r"\ComarcasAgrarias.gdb\ComarcasAgrarias"
clave = "CO_COMARCA"
vlyZonas = baseDir +r"\colombiana.gdb\municipios"
clave = "ADM2_PCODE"

#--
#-- Outputs
#--
filegdb = "time.gdb"
vlyOutput =  baseDir + "/"+filegdb +r"\vlyTime"


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
multidim_raster_layer = baseDir + "/"+ filegdb +r"\multicrf"
zone_stats_table = baseDir + "/"+ filegdb +r"\tblStats"
zone_copy_layer = baseDir + "/"+filegdb+ "/vlyZonasCopy"


#-- (Re)create outfilegdb
print('Recreating output filegdb {}...'.format(filegdb), end='')
if arcpy.Exists(baseDir +"\\"+filegdb):
    arcpy.management.Delete(filegdb)    
arcpy.management.CreateFileGDB(baseDir, filegdb)
print ("ok!")


####################################################

print('MakeMultidimensionalRasterLayer()...', end='')
arcpy.md.MakeMultidimensionalRasterLayer (netcdf, multidim_raster_layer, lstVar, "ALL")
print("ok!")

print('ZonalStatisticsAsTable()..', end='')
arcpy.sa.ZonalStatisticsAsTable(vlyZonas, clave, multidim_raster_layer, zone_stats_table, "DATA", "MEAN", "ALL_SLICES")
print("ok!")

print('PivotTable()..', end='')
in_table = zone_stats_table
fields = clave + ";" + "StdTime"
pivot_field = "Variable"
value_field = "MEAN"
pivot_table = zone_stats_table + "_pivot"
arcpy.management.PivotTable (in_table, fields, pivot_field, value_field, pivot_table) 
print("ok!")


print('MakeQueryTable()...', end='')
# para hacer el join multiple las capas y tablas deben estar en la misma filegdb
arcpy.management.CopyFeatures (vlyZonas, zone_copy_layer)
# join multiple, la salida es en memoria
#arcpy.management.MakeQueryTable(vlyZonasCopy+";"+tblStats, "vlyTime-in-memory" , "USE_KEY_FIELDS", None, None, "vlyZonasCopy.CO_COMARCA = tblStats.CO_COMARCA")
input_tables = zone_copy_layer+";"+pivot_table
sql_clause = zone_copy_layer + "." + clave + " = " + pivot_table + "." + clave
print ( "sql_clause = {}  ".format(sql_clause), end='')
sql_clause = "vlyZonasCopy.ADM2_PCODE = tblStats_pivot.ADM2_PCODE"

arcpy.management.MakeQueryTable(input_tables,  "QueryTable" , "NO_KEY_FIELD", None,  None,  sql_clause)
arcpy.management.CopyFeatures ("QueryTable", vlyOutput)
print("ok!")


####################################################
print ("Publishing to ArcGIS Online...")

# credenciales de ArcGIS Online
sdfName = "vlyTime"
portal = "http://www.arcgis.com" 
user = "twp001"
user = "twp002"
password = "mierda00mierda"

# Set sharing options
shrOrg = True
shrEveryone = True
shrGroups = ""

aprx = baseDir+ "/arcmeteo-v1.2.aprx"
aprx = baseDir+ "/colombiana.aprx"

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
