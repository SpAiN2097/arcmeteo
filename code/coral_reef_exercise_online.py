import sys, os, tempfile, json, logging, arcpy, fnmatch, shutil, subprocess, arcgis
from arcgis.gis import GIS
import datetime as dt
from urllib import request
from urllib.error import URLError

def feedRoutine (url, workGDB, itemid, original_sd_file, service_name):
    # Log file
    logging.basicConfig(filename="coral_reef_exercise.log", level=logging.INFO)
    log_format = "%Y-%m-%d %H:%M:%S"
    
    # Create workGDB and default workspace
    print("Starting workGDB...")
    logging.info("Starting workGDB... {0}".format(dt.datetime.now().strftime(log_format)))
    arcpy.env.workspace = workGDB
    if arcpy.Exists(arcpy.env.workspace):
        for feat in arcpy.ListFeatureClasses ("alert_*"):   
            arcpy.management.Delete(feat)
    else:
        arcpy.management.CreateFileGDB(os.path.dirname(workGDB), os.path.basename(workGDB))
    
    # Download and split json file
    print("Downloading data...")
    logging.info("Downloading data... {0}".format(dt.datetime.now().strftime(log_format)))
    temp_dir = tempfile.mkdtemp()
    filename = os.path.join(temp_dir, 'latest_data.json')
    try:
        response = request.urlretrieve(url, filename)
    except URLError:
        logging.exception("Failed on: request.urlretrieve(url, filename) {0}".format(dt.datetime.now().strftime(log_format)))
        raise Exception("{0} not available. Check internet connection or url address".format(url))
    with open(filename) as json_file:
        data_raw = json.load(json_file)
        data_stations = dict(type=data_raw['type'], features=[])
        data_areas = dict(type=data_raw['type'], features=[])
    for feat in data_raw['features']:
        if feat['geometry']['type'] == 'Point':
            data_stations['features'].append(feat)
        else:
            data_areas['features'].append(feat)
    
    # Filenames of temp json files
    stations_json_path = os.path.join(temp_dir, 'points.json')
    areas_json_path = os.path.join(temp_dir, 'polygons.json')
    
    # Save dictionaries into json files
    with open(stations_json_path, 'w') as point_json_file:
        json.dump(data_stations, point_json_file, indent=4)
    with open(areas_json_path, 'w') as poly_json_file:
        json.dump(data_areas, poly_json_file, indent=4)
    
    # Convert json files to features
    print("Creating feature classes...")
    logging.info("Creating feature classes... {0}".format(dt.datetime.now().strftime(log_format)))
    arcpy.conversion.JSONToFeatures(stations_json_path, 'alert_stations') 
    arcpy.conversion.JSONToFeatures(areas_json_path, 'alert_areas')
    
    # Add 'alert_level ' field
    arcpy.management.AddField('alert_stations', 'alert_level', 'SHORT', field_alias='Alert Level')
    arcpy.management.AddField('alert_areas', 'alert_level', 'SHORT', field_alias='Alert Level')
    
    # Calculate 'alert_level ' field
    arcpy.management.CalculateField('alert_stations', 'alert_level', "int(!alert!)")
    arcpy.management.CalculateField('alert_areas', 'alert_level', "int(!alert!)")
    
    # Deployment Logic
    print("Deploying...")
    logging.info("Deploying... {0}".format(dt.datetime.now().strftime(log_format)))
    deployLogic(workGDB, itemid, original_sd_file, service_name)
    
    # Close Log File
    logging.shutdown()
    
    # Return
    print("Done!")
    logging.info("Done! {0}".format(dt.datetime.now().strftime(log_format)))
    return True
    
    
def deployLogic(workGDB, itemid, original_sd_file, service_name):
    # Get item from ArcGIS Online
    gis = GIS(url='https://arcgis.com', username='theweatherpartner', password='mierda00mierda')
    item = gis.content.get(itemid)
    sd_file_name = os.path.basename(original_sd_file)
    if sd_file_name != item.related_items("Service2Data")[0].name:
        raise Exception('Erroneous itemid, service name, or original sd file'.format(itemid))
    # Unpack original_sd_file using 7-zip
    path_7z = fnmatch.filter(os.environ['path'].split(';'), '*7-Zip')
    temp_dir = tempfile.mkdtemp()
    if len(path_7z):
        exe_7z = os.path.join(path_7z[0], '7z.exe')
        call_unzip = '{0} x {1} -o{2}'.format(exe_7z, original_sd_file, temp_dir)
    else:
        raise Exception('7-Zip could not be found in the PATH environment variable')
    subprocess.call(call_unzip)
    # Replace Live.gdb content
    liveGDB = os.path.join(temp_dir, 'p20', 'live.gdb')
    shutil.rmtree(liveGDB)
    os.mkdir(liveGDB)
    for root, dirs, files in os.walk(workGDB):
        files = [f for f in files if '.lock' not in f]
        for f in files:
            shutil.copy2(os.path.join(workGDB, f), os.path.join(liveGDB, f))
    # Zip file
    os.chdir(temp_dir)
    updated_sd = os.path.join(temp_dir, sd_file_name)
    call_zip = '{0} a {1} -m1=LZMA'.format(exe_7z, updated_sd)
    subprocess.call(call_zip)
    # Replace file
    manager = arcgis.features.FeatureLayerCollection.fromitem(item).manager
    status = manager.overwrite(updated_sd)
    # Return
    return True
    
if __name__ == "__main__":
    [url, workGDB, itemid, original_sd_file, service_name] = sys.argv[1:]
    feedRoutine (url, workGDB, itemid, original_sd_file, service_name)
    
