import geospatial_utils
import argparse


def main():
    #############################################
    #       Shapefile Creator Parser           #
    ##############################################
    parser = argparse.ArgumentParser(
        description="Shapefile creator"
    )


    parser.add_argument(
        "--xmin",
        help = "Minimum longitude"
    )

    parser.add_argument(
        "--ymin",
        help = "Minimum latitude"
    )

    parser.add_argument(
        "--xmax",
        help = "Maximum longitude"
    )

    parser.add_argument(
        "--ymax",
        help = "Maximum Latitude"
    )

    parser.add_argument(
        "--outfile",
        help = "Shapefile"
    )

    args = parser.parse_args()

    xmin = args.xmin
    xmax = args.xmax 
    ymin = args.ymin
    ymax = args.ymax
    my_out = args.outfile

    print("Hello World_")

    geospatial_utils.shapefile_creator(my_out, xmin, ymin, xmax, ymax)

    #geospatia_l_utils.create_rgb
    return my_out

if __name__ == "__main__":
    main()