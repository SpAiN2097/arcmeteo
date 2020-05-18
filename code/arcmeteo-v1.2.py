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
#lista = ['temp',"tp","rh","tavg","rhavg","tpacc"]
#listaalias = ['Temperatura','Precipitación total','Humedad relativa',"Temperatura media","Humedad relativa media","Precipitación acumulada"]
lista = ['temp',"tp","rh"]
listaalias = ['Temperatura','Precipitación total','Humedad relativa']
listamedia=  ['rhavg',"tavg","tpacc"]
listamediaAlias =  ['Humedad relativa',"Temperatura media","Precipitación acumulada"]


# FGDB con la capa de vlyZonas generalizada (vlyZonas = municipios here)
vlyZonas = base +r"\Municipios.gdb\MuniIberia"
clave = "codMuni"
variable2 = "variable"
transponer = clave+";"+variable2

# FGDB de salida
FGDB = "Salida.gdb"
vlyTime = base + r"/"+FGDB+ "/vlyTime"
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
multicrf =  base + "/"+ FGDB+r"\multicrf"
tblTime = base + "/"+ FGDB+r"\tblTime"
tblStat = base + "/"+ FGDB+r"\tblStat"
salidazonal = FGDB +r"\zonal_vlyZonas"
nombrepivotar = "zonal_pivotar"
salidaPivotTable = base + r"/"+FGDB +r"\tablaPivotTable"
SalidaFinal = base + r"/"+FGDB +r"\MunicipiosMeteo"

# comprueba si existe la FGDB de trabajo
if arcpy.Exists(FGDB):
    arcpy.Delete_management (FGDB)    
arcpy.CreateFileGDB_management(base, FGDB)
print ("creada FGDB")

####################################################
'''
print ("Empezamos el procesado de las variables dependientes del tiempo...")

arcpy.md.MakeMultidimensionalRasterLayer (netcdf, multicrf, lista, "ALL")
arcpy.sa.ZonalStatisticsAsTable(vlyZonas, clave, multicrf, tblTime, "DATA", "MEAN", "ALL_SLICES")
arcpy.PivotTable_management (tblTime, clave+";"+variable2, 'StdTime', 'MEAN',salidaPivotTable)

arcpy.CopyFeatures_management (vlyZonas,vlyTime)
num = 0
for var in lista:
    arcpy.conversion.TableToTable (salidaPivotTable,base+ r"/"+FGDB,nombrepivotar+var, "Variable = '"+var+"'")
    #arcpy.management.MakeTableView(salidaPivotTable, "zonal_pivotar_View"+var, "Variable = '"+var+"'", None)
    fieldList = [f.name for f in arcpy.ListFields(base+ r"/"+FGDB+r"/"+nombrepivotar+var, "*Std*")]
    print (listaalias[num])
    fieldlist2 = []
    for field in fieldList:
            print (field)
            f= field.find("Std")
            dia= field.split("_")[0].replace("StdTime","").zfill(2)
            mes = field.split("_")[1]
            year = field.split("_")[2]
            #hora = field.split("_")[3].zfill(2)
            if len(field) <= 20:
                hora = "00"
            else:
                hora = field.split("_")[3].zfill(2)
            nuevaFecha = (year+"/"+mes+"/"+dia+" "+hora)
            #fecha1 =nuevaFecha
            fieldlist2.append (nuevaFecha)
            #arcpy.AlterField_management(vlyZonas_enriquecida_join,field,  "Tiempo_"+var+"_"+str(num),var+"_"+field[f:])
            arcpy.AlterField_management(base+ r"/"+FGDB+r"/"+nombrepivotar+var,field, "STD_"+var+"_"+str(nuevaFecha),var+"_"+str(nuevaFecha))
            
    fieldListcambio = [f.name for f in arcpy.ListFields(base+ r"/"+FGDB+r"/"+nombrepivotar+var, "*STD*")]
    fieldListorder= sorted(fieldListcambio)
    orden = 0
    for field2 in fieldListorder:
        arcpy.AlterField_management(base+ r"/"+FGDB+r"/"+nombrepivotar+var,field2, "Tiempo_"+var+"_"+str(orden),field2)
        orden = orden+1
    fieldListjoin = [f.name for f in arcpy.ListFields(base+ r"/"+FGDB+r"/"+nombrepivotar+var, "*Tiempo_*")]
    arcpy.management.JoinField(vlyTime, clave, base+ r"/"+FGDB+r"/"+nombrepivotar+var, clave, fieldListjoin)

    num = num+1            

print ("..done!")
'''

