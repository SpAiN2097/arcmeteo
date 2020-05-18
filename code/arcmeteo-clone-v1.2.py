
from arcgis.gis import GIS

'''
#Connect to the origin ArcGIS Online organization
gis1 = GIS("https://arcgis.com", "theweatherpartner")
'''

#Connect to the target ArcGIS Online organization
gis2 = GIS("https://arcgis.com", "twp001", "mierda00mierda")

#Search for and create a list from (a) Hosted Feature Layer(s) in the origin ArcGIS Online account, then display the list
#items = gis2.content.search(query="title:'vlyStat', owner:twp001")
#print("Found SD: {}, ID: {} --> Cloning...".format(items[0].title, items[0].id))
#Clone the items from the origin ArcGIS Online organization to the target organization. Make sure copy_data=true to create a copy of the service in the target organization. 
#gis2.content.clone_items(items, folder='previous', copy_data=True)

#Search for and create a list from (a) Hosted Feature Layer(s) in the origin ArcGIS Online account, then display the list
items = gis2.content.search(query="title:'vlyTime', owner:twp001")
print("Found SD: {}, ID: {} --> Cloning...".format(items[0].title, items[0].id))
#Clone the items from the origin ArcGIS Online organization to the target organization. Make sure copy_data=true to create a copy of the service in the target organization. 
gis2.content.clone_items(items, folder='previous', copy_data=True)

print("Successfully copied the items")
