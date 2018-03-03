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
def read_geodata(geodata):
    try:
        gdf = gpd.read_file(geodata)
    except Exception as e:
        print (e)
        raise
    else:
        return gdf
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
                        zoom_start,
                        tile = 'openstreetmap'):
        super(Web_map, self).__init__()
        self.map_name = map_name
        self.Map = folium.Map(location = [lat, lng], zoom_start = zoom_start, tiles = tile)

    #write folium Map object out to html file
    def save_map(self, output_dir, map_name):
        output_path = os.path.join(output_dir, map_name)
        self.Map.save(output_path)

    #add marker
    def add_marker(self, location, pop_up = None,):
        marker = folium.Marker(location, popup = pop_up)
        marker.add_to(self.Map)

    #add geometry to self.Map
    def add_geometry(self, geojson_data, layer_name, pop_up = None): 
        self.Map.add_child(folium.GeoJson(geojson_data, 
                        name = layer_name).add_child(folium.Popup("Street A & Ave B")))

    #add interesting popup
    def add_popup(self, ):
        pass

    #add layer control 
    def add_layer_control(self):
        folium.LayerControl().add_to(self.Map)

def main():
    #set initial parameters  
    sf_lat, sf_lng = 37.76, -122.44  
    zoom_start  = 13      
    base_dir = os.path.dirname(os.path.abspath(__file__))
    map_folder = "temp_maps"
    output_dir = os.path.join(base_dir, map_folder)
    if not os.path.isdir(output_dir): 
        os.mkdir(output_dir)
    map_name = "sf_downtown.html"

    #create a map instance
    first_map = Web_map("SF", sf_lat, sf_lng, zoom_start)
    #add marker 
    van_ness = [37.775, -122.419]
    first_map.add_marker( van_ness, pop_up = "Van Ness Station")

    #add geometry stored in geojson 
    json_path = os.path.join(base_dir, "data_warehouse/Street_Centerlines/StreetCenterlines.geojson")
    gdf_short = gpd.read_file(json_path).sample(frac = 0.005)
    first_map.add_geometry(gdf_short.to_json(), "SF_Street" )

    #add layer control 
    first_map.add_layer_control()
    # write into html       
    first_map.save_map(output_dir, map_name)   
    print (json_path)

if __name__ == "__main__":
    sys.exit(main())





