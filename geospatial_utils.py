from skimage.filters import threshold_otsu
from pathlib import Path 
from shapely.geometry import box
import geopandas as gpd
import rasterio
from rasterio.mask import mask 
import numpy as np 
import subprocess
import json 
from osgeo import gdal
from sarpy.io.complex.sicd import SICDReader, SICDWriter
from sarpy.io.complex.converter import open_complex
import h5py
from functools import reduce
import matplotlib.pyplot as plt
import os
from matplotlib.colors import ListedColormap 
from matplotlib.patches import Patch

def aoi_intersection(input_dir, desc) -> None: 
    """
    This function will return the intersection of area of interests for several input shapefiles in an input directory. 
    Returns nothing.

    Parameters 
    ---
    input_dir : str 
        - string containing the absolute path to the input directory containing shapefiles. Must end in a slash.
    desc : str 
        - string containing the absolute path to the input directory containing descriptions. 
    """

    input_path = Path(input_dir)
    shapefiles = []
    crss = []

    for j in input_path.iterdir(): 
        #print(type(j))
        k = str(j) 
        i = k[-4:]
        if i == '.shp':
            #print(k)
            #print(type(k))
            gdf = gpd.read_file(k)
            crs = gdf.crs 
            gdf_4326 = gdf if gdf.crs == "EPSG:4326" else gdf.to_crs("EPSG:4326")
            crs_4326 = gdf_4326.crs
            crss.append(crs_4326)
            shapefiles.append(gdf_4326[["geometry"]])

    #my_type = type(shapefiles)
    unique_crs = []
    for m in crss: 
        if m not in unique_crs:
            unique_crs.append(m)

    for g in unique_crs:
        print(g)

    if len(unique_crs) >1:
        raise ValueError("Shapefiles must have matching CRS!")

    common_intersection = reduce(
        lambda left, right: gpd.overlay(left, right, how="intersection"), shapefiles
    )
    output_name = input_dir + desc + "_intersection.shp"
    common_intersection.to_file(output_name)
    print(f"Intersection shapefile written to {output_name}")

    return 0

def image_clipper(input_img, input_shp, dst_path, nodata=None):
    """
    This function will take an input image (in .tif format) and an input Area of Interest (in .shp format)
    and will output a clipped image in .tif format. 

    Parameters 
    ---
    input_img : str 
        - str containing the absolute path to an input image. Must end in .tif 
    input_shp : str 
        - str containing the absolute path to an input shapefile. 
          Must end in .shp and be associated with sidecar files (.dbf, .shp, .shx, etc.)
    dst_path : str 
        - String containing the absolute path to the output .tif file, mut end in .tif.

    Returns the path to the output image
    """

    gdf = gpd.read_file (input_shp)

    with rasterio.open(input_img) as src: 
        gdf = gdf.to_crs(src.crs) 
        nodata = nodata if nodata is not None else src.nodata
    
        if nodata is None: 
            nodata = 0
            
        data, transform = mask(
            src, 
            gdf.geometry, 
            crop = True, 
            nodata = nodata, 
            all_touched = False
        ) 

        profile = src.profile.copy() 
        profile.update(
            height = data.shape[1], 
            width = data.shape[2], 
            transform = transform, 
            nodata = nodata
        )

    with rasterio.open(dst_path, 'w', **profile) as dst: 
        dst.write(data)

    print(f"Clipped Image written to {dst_path}")
    return dst_path
   
############### BEGIN CODE USED FROM DSWX-SAR REPOSITORY #################
# THIS CODE WAS NOT AUTHORED BY ME. ALL CREDIT TO DSWx-SAR Team #
def intensity_display(intensity, outputdir, pol, immin=-30, immax=0):
    """save intensity images into png file

    Parameters
    ----------
    intensity: numpy.ndarray
        2 dimensional array containing linear intensity
    outputdir: str
        path for output directory
    pol: str
        specific polarization added to the file name
    immin: float
        minimum dB value for displaying intensity
    immax: float
        maximum dB value for displaying intensity
    """
    # Read GeoTIFF 
    with rasterio.open(intensity) as src: 
        intensity = src.read(1, masked = True)
    
    plt.figure(figsize=(20, 20))
    _, ax = plt.subplots(1, 1, figsize=(15, 15))

    ax.imshow(10 * np.log10(intensity),
              cmap=plt.get_cmap('gray'),
              vmin=immin,
              vmax=immax)
    
    #plt.title('RTC')
    plt.tight_layout()
    plt.savefig(os.path.join(outputdir, f'RTC_intensity_{pol}'))

