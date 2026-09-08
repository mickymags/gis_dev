import numpy as np  
import argparse 


def lon_radians_to_lon_meters(lat_radians):
    """
    Input: Latitude in Radians 
    Output: Length of 1 degree longitude in meters
    """
    length_of_1_deg_lon_in_meters = 111412.84 * np.cos(lat_radians)\
    - 93.5 * np.cos((3*lat_radians)) + 0.118 * np.cos((5*lat_radians))

    return length_of_1_deg_lon_in_meters
    

def lat_radians_to_lat_meters(lat_radians):
    """
    Input: Latitude in Radians 
    Output: Length of 1 degree latitude in meters
    """
    length_of_1_degree_latitude_in_meters = 111132.92 - 559.82 * np.cos((2 * lat_radians))\
    + 1.175 * np.cos((4 * lat_radians)) - 0.023 * np.cos((6 * lat_radians))

    return length_of_1_degree_latitude_in_meters

def lon_meters_2_degrees(number_of_meters, lon_scaling_factor):
    lon_pixel_spacing_degrees = number_of_meters / lon_scaling_factor
    return lon_pixel_spacing_degrees

def lat_meters_2_degrees(number_of_meters, lat_scaling_factor):
    lat_pixel_spacing_degrees = number_of_meters / lat_scaling_factor 
    return lat_pixel_spacing_degrees

def lon_degrees_2_meters(number_of_degrees, lon_scaling_factor):
    lon_pixel_spacing_meters = number_of_degrees * lon_scaling_factor
    return lon_pixel_spacing_meters

def lat_degrees_2_meters(number_of_degrees, lat_scaling_factor):
    lat_pixel_spacing_meters = number_of_degrees * lat_scaling_factor
    return lat_pixel_spacing_meters


def main():
    parser = argparse.ArgumentParser(
        description = "A script to create a conversion factor to scale 1 degree of longitude or latutide to meters"
    )

    parser.add_argument("--latitude", type = float, help = "input latitude in degrees")

    parser.add_argument("--meters_pixel_spacing", type = float, help = "input pixel resolution in meters")

    parser.add_argument("--degrees_pixel_spacing", type = float, help = "input pixel resolution in degrees")

    args = parser.parse_args() 

    lat_radians = (args.latitude * 2 * np.pi)/360 

    print("Input latitude in radians {0:0.3f}".format(lat_radians))

    lon_length_meters = lon_radians_to_lon_meters(lat_radians)
    lat_length_meters = lat_radians_to_lat_meters(lat_radians)

    print(f"Length of 1 degree of longitude in meters at {args.latitude:0.3f} degree latitude: {lon_length_meters:0.3f}")

    print(f"Length of 1 degree of latitude in meters at {args.latitude:0.3f} degree latitude: {lat_length_meters:0.3f}")


    if type(args.meters_pixel_spacing) == float:
        lon_pixel_spacing_degs = lon_meters_2_degrees(args.meters_pixel_spacing, lon_length_meters)
        lat_pixel_spacing_degs = lat_meters_2_degrees(args.meters_pixel_spacing, lat_length_meters)

        print(f"\n Longitude Pixel Spacing in Degrees: {lon_pixel_spacing_degs:0.25f}")
        print(f"Latitude Pixel Spacing in Degrees: {lat_pixel_spacing_degs: 0.25f}")

    if type(args.degrees_pixel_spacing) == float:
        lon_pixel_spacing_m = lon_degrees_2_meters(args.degrees_pixel_spacing, lon_length_meters)
        lat_pixel_spacing_m = lat_degrees_2_meters(args.degrees_pixel_spacing, lat_length_meters)

        print(f"\n Longitude Pixel Spacing in Meters: {lon_pixel_spacing_m:0.3f}")
        print(f"Latitude Pixel Spacing in Meters: {lat_pixel_spacing_m:0.3f}")
        
if __name__ == "__main__":
    main()