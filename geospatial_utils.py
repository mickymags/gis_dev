from skimage.filters import threshold_otsu
from pathlib import Path 
from shapely.geometry import box
import geopandas as gpd
import numpy as np 
import subprocess

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