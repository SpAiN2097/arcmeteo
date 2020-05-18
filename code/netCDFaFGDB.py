import arcpy
import os
arcpy.env.overwriteOutput = True

arcpy.env.workspace = r'C:\Proyecto\DatosMeteo'
FGDB = "Salida.gdb"
netCDF = 'catd03-t2.nc'
variable = "T_2m"

# comprueba si existe
if not arcpy.Exists(FGDB):
    arcpy.CreateFileGDB_management(arcpy.env.workspace, FGDB)
    print ("creada FGDB")


#variable = "wd_10m"
# tiempo 0
i="0"
netCDFtiempo =variable+"_Layer_"+i
tablatiempo = FGDB +"\\"+variable+"_Layer_"+i
campotiempo=variable+i
arcpy.md.MakeNetCDFFeatureLayer( netCDF, variable, "lon", "lat", netCDFtiempo, "west_east;south_north", '', '', "time "+i, "BY_INDEX")
arcpy.conversion.FeatureClassToFeatureClass(netCDFtiempo, FGDB, netCDFtiempo)
#campo clave
arcpy.management.AddField(tablatiempo, "clave", 'TEXT',"","","50")
arcpy.management.CalculateField(tablatiempo, "clave", 'str (!west_east!)+"/" +str (!south_north!)', "PYTHON3", '')
# Pendiente, hay que incorporar la fecha inicial
arcpy.management.AddField(tablatiempo, campotiempo, "DOUBLE", None, None, None, '', "NULLABLE", "NON_REQUIRED", '')
arcpy.management.CalculateField(tablatiempo, campotiempo, "!"+variable+"!", "PYTHON3", '')
arcpy.management.DeleteField(tablatiempo, variable)

i=1
while i < 48:
    print (i)
    arcpy.md.MakeNetCDFTableView(netCDF, variable, "tabla_"+str(i), "west_east;south_north", "time "+str(i), "BY_INDEX")
    arcpy.conversion.TableToTable("tabla_"+str(i), FGDB, "tabla_"+str(i))
    arcpy.management.AddField(FGDB+"\\tabla_"+str(i), "clave", 'TEXT',"","","50")
    arcpy.management.CalculateField(FGDB+"\\tabla_"+str(i), "clave", 'str (!west_east!)+"/" +str (!south_north!)', "PYTHON3", '')
    arcpy.management.JoinField(tablatiempo, "clave", FGDB+"\\tabla_"+str(i), "clave", variable)
    arcpy.management.AlterField(tablatiempo, variable, variable+str(i), variable +"Hora +"+str(i))
    i += 1

print ("se acabo")