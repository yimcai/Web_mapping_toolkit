import os
import sys 

import folium
import geopandas as gpd 

USAGE ="""
        Read shapefile or other file formats compatible with fiona.supported_drivers into GeoDataFrame. 
        Folium will handle everything related to web mapping via playing around leaflet.js on the background.
        The output will be html files that can be hosted on Github pages
        """

#read files into geodataframe 
def read_shapefile(network_file):
    try:
        network_gdf = gpd.read_file(network_file)
    except Exception as e:
        print (e)
        raise
    else:
        return network_gdf
#project GeoDataFrame to WGS84 for mapping purpose  
def proj_to_wgs84(gdf):
    crs = {"init":"epsg:4326"}
    gdf = gdf.to_crs(crs)
    return gdf
#convert geodataframe to geojson
def to_geojson(gdf):
    return gdf.to_json()

#create an folium map object 
class Web_map(object):
    """Currently, tiles  can also be customized. """
    def __init__(self, map_name,
                        lat, lng,
                        zoom_start):
        super(Web_map, self).__init__()
        self.map_name = map_name
        self.Map = folium.Map(location = [lat, lng], zoom_start = zoom_start)

    #write folium Map object out to html file
    def save_map(self, output_dir, map_name):
        output_path = os.path.join(output_dir, map_name)
        self.Map.save(output_path)

    #add marker
    def add_marker(self, location, pop_up = None,):
        marker = folium.Marker(location, popup = pop_up)
        marker.add_to(self.Map)

    #add geometry to self.Map
    def add_geometry(self, geojson_data): 
        folium.GeoJson(geojson_data).add_to(self.Map)
    #add interesting popup
    def add_popup(self, ):
        pass

def main():
    #set parameters  
    sf_lat, sf_lng = 37.76, -122.44  
    zoom_start  = 13      
    base_dir = os.path.dirname(os.path.abspath(__file__))
    map_folder = "temp_maps\\"
    output_dir = os.path.join(base_dir, map_folder)
    map_name = "sf_downtown.html"
    #create a map instance
    first_map = Web_map("SF", sf_lat, sf_lng, zoom_start)
    #add marker 
    van_ness = [37.775, -122.419]
    first_map.add_marker( van_ness, pop_up = "a marker")
    # first_map.save_map()       
    first_map.save_map(output_dir, map_name)   
if __name__ == "__main__":
    sys.exit(main())