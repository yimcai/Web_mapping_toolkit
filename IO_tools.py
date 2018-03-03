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

#do parallel offset for linestrings 
def offset_linestring(geo_dataframe, offset):
    pass

#define projection 
def define_proj(gdf, proj_name):
    gdf.crs = proj_name
    return gdf

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
                        tiles = "https://api.mapbox.com/styles/v1/yimcai92/cjeal4ce31b2q2sp6kig2ahnj/tiles/256/{z}/{x}/{y}?access_token=pk.eyJ1IjoieWltY2FpOTIiLCJhIjoiY2plYWt5Z3Q2MDFyNDJxbzJhYWszYWNpcyJ9.PBOwWRoTa7GETNouo6P-rA"):
        super(Web_map, self).__init__()
        self.map_name = map_name
        self.Map = folium.Map(location = [lat, lng], zoom_start = zoom_start, tiles = tiles, attr = "Mapbox|Dark")

    #write folium Map object out to html file
    def save_map(self, output_dir, map_name):
        output_path = os.path.join(output_dir, map_name)
        self.Map.save(output_path)
    
    #add layer to map
    def add_featuregroup_layer(self, name = None):
        ft_group = folium.FeatureGroup(name = name)
        return ft_group
    def add_layer(self, name = None):
        layer = folium.map.Layer(name = name, overlay = False)
        return layer

    #add marker
    def create_marker(self, location, pop_up = None,):
        marker = folium.Marker(location, popup = pop_up )
        return marker
    
    #add geometry and popups 
    #option 1
    # def add_geometry(self, geojson_data, layer_name, pop_up = None): 
    #     self.Map.add_child(folium.GeoJson(geojson_data, 
    #                     name = layer_name).add_child(folium.Popup(pop_up)))
    #option 2 
    def style_function(self, feature):
        return {
                "color": hex_code_colors() , 
                 "weight" : 3,
        }
    def highlight_function(self, feature):
        return {
                "color" : "red" ,
                "weight" : 4
        }

    def add_geometry(self, geojson_data, layer_name = None, pop_up =None):
        geojson = folium.GeoJson(geojson_data,
                                    style_function = self.style_function,
                                    highlight_function = self.highlight_function, 
                                    name= layer_name)
        if pop_up:
            popup_obj =  folium.Popup(pop_up)
            popup_obj.add_to(geojson)
        return geojson

    #add interesting popup
    def add_popup(self, ):
        pass
    #merge additional child back to self.Map 
    def accept_pull(self, child_obj):
        self.Map.add_child(child_obj)

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
    turn_map = Web_map("SF", sf_lat, sf_lng, zoom_start)
    #add feature group layer for marker 
    marker_layer = turn_map.add_featuregroup_layer(name = "Land Markers")
    #add marker 
    cta = [37.775422, -122.417957]
    civic_center = [37.777948, -122.417817]
    marker1 = turn_map.create_marker( cta, pop_up = "SFCTA")
    marker2 = turn_map.create_marker( civic_center, pop_up = "Civic Center")
    marker1.add_to(marker_layer)
    marker2.add_to(marker_layer)
    turn_map.accept_pull(marker_layer)
    # marker.add_to(turn_map.Map)
    #add geometry stored in geojson 
    # json_path = os.path.join(base_dir, "data_warehouse\Street_Centerlines\StreetCenterlines.geojson")
    # gdf_short = gpd.read_file(json_path).sample(frac = 0.005)

    #add feature group layer for turns 
    turns_layer = turn_map.add_featuregroup_layer(name= "Turn_Restrictions")
    #read shapefile into geodataframe
    # path style varies across platforms
    shp_path = os.path.join(base_dir, "data_warehouse\\turn_am.shp")
    gdf = read_geodata(shp_path)
    #project gdf to wgs84
    gdf_84 = proj_to_wgs84(gdf) 
    #randomly sample a fraction of the geodataframe
    gdf_short = gdf_84.sample(frac = 0.1)
    #loop through gdf_short to access the "Comments", which would be used as popup info
    for i in range(gdf_short.shape[0]):
        gdf_i = gdf_short[i:i+1] 
        comment = gdf_i.iloc[0]["Comments"]
        #adding geojson to existing layer fails
        geom_feature = turn_map.add_geometry(gdf_i.to_json(), pop_up = comment)
        geom_feature.add_to(turns_layer)

    turn_map.accept_pull(turns_layer)
    #add layer control 
    turn_map.add_layer_control()
    # write into html       
    turn_map.save_map(output_dir, map_name)   

if __name__ == "__main__":
    sys.exit(main())





