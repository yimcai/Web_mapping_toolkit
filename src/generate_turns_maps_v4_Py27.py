import getopt
import logging
import os
import sys
import subprocess 
from collections import OrderedDict

import geopandas as gpd
from shapely.geometry import LineString
import pandas as pd
import numpy as np 
import matplotlib.pyplot as plt 

USAGE = """
        Generate GeoJSON files for turn.pen files 

        """

#set up logger
logger = logging.getLogger(__name__)
file_handler = logging.FileHandler("turn.log")
formatter = logging.Formatter("%(asctime)s:%(name)s:%(levelname)s:%(message)s")
logger.addHandler(file_handler)
logger.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)


def readTurnPens(filename):
    """
    Read turn files into dictionary, which is mainly the legacy code.
    
    Exception might throw if the format of the turns file does not follow the pattern:
    starting_node turning_node end_node 1 -1; comments(optional)
    """
    turn_pen = OrderedDict()
    with open(filename, "r") as infile:  
        for line in infile:
            if ";" in line:
                line_parts = line.split(";")
                line = line_parts[0].strip()
                
                comment = line_parts[1]
                comment = comment.strip()
            else:
                line = line.strip()
                comment = "no_details_available"
            turn_parts = line.split(" ")
            while "" in turn_parts:
                turn_parts.remove("")
            try:
                key = (int(turn_parts[0]),
                       int(turn_parts[1]),
                       int(turn_parts[2]),
                       int(turn_parts[3]),
                       int(turn_parts[4]))
#                keys.append(key)
#                values.append(comment)
                turn_pen[key] = comment
            except Exception as e:
                print (e)
                logger.error("{0} encountered '{1}' exception".format(line, e))
                ## do not raise at this time
                raise Exception("turn.pen file not properly loaded, check log file to see which line has problem")
    return turn_pen

def read_shapefile(network_file):
    try:
        network_gdf = gpd.read_file(network_file)
    except Exception as e:
        print (e)
        raise
    else:
        return network_gdf
#%%
def find_link_in_geodataframe(geodataframe ,start_id, end_id, start_field ="A", end_field="B" ):
    """
    find corresponding records in geodataframe, extract geometry, and add "STREETS" and "Comments" to it 
    if sucessfully 
    """
    #indicate whether the line needs to be reversed in point sequence, default is False;
    try:
        link_record = geodataframe[(geodataframe[start_field] == start_id) & (geodataframe[end_field] == end_id)].copy()
        if link_record.shape[0] == 0: # no record on this direction, try another direction 
            link_record = geodataframe[(geodataframe[start_field] == end_id) & (geodataframe[end_field] == start_id)].copy()
            #try to reverse the LineString object to match start and end node id
            if link_record.shape[0] != 0:
                link_record["geometry"] = link_record.apply(lambda x: LineString(x["geometry"].coords[::-1]) , axis =1)
            else:
                raise Exception("No matching records for link({}-{})".format(start_id, end_id))
        #if link_record is not 0, add "TYPE" value to Street name
        if link_record.iloc[0]["TYPE"] : 
            #Street name is not None
            if link_record.iloc[0]["STREETNAME"]:
                print "Street Name: ", link_record.iloc[0]["STREETNAME"]
                link_record["STREETS"] = link_record.iloc[0]["STREETNAME"] + "_" + link_record.iloc[0]["TYPE"]
            else:
                link_record["STREETS"] = "Street_Unknown"
        else:
            link_record["STREETS"] = link_record.iloc[0]["STREETNAME"]
        kept_fields = ["STREETS", "geometry"]
        link_record = link_record[kept_fields] 
    # try fails, not corresponding record
    except Exception:
        return gpd.GeoDataFrame()
        # raise
    #if no exception happens
    else:
        return link_record
#%%
def linestring_adjust(line1, line2, distance = 0.95, normalized = True):
    # Used to combine two lineString objects, whose sequence are: from line1 --> line2
       
    l1_head, l1_tail = list(line1.coords)[0], list(line1.coords)[-1]
    l2_head, l2_tail = list(line2.coords)[0], list(line2.coords)[-1]
    if l2_head == l1_tail:
        if len(line1.coords[:]) >= 3:        
            original_sequence = line1.coords[:-1] + line2.coords[1:]
        else:
            line1_turn_pt = line1.interpolate(distance, normalized = normalized)
            line2_turn_pt = line2.interpolate(1-distance, normalized = normalized)
            original_sequence = [line1.coords[0], line1_turn_pt.coords[0], line2_turn_pt.coords[0], line2.coords[-1]]
        reversed_sequece = original_sequence[::-1]
        return LineString(original_sequence)
    else:
        return None

def combine_AB_BC(link_ab, link_bc, index):
    """
    combine geometry into a single linestring and add an field named "Intersect" with two streets's names 
    """
    street_AB = link_ab.iloc[0]["STREETS"]
    geo_AB = link_ab.iloc[0]["geometry"]
    #street BC
    street_BC = link_bc.iloc[0]["STREETS"]
    geo_BC = link_bc.iloc[0]["geometry"]
    #combine AB-BC to ABC
    geo_ABC = linestring_adjust(geo_AB, geo_BC)
    data = {"STREET_AB":[street_AB], "STREET_BC": [street_BC], 
            "Intersect": ["{0}_&_{1}".format(street_AB, street_BC)], 
            "Restriction":["No_Turn_from {0} to {1}".format(street_AB, street_BC)],
            "geometry": [geo_ABC], 
            "id": [index]
            }
    gdf = gpd.GeoDataFrame(data)
    return gdf 
