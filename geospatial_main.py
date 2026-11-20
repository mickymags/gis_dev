from geospatial_utils import geojson_creator, area_estimator, SICD_info,\
                                h5_dump, aoi_intersection, image_clipper,\
                                intensity_display, dem_display, paletted_display
import argparse


def run_geojson_creator(args): 
    geojson_creator(args.outfile, args.xmin, args.ymin, args.xmax, args.ymax)

def run_area_estimator(args): 
    area_estimator(args.geojson)

def run_sicd_info(args): 
    SICD_info(args.input_file)

def run_hdf5_meta(args):
    h5_dump(args.input_file)

def run_intersectioner(args): 
    aoi_intersection(args.input_dir, args.desc)

def run_image_clipper(args):
    image_clipper(args.input_img, args.input_shp, args.dest_path)

def run_intensity_display(args):
    intensity_display(args.intensity_image, args.out_dir, args.polarization)

def run_dem_display(args):
    dem_display(args.dem_path, args.out_dir)

def run_paletted_display(args): 
    paletted_display(args.input_img, args.out_dir)

global_parser = argparse.ArgumentParser(
    prog = 'geospatial_utils', 
    description = 'Geospatial Utilities Using Python', 
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

subparsers = global_parser.add_subparsers(
    title="command", 
    dest = "command",
    required = True,
    help = "geospatial_utils sub-commands"
)

# GeoJSON Creator Subparser
geojson = subparsers.add_parser("geojson_creator", help = "Create a GeoJSON")
geojson.add_argument("--outfile", required = True, help = "absolute path to outfile, must end in .json")
geojson.add_argument("--xmin", type = float, required = True, help = "Minimum Longitude in decimal degrees")
geojson.add_argument("--ymin", type = float, required = True, help = "Minimum Latitude in decimal degrees")
geojson.add_argument("--xmax", type = float, required = True, help = "Maximum Longitude in decimal degrees")
geojson.add_argument("--ymax", type = float, required = True, help = "Maximum Latitude in decimal degrees")
geojson.set_defaults(func = run_geojson_creator)

################### Area Estimator Subparser ##########################
area_estimation = subparsers.add_parser("area_estimator", help = "Estimate the area of a region of interest. Accepts GeoJSONs only")

area_estimation.add_argument("--geojson", required = True, help = "string containing absolute path to geojson file")
area_estimation.set_defaults(func = run_area_estimator)

####################### SICD Metadata Subparser ######################
sicd_subparser = subparsers.add_parser("sicd_metadata", help = "Examine the metadata of a SICD SAR image.")

sicd_subparser.add_argument("--input_file", required = True, help = "string containing absolute path to input SAR image file. Must end in .nitf or .ntf")
sicd_subparser.set_defaults(func = run_sicd_info)


########################## HDF5 Metadata Subparser ##################
hdf5_subparser = subparsers.add_parser("hdf5_metadata", help = "Examine the metadata of an HDF5 SAR image.")

hdf5_subparser.add_argument("--input_file", required = True, help = "string containing absolute path to input SAR image file. Must end in .h5 or .hdf5")
hdf5_subparser.set_defaults(func = run_hdf5_meta)


########################## Intersection Subparser #########################
intersection_subparser = subparsers.add_parser("shp_intersection", help = "Extract the intersection of several Shapefiles.")

intersection_subparser.add_argument("--input_dir", required = True, help = "string containing absolute path to directory containing .shp files. Cannot contain a slash (/).")
intersection_subparser.add_argument("--desc", required = True, help = "string containing description of study area.")


intersection_subparser.set_defaults(func = run_intersectioner)

######################## Image Clipper Subparser ###############################
clipper_subparser = subparsers.add_parser("image_clipper", help = "Clip the image to a shapefile")

clipper_subparser.add_argument("--input_img", required = True, help = "String containing path to input image")
clipper_subparser.add_argument("--input_shp", required = True, help = "String containing path to shapefile.")
clipper_subparser.add_argument("--dest_path", required = True, help = "string containing path to destination.")

clipper_subparser.set_defaults(func = run_image_clipper)

#################### Intensity Display Subparser ################# 
display_subparser = subparsers.add_parser("intensity_display", help = "Display a single band image")
display_subparser.add_argument("--intensity_image", required = True, help = "Intensity Image")
display_subparser.add_argument("--out_dir", required = True, help = 'Output Directory')
display_subparser.add_argument("--polarization", required = True, help = "Polarization")

display_subparser.set_defaults(func = run_intensity_display)


############################# DEM Display subparser ####################
demdis_subparser = subparsers.add_parser("dem_display", help = "Display a single band DEM")

demdis_subparser.add_argument("--dem_path", required = True, help = "string containing absolute path to DEM image")
demdis_subparser.add_argument("--out_dir", required = True, help = "string containing path to output directory.")

# Assign subparser to function
demdis_subparser.set_defaults(func = run_dem_display)

############################ Paletted Display Subparser #########################
paldis_subparser = subparsers.add_parser("cswe_display", help = "Display a binary single-band image with 0 set to gray and 1 set to blue")

paldis_subparser.add_argument("--input_img", required = True, help = "Input binary image")
paldis_subparser.add_argument("--out_dir", required = True, help = "Output Directory")

# Assign subparser to function 
paldis_subparser.set_defaults(func = run_paletted_display)

############## Executor ###########
args = global_parser.parse_args()
args.func(args)

"""
print(f'area_estimator: {area_estimator}')
print(f' type of area estimator: {type(area_estimator)}')
print('\n')
print(f'geojson_creator: {geojson_creator}')
print(f'type geojson creator: {type(geojson_creator)}')

geojson_creator(args.outfile, 
                float(args.xmin), 
                float(args.ymin), 
                float(args.xmax),
                float(args.ymax))
"""

