import os
import random
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
#define projection 
def define_proj(gdf, proj_name):
    gdf.crs = proj_name

#project GeoDataFrame to WGS84 for mapping purpose  
def proj_to_wgs84(gdf):
    crs = {"init":"epsg:4326"}
    gdf = gdf.to_crs(crs)
    return gdf
#SF proj {"init":"epsg:102643"} 

#generate random 
def hex_code_colors():
    a = hex(random.randrange(0, 256))
    b = hex(random.randrange(0, 256))
    c = hex(random.randrange(0, 256))
    a = a[2:]
    b = b[2:]
    c = c[2:]
    if len(a) < 2:
        a = "0" + a
    if len(b) < 2:
        b = "0" + b
    if len(c) < 2:
        c = "0" + c
    z = a+ b + c
    return "#" + z.upper()

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

    #add geometry and popups 
    #option 1
    # def add_geometry(self, geojson_data, layer_name, pop_up = None): 
    #     self.Map.add_child(folium.GeoJson(geojson_data, 
    #                     name = layer_name).add_child(folium.Popup(pop_up)))
    #option 2 
    def highlight_function(self, feature):
        return {
                "color" : "blue" ,
                "weight" : 4
        }

    def add_geometry(self, geojson_data, layer_name, pop_up =None):
        geojson = folium.GeoJson(geojson_data,
                                    style_function = lambda feature:{
                                        "color": hex_code_colors() , 
                                        "weight" : 2,
                                    },
                                    highlight_function = self.highlight_function, 
                                    name= layer_name)
        popup_obj =  folium.Popup(pop_up)
        popup_obj.add_to(geojson)
        geojson.add_to(self.Map)

    #add interesting popup
    def add_popup(self, ):
        pass

    #add layer control 
    def add_layer_control(self):
        folium.LayerControl().add_to(self.Map)

def main():
    #set directory and file name
    #initialization  
    sf_lat, sf_lng = 37.76, -122.44  
    zoom_start  = 13      
    base_dir = os.path.dirname(os.path.abspath(__file__))
    map_folder = "docs"
    output_dir = os.path.join(base_dir, map_folder)
    if not os.path.isdir(output_dir): 
        os.mkdir(output_dir)
    map_name = "turn_restriction.html"

    #create a Web_map instance
    first_map = Web_map("SF", sf_lat, sf_lng, zoom_start)
    #add marker 
    van_ness = [37.775, -122.418]
    first_map.add_marker( van_ness, pop_up = "SFCTA")

    #add geometry stored in geojson 
    # json_path = os.path.join(base_dir, "data_warehouse\Street_Centerlines\StreetCenterlines.geojson")
    # gdf_short = gpd.read_file(json_path).sample(frac = 0.005)

    #read shapefile into geodataframe
    # path style varies across platforms
    shp_path = os.path.join(base_dir, "data_warehouse\\turn_am.shp")
    gdf = read_geodata(shp_path)
    #project gdf to wgs84
    gdf_84 = proj_to_wgs84(gdf) 
    #randomly sample a fraction of the geodataframe
    gdf_short = gdf_84.sample(frac = 1)
    #loop through gdf_short to access the "Comments", which would be used as popup info
    for i in range(gdf_short.shape[0]):
        gdf_i = gdf_short[i:i+1] 
        comment = gdf_i.iloc[0]["Comments"]
        #adding geojson to existing layer fails
        first_map.add_geometry(gdf_i.to_json(), "SF_Street" , pop_up = comment)

    #add layer control 
    first_map.add_layer_control()
    # write into html       
    first_map.save_map(output_dir, map_name)   

if __name__ == "__main__":
    sys.exit(main())





