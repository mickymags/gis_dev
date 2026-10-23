from skimage.filters import threshold_otsu
from pathlib import Path 
from shapely.geometry import box
import geopandas as gpd
import numpy as np 
import subprocess
import json 
from osgeo import gdal
from sarpy.io.complex.sicd import SICDReader, SICDWriter

def iceye_metadata_extract(input_file, description):
    """ 
    A function that extracts metadata from ICEYE GRD files. 
    

    Parameters
    ---
    input_file = absolute path to input file 
    description = a description of the study area
    """

    opened = gdal.Open(input_file)


    # If the dataset exists, get its metadata. otherwise, return an error to the user and break
    if opened is not None:
        metadata = opened.GetMetadata()
    else: 
        raise FileNotFoundError

    type_opened = type(opened)
    type_metadata = type(metadata)
    keys = metadata.keys()

    range_resolution = metadata["RANGE_RESOLUTION_CENTER"]
    azimuth_resolution = metadata["AZIMUTH_RESOLUTION"]

    start_time = metadata["ACQUISITION_START_UTC"]
    end_time = metadata["ACQUISITION_END_UTC"]

    product_type = metadata["ACQUISITION_MODE"]

    incidence_angle = metadata["INCIDENCE_CENTER"]


    # Construct a dictionary of what we learned to return to the user
    print(f"\nMetadata for {description} ICEYE image")
    out_string = f"Range Resolution: {range_resolution} \n \
                    Azimuth resolution: {azimuth_resolution} \n \
                    Acquisition time: {start_time} \n \
                    Product Type: {product_type} \n \
                    Incidence Angle: {incidence_angle}" 

    print(out_string)

    return out_string


def split_sicd_into_quadrants(input_file, output_dir):
    """
    Split a SICD NITF into four image-space quadrants.

    The output files retain SICD metadata appropriate to each subset.

    Parameters
    ----------
    input_file : str or Path
        Input SICD NITF file.
    output_dir : str or Path
        Directory where the four SICD NITFs will be written.
    """

    input_file = Path(input_file)
    output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Opening SICD:")
    print(f"  {input_file}")

    reader = SICDReader(str(input_file))

    try:
        # ------------------------------------------------------------
        # Get image dimensions
        # ------------------------------------------------------------

        rows, cols = reader.get_data_size_as_tuple()[0]

        print()
        print("Input image:")
        print(f"  Rows:    {rows}")
        print(f"  Columns: {cols}")

        # We expect the Umbra image to be:
        #
        #   26620 rows
        #   41472 columns
        #
        # But don't hard-code those values.

        row_mid = rows // 2
        col_mid = cols // 2

        print()
        print("Split:")
        print(f"  Row midpoint:    {row_mid}")
        print(f"  Column midpoint: {col_mid}")

        # ------------------------------------------------------------
        # Define the four quadrants
        #
        # Bounds are:
        #
        #   rows:    start, stop
        #   columns: start, stop
        # ------------------------------------------------------------

        tiles = {
            "tile_1": {
                "row_bounds": (0, row_mid),
                "col_bounds": (0, col_mid),
            },
            "tile_2": {
                "row_bounds": (0, row_mid),
                "col_bounds": (col_mid, cols),
            },
            "tile_3": {
                "row_bounds": (row_mid, rows),
                "col_bounds": (0, col_mid),
            },
            "tile_4": {
                "row_bounds": (row_mid, rows),
                "col_bounds": (col_mid, cols),
            },
        }

        # Original SICD metadata
        original_sicd = reader.sicd_meta

        print()
        print("Original SICD:")
        print(f"  NumRows: {original_sicd.ImageData.NumRows}")
        print(f"  NumCols: {original_sicd.ImageData.NumCols}")

        # ------------------------------------------------------------
        # Process each quadrant
        # ------------------------------------------------------------

        for tile_name, bounds in tiles.items():

            row_start, row_end = bounds["row_bounds"]
            col_start, col_end = bounds["col_bounds"]

            tile_rows = row_end - row_start
            tile_cols = col_end - col_start

            print()
            print("=" * 70)
            print(f"Processing {tile_name}")
            print("=" * 70)

            print(
                f"Rows: {row_start}:{row_end} "
                f"({tile_rows} rows)"
            )

            print(
                f"Columns: {col_start}:{col_end} "
                f"({tile_cols} columns)"
            )

            # --------------------------------------------------------
            # Create SICD metadata corresponding to this subset.
            #
            # This is the important part.
            #
            # We do NOT simply copy the original SICD and change
            # NumRows/NumCols.
            # --------------------------------------------------------

            subset_sicd, row_shift, col_shift = original_sicd.create_subset_structure(
                row_bounds=(row_start, row_end),
                column_bounds=(col_start, col_end),
            )
            print()
            print("Subset SICD:")
            print(f"  NumRows: {subset_sicd.ImageData.NumRows}")
            print(f"  NumCols: {subset_sicd.ImageData.NumCols}")

            # --------------------------------------------------------
            # Output filename
            # --------------------------------------------------------

            output_file = (
                output_dir /
                f"{input_file.stem}_{tile_name}.nitf"
            )

            print()
            print(f"Writing:")
            print(f"  {output_file}")

            # --------------------------------------------------------
            # Read ONLY this quadrant from the source.
            #
            # This prevents the entire 8 GB source from being loaded
            # into RAM.
            # --------------------------------------------------------

            print("Reading image subset...")

            data = reader.read_chip(
                slice(row_start, row_end),
                slice(col_start, col_end),
                index=0,
                squeeze=False,
            )

            print(f"  Array shape: {data.shape}")
            print(f"  Array dtype: {data.dtype}")
            print(
                f"  Array size: "
                f"{data.nbytes / (1024 ** 3):.2f} GB"
            )

            # --------------------------------------------------------
            # Write the subset as a new SICD NITF.
            # --------------------------------------------------------

            print("Writing SICD...")

            writer = SICDWriter(
                str(output_file),
                subset_sicd,
            )

            try:
                writer.write_chip(
                    data,
                    start_indices=(0, 0),
                )
            finally:
                writer.close()

            # Explicitly release the large NumPy array before moving
            # to the next quadrant.
            del data

            print(f"Finished: {output_file}")

    finally:
        reader.close()

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)
    print(f"Created four SICD files in:")
    print(f"  {output_dir}")

