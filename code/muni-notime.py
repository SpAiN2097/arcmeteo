#!/usr/bin/python
# ejecutar cmd como 
# necesitamos Spatial 
# entrada sscc

import arcpy
import os, sys
from arcgis.gis import GIS
import time
import sys
import ftplib
from datetime import datetime
import logging



# CONFIGURAR---------------------------
# configurar espacio de trabajo
base = r'D:\arcgis\projects\COVID-19\TWP\automatizacion'
logdir= os.path.join(base,"_logs")
#Configuracion de log, por si hiciera falta
nombreProyecto = "TWP"
logging.basicConfig(filename=os.path.join(logdir,"{}_{}{}".format(nombreProyecto,datetime.now().strftime("%d%m%Y_%H%M"),'.log')), filemode='w', format='%(asctime)-15s %(name)s - %(levelname)s - %(message)s',level=logging.INFO)


##########################
# netcdf de entrada
netCDFIberia = base+r'\necdfFTP\iberiav2.nc'
netCDFCanarias = base+r'\necdfFTP\canariasv2.nc'
netCDFIberia = r'D:\data\gfs\iberiav2.nc'
netCDFCanarias = r'D:\data\gfs\canariasv2.nc'
#nombre de la variable
#lista = ['temp',"tp","rh","tavg","rhavg","tpacc"]
lista = ['temp',"tp","rh"]
listamedia=  ['rhavg',"tavg","tpacc"]
listamediaAlias =  ['Humedad relativa',"Temperatura media","Precipitación acumulada"]
#listaalias = ['Temperatura','Precipitación total','Humedad relativa',"Temperatura media","Humedad relativa media","Precipitación acumulada"]
listaalias = ['Temperatura','Precipitación total','Humedad relativa']
# FGDB con la capa de sscc generalizada
sscc = base +r"\Municipios\Municipios.gdb\MuniIberia"
ssccCanarias = base +r"\Municipios\Municipios.gdb\MuniCanarias"
clave = "codMuni"
variable2 = "variable"
transponer = clave+";"+variable2
# FGDB de salida
FGDB = "Salida_municipios.gdb"
FGDBcanarias = "Salida_municipios_canarias.gdb"
muniCopy = base + r"/"+FGDB+ "/muni"
muniCopyCanarias = base + r"/"+FGDBcanarias+ "/muniCanarias"
muniCopymedia = base + r"/"+FGDB+ "/munimedia"
muniCopymediaCanarias = base + r"/"+FGDBcanarias+ "/muniCanariasmedia"
muniMerge = base + r"/"+FGDB+ "/muniEspaña"
muniMergeMedia = base + r"/"+FGDB+ "/muniEspanaMedia"

# credenciales de ArcGIS Online
sd_fs_name = "DatosMeteov2"
portal = "http://www.arcgis.com" 
'''
user = "jlnavarro_plataformacovid"
password = "TWP_COVID19_"
'''
user = "theweatherpartner"
password = "mierda00mierda"

# Set sharing options
shrOrg = True
shrEveryone = True
shrGroups = ""
#proyecto de Pro
prjPath = base+ "/TWP.aprx"
#prjPathCanarias = base+ "/TWP_canarias.aprx"
# Fin de configuracion ---------------------------

#######################FTP
########################################################

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
zonal_tabla_media = base + "/"+ FGDB+r"\zonal_tabla_media"
salidazonal = FGDB +r"\zonal_sscc"
salidazonalcanarias = FGDBcanarias +r"\zonal_sscc"
nombrepivotar = "zonal_pivotar"
salidapivotar = base + r"/"+FGDB +r"\zonal_pivotar"
salidapivotarcanarias = base + r"/"+FGDBcanarias +r"\zonal_pivotar"
SalidaFinal = base + r"/"+FGDB +r"\MunicipiosMeteo"
SalidaFinalCanarias = base + r"/"+FGDBcanarias +r"\MunicipiosMeteo"

# comprueba si existe la FGDB de trabajo
if arcpy.Exists(FGDB):
    arcpy.Delete_management (FGDB)    
arcpy.CreateFileGDB_management(base, FGDB)
print ("creada FGDB")

print ("Empezamos el procesado del resto de variables")
####################################################
#restovariables
arcpy.md.MakeMultidimensionalRasterLayer (netCDFIberia, multicrf, lista, "ALL")
arcpy.sa.ZonalStatisticsAsTable(sscc, clave, multicrf, zonal_tabla, "DATA", "MEAN", "ALL_SLICES")

arcpy.PivotTable_management (zonal_tabla, clave+";"+variable2, 'StdTime', 'MEAN',salidapivotar)

