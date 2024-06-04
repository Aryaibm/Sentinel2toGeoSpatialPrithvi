# Reads the sentinel-2 data and stacks with three time steps as the input to Prtithvi crop classification
# Check the input variables --> root_folder, year and month

import os
import numpy as np
from osgeo import gdal, gdalconst
from PIL import Image
import rasterio
from rasterio.windows import Window
from rasterio.plot import show
import matplotlib.pyplot as plt
import glob

def windowing_sentinel(filename, root_folder, year, month):
    # Windowing for Sentinel data
    with rasterio.open(filename) as src:
    # Define the window to extract the 224x224 region
        window = Window(0, 0, 224, 224)  # Adjust the window coordinates as needed

        # Read all bands for the 224x224 window
        window_data = []
        for band_number in range(1, src.count + 1):  # Loop through all bands
            band_data = src.read(band_number, window=window)
            window_data.append(band_data)

        # Get metadata for the output TIFF file
        meta = src.meta.copy()
        meta['width'] = window.width
        meta['height'] = window.height
        meta['transform'] = rasterio.windows.transform(window, src.transform)

        # Define the output filename
        output_filename = root_folder+year+"/window_extracted_"+year+"_"+month+".tif"

        # Write the window data to a TIFF file
        with rasterio.open(output_filename, 'w', **meta) as dst:
            for i, band_data in enumerate(window_data):
                dst.write(band_data, i + 1)

    print("\nWindow data saved to", output_filename)

def read_window_sentinel(root_folder, year, months):
    for month in months:
        # Construct the directory path
        directory = os.path.join(root_folder, year, month, "*")
        print ("\n\n\n", directory)
        temp = glob.glob(directory)
        filename = temp[0]+"/response.tiff"
        windowing_sentinel(filename, root_folder, year, month)

def stacking_images_level1(root_folder, year, months):
    dat1 = root_folder+year+"/window_extracted_"+year+"_"+months[0]+".tif"
    dat2 = root_folder+year+"/window_extracted_"+year+"_"+months[1]+".tif"        
    dat3 = root_folder+year+"/window_extracted_"+year+"_"+months[2]+".tif"

    # Define paths to the three GeoTIFF files
    file_paths = [dat1, dat2, dat3]

    #Read one image of HLS to get its metadata
    file_path = "./Sentinel2toGeoSpatialPrithvi/src/time_step_0.tif"

    first_dataset = gdal.Open(file_path, gdalconst.GA_ReadOnly)
    if first_dataset is None:
        print("Error: Could not open the first dataset.")
        exit(1)


    # Get metadata from the first dataset
    width = first_dataset.RasterXSize
    height = first_dataset.RasterYSize
    bands = first_dataset.RasterCount
    driver = first_dataset.GetDriver()

    # Create a new GeoTIFF file for the merged image
    output = root_folder+year+"/Initial_merged.tif"
    merged_dataset = driver.Create(output, width, height, bands * len(file_paths), first_dataset.GetRasterBand(1).DataType)
    if merged_dataset is None:
        print("Error: Could not create the merged dataset.")
        exit(1)

    # Loop through the input files and merge them into the new dataset
    for i, file_path in enumerate(file_paths):
        dataset = gdal.Open(file_path, gdalconst.GA_ReadOnly)
        if dataset is None:
            print(f"Error: Could not open the dataset {file_path}.")
            exit(1)

        for band in range(bands):
            band_data = dataset.GetRasterBand(band + 1).ReadAsArray()
            merged_dataset.GetRasterBand(i * bands + band + 1).WriteArray(band_data)

        dataset = None

    # Close the merged dataset
    merged_dataset = None

def resplitting_stacks(root_folder, year):
    #Resplitting and checking

    # Load the GeoTIFF file
    file = root_folder+year+"/Initial_merged.tif"
    dataset = gdal.Open(file, gdal.GA_ReadOnly)

    if dataset is None:
        print("Error: Could not open the dataset.")
        exit(1)

    # Get dimensions of the dataset
    # width = dataset.RasterXSize
    # height = dataset.RasterYSize
    bands = dataset.RasterCount

    # Define the size of each image
    image_width = 224
    image_height = 224

    # Define the number of time steps
    time_steps = 3

    # Calculate the number of bands per time step
    bands_per_time_step = bands // time_steps

    # Loop through time steps
    for t in range(time_steps):
        # Create a new GeoTIFF file for each time step
        time_step_path = root_folder+year+"/Initial_merged"
        new_ds = gdal.GetDriverByName('GTiff').Create(time_step_path+f"_time_step_{t}.tif", image_width, image_height, bands_per_time_step, gdal.GDT_Float32)

        if new_ds is None:
            print("Error: Could not create the new dataset.")
            exit(1)

        # Calculate the starting and ending bands for the current time step
        start_band = t * bands_per_time_step
        end_band = start_band + bands_per_time_step

        for b in range(start_band, end_band):
            # Read data for each band and time step
            band_data = dataset.GetRasterBand(b + 1).ReadAsArray()

            if band_data is None:
                print(f"Error: Could not read data for band {b + 1}.")
                exit(1)

            # Write the band data to the new GeoTIFF file
            new_ds.GetRasterBand(b - start_band + 1).WriteArray(band_data)

        # Close the new GeoTIFF file
        new_ds = None

    dataset = None