def rtc_merger(input_dir, description, output_nodata_value):
    """
    This function is designed to work with the outputs of a MultiRTC tiled run. 
    Assumes you will have RTC'd .tif files in the input directory. 
    Since MultiRTC writes out rasters with Nans for nodata, we want to convert this data 
    into a nodata value specified by the user. We will then merge the tiles together

    Parameters 
    ---------------
    input_dir: str 
        Directory containing input GeoTiffs

    description: str 
        Description used to construct the output filename

    Returns 
    ----------
    Path 
        Path to the output merged raster
    """


def constrained_otsu_thresholding(lower_bound, array):
    db_array = 10*np.log10(array)
    modded_array = db_array[db_array > lower_bound]
    otsu_thresh = threshold_otsu(modded_array)

    return otsu_thresh

def shapefile_creator(outfile, xmin, ymin, xmax, ymax):
    """
    outfile must end in .shp. 
    xmin = longitude_minimum
    ymin = latitude_minimum
    xmax = longitude_maximum 
    ymax = latitude_maximum
    """
    bbox = box(xmin, ymin, xmax, ymax)

    # Put it into a pandas dataframe
    gdf = gpd.GeoDataFrame(
        {"id": [1]},
        geometry=[bbox],
        crs = 'EPSG:4326'
    )

    # Write shapefile 
    gdf.to_file(outfile)

    print(f"Shapefile written to {outfile}")

    return 0

def geojson_creator(outfile, xmin, ymin, xmax, ymax) -> None: 
    """
    outfile must end in .json
    xmin = longitude_minimum
    ymin = latitude_minimum 
    xmax = longitude_maxmum, 
    ymax = latitude_maximum
    """

    bbox = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature", 
            "properties": {"name": "bbox"},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[
                    [xmin, ymin], 
                    [xmax, ymin], 
                    [xmax, ymax], 
                    [xmin, ymax], 
                    [xmin, ymin]
                ]],
            },
        }],
    }

    with open(outfile, "w") as f: 
        json.dump(bbox, f, indent = 2)

    print(f"Geojson file is written to {outfile}")

