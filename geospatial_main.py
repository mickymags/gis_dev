from geospatial_utils import geojson_creator
import argparse



global_parser = argparse.ArgumentParser(
    prog = 'geospatial_utils', 
    description = 'Geospatial Utilities Using Python', 
    formatter_class = argparse.ArgumentDefaultsHelpFormatter
)

subparsers = global_parser.add_subparsers(
    title="command", 
    help = "geospatial_utils sub-commands"
)

# GeoJSON Creator Subparser
geojson = subparsers.add_parser("geojson_creator", help = "Create a GeoJSON")
geojson.add_argument("--outfile", required = True, help = "absolute path to outfile, must end in .json")
geojson.add_argument("--xmin", required = True, help = "Minimum Longitude in decimal degrees")
geojson.add_argument("--ymin", required = True, help = "Minimum Latitude in decimal degrees")
geojson.add_argument("--xmax", required = True, help = "Maximum Longitude in decimal degrees")
geojson.add_argument("--ymax", required = True, help = "Maximum Latitude in decimal degrees")

args = global_parser.parse_args()


geojson_creator(args.outfile, 
                float(args.xmin), 
                float(args.ymin), 
                float(args.xmax),
                float(args.ymax))