def dem_display(dem_path, outputdir, filename = 'DEM', immin = None, immax=None, cmap = 'terrain'): 

    """
    Save a DEM visualization as a PNG file. 

    Parameters 
    -------
    dem : numpy.ndarray 
        2-dimensional array containing elevation values. 
    outputdir : str
        - path to the output directory. 
    filename : str 
        Output filename (without extension)
    immin : float, optional 
    immax : float, optional 
    cmap : str 
        Matplotlib colormap used to display elevation
    """

    plt.figure(figsize = (15, 15))
    fig, ax = plt.subplots(1, 1, figsize=(15, 15))

    with rasterio.open(dem_path) as src: 
        dem = src.read(1, masked = True)

    im = ax.imshow(
        dem, 
        cmap = plt.get_cmap(cmap),
        vmin=immin, 
        vmax=immax
    )

    #ax.set_title('DEM Elevation')
    ax.set_axis_off()

    cbar = fig.colorbar(im, ax=ax, shrink = 0.7)
    cbar.set_label('Elevation (m)')

    fig.savefig(
        os.path.join(outputdir, f'{filename}.png'),
        dpi=300, bbox_inches='tight'
    )

    print(f"DEM Visualization written to {outputdir}{filename}.png")

    plt.close(fig)

    return None

def paletted_display(raster_path, outputdir, filename = 'Paletted_Map'):

    """
    Save a paletted raster visualization as a PNG file. Designed for use with CSWE-SAR outputs. 

    Parameters 
    ---
    raster_path : str 
        Path to the input raster. 
    output_dir : tr 
        Path to the output directotry. 
    filename : str 
        Output filename (without extension)

    Returns a png showing ones as blue and zeroes as gray. 
    """
    cmap = ListedColormap([
        '#d3d3d3', #0
        '#00558B'     #1
    ])

    fig, ax = plt.subplots(1, 1, figsize=(15, 15))

    with rasterio.open(raster_path) as src: 
        data = src.read(1, masked=True)

    im = ax.imshow(data, cmap = cmap, vmin = 0, vmax = 1)

    ax.set_axis_off()

    # Create discrete colorbar 
    cbar = fig.colorbar(im, ax=ax, shrink=0.7, ticks = [0.25, 0.75])
    cbar.ax.set_yticklabels(['0', '1'])

    fig.savefig(
        os.path.join(outputdir, f'{filename}.png'),
        dpi=300, 
        bbox_inches='tight'
    )

    print(f'Paletted visualiuzation written to {os.path.join(outputdir, filename)}.png')

def SICD_info(input_file):
    """
    A function that extracts metadata from a SICD (Sensor-Independent Complex Data) SAR image. 
    The main thing extracted is the grid format, as this is important 
    for downstream processing with multirtc. 
    """
    reader = open_complex(input_file)           # Open the input file
    sicd = reader.get_sicds_as_tuple()[0]       # Read the input file
    grid = sicd.Grid                            # Extract grid information 
    scpcoa = sicd.SCPCOA                        # Scene Center Point, Center of Aperture
    side = scpcoa.SideOfTrack
    dca = scpcoa.DopplerConeAng                  #  Extract Doppler Cone Angle, the angle between sensor velocity vector and line of sight
    vz = scpcoa.ARPVel.Z
    orbit = "Ascending" if vz > 0 else "Descending"
    look_dir = 'Right' if side == 'R' else 'Left'
    polarizations = reader.get_sicd_polarizations()
    #print(polarizations)

    # Print information to the user. 
    print('\n=========   Resolution and Spacing     =========')
    print(f'Range Resolution (in m):          {grid.Row.ImpRespWid:.2f}')
    print(f'Range Sample Spacing (in m):      {grid.Row.SS:.2f}')
    print(f'Azimuth Resolution (in m):        {grid.Col.ImpRespWid:.2f}')
    print(f'Azimuth sample spacing (in m):    {grid.Col.SS:.2f}')

    print('\n=========    Acquisition Geometry    ===========')
    print(f"Incidence Angle (in degrees):     {scpcoa.IncidenceAng:.2f}")
    print(f'Squint Angle (in degrees):        {90.0 - dca:0.2f}')
    print(f'Orbit Direction:                  {orbit}')
    print(f'Look Direction:                   {look_dir}')

    print('\n==========    Image Format    ===========')
    print(f'Imaging Mode:                     {sicd.CollectionInfo.RadarMode.ModeType}')
    print(f'Grid Type:                        {sicd.Grid.Type}')
    print(f'Image Formation Algorithm:        {sicd.ImageFormation.ImageFormAlgo}')
    print(f'Polarization:                     {polarizations}')