#%%
def createFeatureClass(network_gdf, turn_key, i):
    """
    network_shapefile: the network Shapefile which have node information and geometry details
    turn_record, (t1,t2,t3, 1 ,-1),(comments)
    """
    #find A-B link
    logger.debug("A start: {} B end: {}".format(turn_key[0], turn_key[1]))
    link_AB = find_link_in_geodataframe(network_gdf, turn_key[0], turn_key[1], "A", "B")
    #find B-C link 
    logger.debug("B start: {} C end: {}".format(turn_key[1], turn_key[2]))
    link_BC = find_link_in_geodataframe(network_gdf, turn_key[1], turn_key[2], "A", "B")
    #process two segments only if two segments have records 
    if not link_AB.empty and not link_BC.empty :
        link_ABC = combine_AB_BC(link_AB, link_BC, i)
    else:
        logger.warning("cannot find all geometry for turn {}".format(turn_key))
        link_ABC = gpd.GeoDataFrame()
    return link_ABC 
#%%
def offset_turn(turn_gdf):
    def random_distance():
        return np.random.choice([1, 8, 16 ,20])
    turn_gdf["geometry"] = turn_gdf.apply(lambda x: x["geometry"].parallel_offset(random_distance(), "left"),  axis =1)
    return turn_gdf
#%%
def generate_maps(base_network, overlaid_layers, output_dir, map_name, title):
    fig, ax_map = plt.subplots(1, 1, dpi = 100, figsize = (12, 10))
    base_network.plot(ax = ax_map, linewidth = 0.1, color = "lightgrey")
    overlaid_layers.plot(ax = ax_map, linewidth = 0.25, color = "red")
    end_points = overlaid_layers.apply(lambda x: x["geometry"].coords[-1], axis = 1)
    x_ends, y_ends = zip(*end_points)
    ax_map.scatter(x_ends, y_ends, s= 5, color = "orange")
    min_x, max_x = overlaid_layers.bounds.minx.min(), overlaid_layers.bounds.maxx.max()
    x_diff= max_x - min_x
    min_y, max_y = overlaid_layers.bounds.miny.min(), overlaid_layers.bounds.maxy.max()
    y_diff = max_y - min_y
    x_lim =  (min_x - x_diff*0.1 , max_x + x_diff *0.1)
    y_lim =  (min_y - y_diff*0.1 , max_y + y_diff *0.1)
    # print (x_lim, y_lim)
    plt.axis("equal")
    ax_map.set_xlim(*x_lim)
    ax_map.set_ylim(*y_lim)
    ax_map.set_title(title)
    #save map
    output_path = os.path.join(output_dir, map_name)
    fig.savefig(output_path + ".png", format = "png")
    logger.debug("Sucessfully generate {} map".format(title))
    return fig 
#%%
def main():
    #might add mapping as an option
    opts, remainders = getopt.getopt(sys.argv[1:], "",["working_dir=", "turnfile="])
    # opts, remainders = getopt.getopt(["--working_dir", "Y:\champ\util\pythonlib-migration\dev\generate_turns_maps\MTA_updates", 
    #                                     "--turnfile", "turnspm.pen"], "",["working_dir=", "turnfile="])
    for opt, arg in opts:
        # print (opt, arg)
        if opt in ("--working_dir"):
            working_dir  = arg
        elif opt in ("--turnfile"):
            turn_file = arg
    map_dir = "TURN_MAPS"
    network_shp = "FREEFLOW.shp"
    network_outshp_dir = "OUTPUT_SHP"
    if not os.path.isdir(network_outshp_dir):
        os.mkdir(network_outshp_dir)
    if "am" in turn_file:
        timeclass= "AM"
    elif "pm" in turn_file:
        timeclass = "PM"
    else:
        timeclass = "OP"
    network_outshp_name = timeclass + "_SHP.shp"
    network_prjoutshp_name = network_outshp_name.split(".")[0] + "_PRJ.shp" 
    network_outgjson_name = timeclass + ".geojson"
    network_outshp_file = os.path.join(network_outshp_dir, network_outshp_name)
    network_prjoutshp_file = os.path.join(network_outshp_dir, network_prjoutshp_name)
    abs_map_dir = os.path.join(working_dir, map_dir)
    abs_shapefile_dir = os.path.join(working_dir, network_outshp_file)
    abs_prjshapfile_dir = os.path.join(working_dir, network_prjoutshp_file)
    if not os.path.isdir(abs_map_dir):
        os.mkdir(abs_map_dir)
    network_gdf = read_shapefile(network_shp)
    turn_dict = readTurnPens(turn_file)
    data_store = []
    i = 0
    for key, _ in turn_dict.items():
        i += 1
        gdf_each_pen = createFeatureClass(network_gdf, key, i)
        if not gdf_each_pen.empty:
            data_store.append(gdf_each_pen)
    #construct GeodataFrame from data stored in list         
    turns_gdf = gpd.GeoDataFrame(pd.concat(data_store)).set_index("id")
    #set a random offset 
    turns_gdf = offset_turn(turns_gdf)
    turns_gdf.to_file(network_outshp_file)
    #generate maps 
    generate_maps(network_gdf, turns_gdf, abs_map_dir , timeclass , timeclass + " TURN RESTRICTION")
    subprocess.call(["ogr2ogr", "-a_srs", "EPSG:102643" , abs_prjshapfile_dir, abs_shapefile_dir], shell = True)
    # subprocess.call(["ogr2ogr --help-general"], shell = True)
    crs = {"init":"epsg:4326"}
    try:
        # print working_dir
        # print abs_prjshapfile_dir
        gdf = gpd.read_file(abs_prjshapfile_dir)
        # print (gdf.crs)
        #project to wgs 84
        gdf = gdf.to_crs(crs)
    except Exception as e:
        print (e)
    else:
        gdf.to_file(network_outgjson_name, driver = "GeoJSON")
#%%
if __name__ == "__main__":
    sys.exit(main())
    