arcpy.CopyFeatures_management (sscc,muniCopy)
num = 0
for var in lista:
    arcpy.conversion.TableToTable (salidapivotar,base+ r"/"+FGDB,nombrepivotar+var, "Variable = '"+var+"'")
    #arcpy.management.MakeTableView(salidapivotar, "zonal_pivotar_View"+var, "Variable = '"+var+"'", None)
    fieldList = [f.name for f in arcpy.ListFields(base+ r"/"+FGDB+r"/"+nombrepivotar+var, "*Std*")]
    print (listaalias[num])
    fieldlist2 = []
    for field in fieldList:
            #print (field)
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
            #arcpy.AlterField_management(sscc_enriquecida_join,field,  "Tiempo_"+var+"_"+str(num),var+"_"+field[f:])
            arcpy.AlterField_management(base+ r"/"+FGDB+r"/"+nombrepivotar+var,field, "STD_"+var+"_"+str(nuevaFecha),var+"_"+str(nuevaFecha))
            
    fieldListcambio = [f.name for f in arcpy.ListFields(base+ r"/"+FGDB+r"/"+nombrepivotar+var, "*STD*")]
    fieldListorder= sorted(fieldListcambio)
    orden = 0
    for field2 in fieldListorder:
        arcpy.AlterField_management(base+ r"/"+FGDB+r"/"+nombrepivotar+var,field2, "Tiempo_"+var+"_"+str(orden),field2)
        orden = orden+1
    fieldListjoin = [f.name for f in arcpy.ListFields(base+ r"/"+FGDB+r"/"+nombrepivotar+var, "*Tiempo_*")]
    arcpy.management.JoinField(muniCopy, clave, base+ r"/"+FGDB+r"/"+nombrepivotar+var, clave, fieldListjoin)

    num = num+1            

print ("procesado netCDFIberia")
####################################################
#########Ahora Canarias
if arcpy.Exists(FGDBcanarias):
    arcpy.Delete_management (FGDBcanarias)    
arcpy.CreateFileGDB_management(base, FGDBcanarias)
print ("creada FGDB")
arcpy.md.MakeMultidimensionalRasterLayer (netCDFCanarias, multicrfCanarias, lista, "ALL")
arcpy.sa.ZonalStatisticsAsTable(ssccCanarias, clave, multicrfCanarias, zonal_tablacanarias, "DATA", "MEAN", "ALL_SLICES")

arcpy.PivotTable_management (zonal_tablacanarias, clave+";"+variable2, 'StdTime', 'MEAN',salidapivotarcanarias)

arcpy.CopyFeatures_management (ssccCanarias,muniCopyCanarias)

num = 0
for var in lista:
    arcpy.conversion.TableToTable (salidapivotarcanarias,base+ r"/"+FGDBcanarias,nombrepivotar+var, "Variable = '"+var+"'")
    #arcpy.management.MakeTableView(salidapivotar, "zonal_pivotar_View"+var, "Variable = '"+var+"'", None)
    fieldList1 = [f.name for f in arcpy.ListFields(base+ r"/"+FGDBcanarias+r"/"+nombrepivotar+var, "*Std*")]
    print (listaalias[num])
    fieldlist2 = []
    tiempo =0

    for field1 in fieldList1:
           #print (field)
            f= field1.find("Std")
            dia= field1.split("_")[0].replace("StdTime","").zfill(2)
            mes = field1.split("_")[1]
            year = field1.split("_")[2]
            #hora = field1.split("_")[3].zfill(2)
            if len(field1) <= 20:
                hora = "00"
            else:
                hora = field1.split("_")[3].zfill(2)
            nuevaFecha = (year+"/"+mes+"/"+dia+" "+hora)
            fieldlist2.append (nuevaFecha)
            #arcpy.AlterField_management(sscc_enriquecida_join,field,  "Tiempo_"+var+"_"+str(num),var+"_"+field[f:])
            arcpy.AlterField_management(base+ r"/"+FGDBcanarias+r"/"+nombrepivotar+var,field1, "STD_"+var+"_"+str(nuevaFecha),var+"_"+str(nuevaFecha))
            #arcpy.AlterField_management(base+ r"/"+FGDBcanarias+r"/"+nombrepivotar+var,field,  var+"_"+field[f:],str(listaalias[num])+"_"+field[f:])
            #tiempo = tiempo+1
    fieldListcambiocanarias = [f.name for f in arcpy.ListFields(base+ r"/"+FGDBcanarias+r"/"+nombrepivotar+var, "*STD*")]
    fieldListorder2= sorted(fieldListcambiocanarias)
    orden = 0
    for field3 in fieldListorder2:
        arcpy.AlterField_management(base+ r"/"+FGDBcanarias+r"/"+nombrepivotar+var,field3, "Tiempo_"+var+"_"+str(orden),field3)
        orden = orden+1
    fieldListjoincanarias = [f.name for f in arcpy.ListFields(base+ r"/"+FGDB+r"/"+nombrepivotar+var, "*Tiempo_*")]
    arcpy.management.JoinField(muniCopyCanarias, clave, base+ r"/"+FGDBcanarias+r"/"+nombrepivotar+var, clave, fieldListjoincanarias)

    num = num+1      