def simple_merge(
        input_dir: list[Path],
        output_file: Path, 
        nodata: float | None = None,
    ) -> None:
    """
    A simple gdal_merge.py command that reads files from an input directory, 
    merges them in their native projection, taking a no data value as an inpiut
    """

    #### Step 1: Find input Directory and get files within it 
    output_filename = output_file
    path_dir = Path(input_dir)

    #input_files = list(path_dir.glob("*.tif"))
    input_files = [
        tif for tif in path_dir.glob("*.tif")
        if tif.name != Path(output_filename).name
    ]

    # If there are no input files, throw an error
    if not input_files: 
        raise FileNotFoundError(f"No .tif files found in {input_dir}")


    merge_command = [
        "gdal_merge.py",
        "-o",
        str(output_file),
    ]

    # Only add Nodata arguments if a value was provided by the user 
    if nodata is not None: 
        merge_command.extend([
            "-n",
            str(nodata),
            "-a_nodata",
            str(nodata),
        ])

    # Add input files 
    merge_command.extend(
        str(tif) for tif in input_files
    )

    print(merge_command)

    subprocess.run(merge_command, check = True)
    
    """
        str(nodata),
        "-a_nodata",
        str(nodata),
        "-o",
        str(output_filename),
        *[str(tif) for tif in input_files], #use list comprehension to unpack the list
    ]
    """

    print(f"Executing merge_command: {merge_command}")

    subprocess.run(merge_command, check=True)

    return_string = f"Writing .tif files located within {input_dir} to the following file: {output_filename}"
    print(return_string)

    return return_string 

def create_rgb(input_dir, desc):
    """
    Designed for use with HLS files downloaded from NASA Earthdata
    Create RGB .vrt file from input files. 
    R file must end in B04.tif 
    G file must end in B03.tif
    B file must end in B02.tif 
    """
    input_dir = Path(input_dir)
    output_vrt = input_dir / f"rgb_{desc}.vrt"

    red = next(input_dir.glob("*B04*.tif"))
    green = next(input_dir.glob("*B03*.tif"))
    blue = next(input_dir.glob("*B02*.tif"))

    # Build RGB VRT
    subprocess.run([
        "gdalbuildvrt",
        "-separate",
        "-input_file_list",
        "/dev/stdin",
        str(output_vrt),
    ], input=f"{red}\n{green}\n{blue}\n", text=True, check=True)

    print(f"Created: {output_vrt}")

    return 0

def water_map_from_thresh(template_img, input_array, threshold, output_file):

    shape = np.shape(input_array)

    ones = np.ones(shape)
    zeros = np.zeros(shape)
    new_array = np.where(input_array > threshold, zeros, ones) 

    print(shape)
    print(np.shape(new_array))
    print(new_array[1000][1000:1200])
    print(np.nanmean(new_array))

    binary_water_map = create_singleband_from_template(template_img, new_array,output_file )

    return binary_water_map

def convert_pow2db(intensity):
    """
    Convert power to decibels 

    Parameters 
    ------------
    intensity: numpy.ndarray intensity or power values
    """
    return 10 * np.log10(intensity)

def create_singleband_from_template(template_image, input_array, output_file):
    """ 
    A function to copy the image metadata from an input image, and write the data in an array into a copy of that image

    Parameters 
    ------------
    template_image: 
        type: str 
        path to .tif file
    input_array:
        type: array 
    output_file: 
        type: str 
        path to output file
    """

    # Open template 
    template = gdal.Open(template_image)

    # Get Geotiff Driver
    driver = gdal.GetDriverByName('GTiff')

    # Create new raster 
    output_driver = driver.Create(output_file, 
                      t.RasterXSize, 
                      t.RasterYSize, 
                      1, 
                      gdal.GDT_Float32,
                      options=["COMPRESS=LZW"]
    )

    # Get projection and geotransform from input image, and apply to output image
    output_driver.SetProjection(template.GetProjection())
    output_driver.SetGeoTransform(template.GetGeoTransform())

    # Copy Metadata
    output_driver.SetMetadata(template.GetMetadata())

    src_band = template.GetRasterBand(1)
    out_band = template.GetRasterBand(1)

    out_band.SetMetadata(src_band.GetMetadata())
    out_band.SetNoDataValue(src_band.GetNoDataValue())

    output_img = out_band.WriteArray(input_array)

    output_driver.FlushCache()
    out = None 
    template = None

    return output_img