def h5_dump(input_file):
    """
    A function to see the metadata from an HDF5 file.

    Intended only for use on ICEYE Dwell HDF5 imagery.
    """
    with h5py.File(input_file, 'r') as f: 
        print("ROOT ATTRS")
        keys = f.keys()

        print(keys)

        splitter = input_file.split('/')[-1]
        code = splitter.split('_')[3]

        mode_codes = ['SLF', 'SLH', 'SLEA', 'SLED', 'SLEDF', 'SLEDP', 'SM', 'SC']
        imaging_modes = ['Spotlight_Fine', 'Spotlight', 'Spotlight_Extended_Area', 'Dwell', 'Dwell_Fine', 'Dwell_Precise', 'Strip', 'Scan']

        if code in mode_codes: 
            index = mode_codes.index(code)
            mode = imaging_modes[index]

        else: 
            print(f'Imaging Mode Code {code} not recognized')

        az_res = f.get('azimuth_resolution')[()]
        az_ss = f.get('azimuth_ground_spacing')[()]
        rg_res = f.get('range_resolution_center')[()]
        rg_ss = f.get('slant_range_spacing')[()]

        inc_angle = f.get('incidence_center')[()]
        look_side = f.get('look_side')[()].decode('utf-8')      # Convert from bytes to string
        orbit_direction = f.get('orbit_direction')[()].decode() # Convert from byte to string
        pol = f.get('polarization')[()].decode()                # Convert from bytes to string

        # Calculate squint angle 
        sat_pos = np.array(f.get("coa_pos"))
        sat_vel = np.array(f.get("coa_vel"))
        target = np.array(f.get("ref_track_point_ecef"))

        try: 
            los = target - sat_pos 
        except: 
            squint_deg = 0
            los = 0

        #if los[0] != 0:
        #    los /= np.linalg.norm(los)
        #    v_hat = sat_vel / np.linalg.norm(sat_vel)
        #
        #    squint_deg = np.degrees(np.arcsin(np.dot(los, v_hat)))



        print('\n=========   Resolution and Spacing     =========')
        print(f'Range Resolution (in m):          {rg_res:.2f}')
        print(f'Range Sample Spacing (in m):      {rg_ss:.2f}')
        print(f'Azimuth Resolution (in m):        {az_res:.2f}')
        print(f'Azimuth sample spacing (in m):    {az_ss:.2f}')

        print('\n=========    Acquisition Geometry    ===========')
        print(f"Incidence Angle (in degrees):     {inc_angle:.2f}")
        #print(f'Squint Angle (in degrees):        {squint_deg:0.2f}')
        print(f'Orbit Direction:                  {orbit_direction}')
        print(f'Look Direction:                   {look_side}')

        print('\n==========    Image Format    ===========')
        print(f'Imaging Mode:                     {mode}')
        print(f'Polarization:                     {pol}')


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

def deg2rad(number): 
    """
    converts from degrees to radians
    """

    return (np.pi * number) / 180

def area_estimator(geojson_path): 
    """
    #This is a function that estimates the area of a geojson which 
    #contains a bounding box using the Haversine formula


    """
    my_path = Path(geojson_path)
    with open(my_path) as json_data:
        data = json.load(json_data)
        keys = data.keys()
        features = data['features']
        print(f'num features: {len(features)}')
        first_feature = features[0]
        feature_keys = first_feature.keys()
        first_geom = first_feature["geometry"]
        coords = first_geom["coordinates"]
        xmin = coords[0][0][0]
        ymin = coords[0][0][1]
        xmax = coords[0][1][0]
        ymax = coords[0][2][1]

        xdiff_deg = xmax - xmin 
        ydiff_deg = ymax - ymin

        mean_lat = (ymin + ymax) / 2 
        mean_lat_radians = deg2rad(mean_lat) 

        ydiff_km = ydiff_deg * 111.32
        xdiff_km = xdiff_deg * (40075 * np.cos(mean_lat_radians)) / 360\

        area_sqkm = xdiff_km * ydiff_km 
        print(f'Area of Interest is {area_sqkm:0.2f} square kilometers')

    return area_sqkm


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