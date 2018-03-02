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

#create an folium map object 
class Web_map(object):
    """Currently, tiles  can also be customized. """
    def __init__(self, map_name,
                        lat, lng,
                        zoom_start):
        super(Web_map, self).__init__()
        self.map_name = map_name
        self.Map = folium.Map(location = [lat, lng], zoom_start = zoom_start)

    def save_map(self, output_dir, map_name):
        output_path = os.path.join(output_dir, map_name)
        self.Map.save(output_path)

    def add_marker(self, ):
        pass

    def add_geometry(self,): 
        pass

    def add_popup(self, ): 






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
    first_map.save_map(output_dir, map_name)


    # first_map.save_map()          
if __name__ == "__main__":
    sys.exit(main())