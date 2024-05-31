# Sentinel2toGeoSpatialPrithvi
Code to generate input data for Geo Spatial Prithvi Crop Classification problem using Sentinel-2 satellite data

This code takes three time steps (months) data from same year as input and generates a data of size 224x224x16. 
The data needs to be downloded from Sentinel-2 for the following 6 bands - Blue, Green, Red, NIR, SW1, SW2.
The resultant image of this code can be used as input to Prithvi Crop Classification problem for different use cases.

Data for a Japan co-ordinate for three months of the year 2023 is provided in the folder Data_Japan to use as input.

Use requirements.txt to install required packages.