def scaling_bands(root_folder, year):
    # Scaling
    time_step_path = root_folder+year+"/Initial_merged"
    tgt_path = "./Sentinel2toGeoSpatialPrithvi/src/time_step_0.tif"
    time_steps=3
    for time_step in range(time_steps):
        # Load the source and target raster images
        src_path = time_step_path+"_time_step_" + str(time_step)+".tif"
        
        src_dataset = rasterio.open(src_path)
        tgt_dataset = rasterio.open(tgt_path)

        # Read the bands into numpy arrays
        src_data = src_dataset.read()
        tgt_data = tgt_dataset.read()

        # Calculate the min and max values for each band in both images
        src_min = np.min(src_data, axis=(1, 2))  # Assuming bands are axis 0
        src_max = np.max(src_data, axis=(1, 2))
        tgt_min = np.min(tgt_data, axis=(1, 2))
        tgt_max = np.max(tgt_data, axis=(1, 2))

        # Scale the source image to match the range of the target image for each band
        scaled_data = []
        for i in range(src_data.shape[0]):  # Loop over bands
            scaled_band = np.interp(src_data[i], (src_min[i], src_max[i]), (tgt_min[i], tgt_max[i]))
            scaled_data.append(scaled_band)

        scaled_data = np.array(scaled_data)

        # Create a new raster file with the scaled data
        output_path = root_folder+year+"/scaled_image_"+str(time_step)+".tif"
        with rasterio.open(
            output_path,
            'w',
            driver='GTiff',
            width=src_dataset.width,
            height=src_dataset.height,
            count=src_data.shape[0],  # Use the number of bands from the source image
            dtype=src_data.dtype,
            crs=src_dataset.crs,
            transform=src_dataset.transform,
        ) as dst:
            dst.write(scaled_data)

        # Optionally, visualize the scaled image
        # show(scaled_data)

def restack_rescaled(root_folder, year):
    # Stacking three converted images - Trying the stacking of three same images for trial

    # Define paths to the three GeoTIFF files
    dat1 = root_folder+year+"/scaled_image_0.tif"
    dat2 = root_folder+year+"/scaled_image_1.tif"
    dat3 = root_folder+year+"/scaled_image_2.tif"

    file_paths = [dat1, dat2, dat3]
    
    #Read one image of HLS to get its metadata
    file_path = "./Sentinel2toGeoSpatialPrithvi/src/time_step_0.tif"

    first_dataset = gdal.Open(file_path, gdalconst.GA_ReadOnly)
    if first_dataset is None:
        print("Error: Could not open the first dataset.")
        exit(1)

    # Get metadata from the first dataset
    width = first_dataset.RasterXSize
    height = first_dataset.RasterYSize
    bands = first_dataset.RasterCount
    driver = first_dataset.GetDriver()

    # Create a new GeoTIFF file for the merged image
    merged_dataset = driver.Create(root_folder+"input_"+year+".tif", width, height, bands * len(file_paths), first_dataset.GetRasterBand(1).DataType)
    if merged_dataset is None:
        print("Error: Could not create the merged dataset.")
        exit(1)

    # Loop through the input files and merge them into the new dataset
    for i, file_path in enumerate(file_paths):
        dataset = gdal.Open(file_path, gdalconst.GA_ReadOnly)
        if dataset is None:
            print(f"Error: Could not open the dataset {file_path}.")
            exit(1)

        for band in range(bands):
            band_data = dataset.GetRasterBand(band + 1).ReadAsArray()
            merged_dataset.GetRasterBand(i * bands + band + 1).WriteArray(band_data)

        dataset = None

    # Close the merged dataset
    merged_dataset = None

    print("\n\n Successfully completed the pre-processing of Sentinel-2 data")
    print("\nPre-processed data saved as "+ root_folder + "input_" + year + ".tif \n")

def main():
    print("Welcome")
    # Modify the data path, year and month
    root_folder = "./Sentinel2toGeoSpatialPrithvi/Data_Japan/Sentinel_Data/"
    year = "2023"
    months = ["May", "June",  "Sep"]

    read_window_sentinel(root_folder, year, months)    
    stacking_images_level1(root_folder, year, months)
    resplitting_stacks(root_folder, year)
    scaling_bands(root_folder, year)
    restack_rescaled(root_folder, year)
    
if __name__ == "__main__":
    main()
    
