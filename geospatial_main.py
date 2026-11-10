from geospatial_utils import geojson_creator, area_estimator, SICD_info
import argparse


def run_geojson_creator(args): 
    geojson_creator(args.outfile, args.xmin, args.ymin, args.xmax, args.ymax)

def run_area_estimator(args): 
    area_estimator(args.geojson)

def run_sicd_info(args): 
    SICD_info(args.input_file)


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