print ("procesado netCDFCanarias")

####################################################
#Procesamos la temperatura media
# España
print("Empezando el procesado de las medias")
arcpy.CopyFeatures_management (sscc,muniCopymedia)
numedia=0
for varmedia in listamedia:
    arcpy.md.MakeNetCDFRasterLayer(netCDFIberia, str(varmedia) , "lon", "lat", varmedia+"_Layer", '', None, "BY_VALUE", "CENTER")
    arcpy.sa.ZonalStatisticsAsTable(sscc, clave, str(varmedia)+"_Layer", zonal_tabla_media+"_"+varmedia, "DATA", "MEAN", "CURRENT_SLICE")
    arcpy.AlterField_management(zonal_tabla_media+"_"+varmedia,"MEAN",str(varmedia) ,str(listamediaAlias[numedia]))
    arcpy.management.JoinField(muniCopymedia, clave,zonal_tabla_media+"_"+varmedia, clave, listamedia)
    numedia= numedia+1
#Canarias
arcpy.CopyFeatures_management (ssccCanarias,muniCopymediaCanarias)

numediaCanarias=0
for varmediaCanarias in listamedia:
    arcpy.md.MakeNetCDFRasterLayer(netCDFCanarias, str(varmediaCanarias) , "lon", "lat", varmediaCanarias+"_LayerC", '', None, "BY_VALUE", "CENTER")
    arcpy.sa.ZonalStatisticsAsTable(ssccCanarias, clave, str(varmediaCanarias)+"_LayerC", zonal_tabla_media+"_C_"+varmediaCanarias, "DATA", "MEAN", "CURRENT_SLICE")
    arcpy.AlterField_management(zonal_tabla_media+"_C_"+varmediaCanarias,"MEAN",str(varmediaCanarias) ,str(listamediaAlias[numediaCanarias]))
    arcpy.management.JoinField(muniCopymediaCanarias, clave,zonal_tabla_media+"_C_"+varmediaCanarias, clave, listamedia)
    numediaCanarias= numediaCanarias+1

arcpy.Merge_management (muniCopymedia+";"+muniCopymediaCanarias,muniMergeMedia )
####################################################
#mergeando
arcpy.Merge_management (muniCopy+";"+muniCopyCanarias,muniMerge )

fieldListfinalnombre = [f for f in arcpy.ListFields(muniMerge, "Tiempo_*")]
fieldListfinal = [f.aliasName for f in arcpy.ListFields(muniMerge, "Tiempo_*")]
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
    #arcpy.AlterField_management(sscc_enriquecida_join,field,  "Tiempo_"+var+"_"+str(num),var+"_"+field[f:])
    arcpy.AlterField_management(muniMerge,str(fieldListfinalnombre[numero].name),str(fieldListfinalnombre[numero].name),str(nuevaFecha))
    numero = numero +1
            
arcpy.AddField_management(muniMerge,"FechaTexto","TEXT", None, None, 70, '', "NULLABLE", "NON_REQUIRED", '')

fieldListfecha = [f.aliasName for f in arcpy.ListFields(muniMerge, "Tiempo_temp_0")]
f2= fieldListfecha[0]
fechalimpia = f2.split(" ")[2] +" "+ f2.split(" ")[3] +" horas"
#fecha = str (fieldListfecha [0][f2:])
arcpy.CalculateField_management (muniMerge,"FechaTexto","'"+fechalimpia+"'", "PYTHON3", '', "TEXT")
arcpy.management.JoinField(muniMerge, clave,muniMergeMedia, clave, listamedia)

####################################################
###################################################################
print ("comenzamos publicación")

# Local paths to create temporary content
relPath = sys.path[0]
sddraft = os.path.join(relPath, "WebUpdate.sddraft")
sd = os.path.join(relPath, "WebUpdate.sd")

# Create a new SDDraft and stage to SD
print("Creating SD file")
arcpy.env.overwriteOutput = True
prj = arcpy.mp.ArcGISProject(prjPath)
mp = prj.listMaps()[0]
arcpy.mp.CreateWebLayerSDDraft(mp, sddraft, sd_fs_name, "MY_HOSTED_SERVICES", "FEATURE_ACCESS",'', True, True)
arcpy.StageService_server(sddraft, sd)

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