####################################################
print ("Empezamos el procesado de las variables independientes del tiempo...")
arcpy.management.CopyFeatures(vlyZonas,vlyStat)
numedia=0
for varmedia in listamedia:
    print(listamediaAlias[numedia])
    arcpy.md.MakeNetCDFRasterLayer(netcdf, str(varmedia) , "lon", "lat", "rly"+varmedia, '', None, "BY_VALUE", "CENTER")
    arcpy.sa.ZonalStatisticsAsTable(vlyZonas, clave, "rly"+str(varmedia), tblStat+"_"+varmedia, "DATA", "MEAN", "CURRENT_SLICE")
    arcpy.management.AlterField(tblStat+"_"+varmedia,"MEAN",str(varmedia) ,str(listamediaAlias[numedia]))
    arcpy.management.JoinField(vlyStat, clave,tblStat+"_"+varmedia, clave, listamedia)
    numedia= numedia+1

print ("..done!")
#-- Aquí tenemos una flamante Feature Layer (capa vectorial) de los municipios con las variables meteorológicas que no dependen del tiempo.

####################################################
'''
print ("Hacemos cosas raras con el tiempo...")
fieldListfinalnombre = [f for f in arcpy.ListFields(vlyTime, "Tiempo_*")]
fieldListfinal = [f.aliasName for f in arcpy.ListFields(vlyTime, "Tiempo_*")]
fieldlist8 = []
numero=0
for fieldfinal in fieldListfinal:
    
    #print (field)
    f= fieldfinal.find("STD")
    year = fieldfinal.split("_")[2]
    mes = fieldfinal.split("_")[3]
    dia= fieldfinal.split("_")[4]
    hora = fieldfinal.split("_")[5].zfill(2)
    nuevaFecha = (fieldfinal.split("_")[0] +" "+fieldfinal.split("_")[1]+" "+year+"/"+mes+"/"+dia+" "+hora)
    #fecha1 =nuevaFecha
    fieldlist8.append (nuevaFecha)
    #arcpy.AlterField_management(vlyZonas_enriquecida_join,field,  "Tiempo_"+var+"_"+str(num),var+"_"+field[f:])
    arcpy.AlterField_management(vlyTime,str(fieldListfinalnombre[numero].name),str(fieldListfinalnombre[numero].name),str(nuevaFecha))
    numero = numero +1
            
arcpy.AddField_management(vlyTime,"FechaTexto","TEXT", None, None, 70, '', "NULLABLE", "NON_REQUIRED", '')

fieldListfecha = [f.aliasName for f in arcpy.ListFields(vlyTime, "Tiempo_temp_0")]
f2= fieldListfecha[0]
fechalimpia = f2.split(" ")[2] +" "+ f2.split(" ")[3] +" horas"
#fecha = str (fieldListfecha [0][f2:])
arcpy.CalculateField_management (vlyTime,"FechaTexto","'"+fechalimpia+"'", "PYTHON3", '', "TEXT")
arcpy.management.JoinField(vlyTime, clave,vlyStat, clave, listamedia)

print ("..done!")
'''


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
relPath = sys.path[0]
sddraft = os.path.join(relPath, "covWeblayer.sddraft")
sd = os.path.join(relPath, "covWeblayer.sd")
sddraft = os.path.join(base, "vlyStat.sddraft")
sd = os.path.join(base, "vlyStat.sd")

# Create a new SDDraft and stage to SD
print("Creating SD file")
arcpy.env.overwriteOutput = True
prj = arcpy.mp.ArcGISProject(aprx)
mp = prj.listMaps()[0]
print("Found ArcGIS Pro Map: "+ str(mp))
arcpy.mp.CreateWebLayerSDDraft(mp, sddraft, sd_fs_name, "MY_HOSTED_SERVICES", "FEATURE_ACCESS",'', True, True)
arcpy.server.StageService(sddraft, sd)

print("Connecting to {}".format(portal))
gis = GIS(portal, user, password)

# Find the SD, update it, publish /w overwrite and set sharing and metadata
print("Search for original SD on portal…")
sdItem = gis.content.search("{} AND owner:{}".format(sd_fs_name, user), item_type="Service Definition")[0]
print("Found SD: {}, ID: {} n Uploading and overwriting…".format(sdItem.title, sdItem.id))
sdItem.update(data=sd)
print("Overwriting existing feature service…")
fs = sdItem.publish(overwrite=True)

if shrOrg or shrEveryone or shrGroups:
    print ("Setting sharing options…")
    fs.share(org=shrOrg, everyone=shrEveryone, groups=shrGroups)

print ("Finished updating: {} – ID: {}".format(fs.title, fs.id))

print (time.strftime("%H:%M:%S"))

