# Copyright (C) 2023 Anestis Kaimakamidis, George Spaias, V. Naserentin
# Licensed under the MIT License
#
# This script documents the workflow for SFPG.
# https://github.com/dtcc-platform/dtcc/issues/56

# Initially add the extra functionality to fetch footprints from OSM:


# Initially we are adding the working code from Anestis' MSc:

import cv2
import matplotlib.pyplot as plt
import numpy as np
from keras import backend as K
import rasterio
import geopandas as gpd
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt
import geopandas as gpd
import laspy
from shapely.geometry import mapping
from rasterio.mask import mask


#load point cloud
las = laspy.read("10C030_657_67_2550.laz")

X = las.X*las.header.x_scale + las.header.x_offset
Y = las.Y*las.header.y_scale + las.header.y_offset
point_data = np.stack([X, Y, las.Z, las.classification], axis=0).transpose((1, 0))


#load building footprints

df = gpd.read_file("../Fastighetskartan_Bebyggelse_latest_shp_br_Property_map_Built_up_areas_df550b58-742c-4484-9424-9979d39e7cdb_/by_01.shp")

df1 = gpd.GeoDataFrame()
s_buildings = []
for poly in df['geometry']:
    bounds = list(poly.bounds)
    if(bounds[0] >= las.header.x_min and bounds[1] >= las.header.y_min and bounds[2] <= las.header.x_max and bounds[3] <= las.header.y_max):
        s_buildings.append(poly)




a = {'geometry' : s_buildings}
df_buildings = gpd.GeoDataFrame(a, crs=df.crs)

df_buildings = df_buildings.to_crs(4326)


#pick a building


a = {'geometry' : s_buildings[91:92]}
df_b = gpd.GeoDataFrame(a, crs=df.crs)
poly= df_b['geometry'][0]
df_b = df_b.to_crs(4326)


# isolate building point cloud points
building = point_data[np.where(np.all([point_data[:,0] >= poly.bounds[0], point_data[:,0] <= poly.bounds[2], point_data[:,1] >= poly.bounds[1], point_data[:,1] <= poly.bounds[3]], axis=0))]
building = building[building[:,3] == 1]


#calculate building coordinates from footprint
lat, lng = df_b['geometry'][0].centroid.y, df_b['geometry'][0].centroid.x

#fetch aerial image from google maps
import googlemaps
from PIL import Image
import requests



apikey = 'AIzaSyBTqS7ul4p32-QjPBbNs46c4FT10zUGiQQ'
gmaps = googlemaps.Client(key=apikey)


url = f'https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom=20&size=512x512&maptype=satellite&key={apikey}'
a = requests.get(url, stream=True)

image = Image.open(a.raw)
image.save('satellite.png')

#google maps bounding box
dLongitude = (512 / 256 ) * ( 360 / pow(2, 21) )

dLatitude = (512 / 256 ) * ( 180 / pow(2, 21) )

west = lng-dLongitude
east = lng+dLongitude
south = lat-dLatitude
north = lat+dLatitude

#Load pre-trained network and predict image
import keras
from helpers1 import build_unet1
model = build_unet1((512,512,3), 6)
model.load_weights('../m1655470/RID_dataset/roof_segmentation_model(domain_adapt, 6classes).hdf5')

I1 = cv2.imread('satellite.png')
I = cv2.cvtColor(I1, cv2.COLOR_BGR2RGB)


pred = np.argmax(model.predict(I.reshape(1,512,512,3)), axis=-1)
cv2.imwrite('mask.png', pred[0])

#convert prediction to TIFF format
image = Image.open('mask.png').convert('L')


# Create a GeoTIFF file
tif_path = 'mask.tif'
with rasterio.open(tif_path, 'w', driver='GTiff', height=image.size[1], width=image.size[0], dtype=rasterio.uint8, count=1) as dst:
    # Set the transformation and coordinate system
    transform = rasterio.transform.from_bounds(west, south, east, north, image.size[0], image.size[1])
    dst.transform = transform
    dst.crs = rasterio.crs.CRS.from_epsg(3006)

    # Write the image band to the GeoTIFF file
    dst.write(image, indexes=1)

#Crop prediction with respect to the footprint
geom_building = df_b.geometry.values

with rasterio.open("mask.tif") as src:
    fet = []
    for index, geom in enumerate(geom_building):
        
        fet.append(mapping(geom))

  
    
    # the mask function returns an array of the raster pixels within this feature
    out_image, out_transform = mask(src, fet, crop=False, indexes=1, nodata=6)

    out_image1 = np.where(out_image == 5, 6, out_image)



#Get predicted classes
out_img_processed = out_image.reshape(512,512,1)

# Identify the unique classes in the mask
unique_classes = np.unique(out_image)

# Calculate the center point for each class
class_centers = {}
for class_value in unique_classes:
    # Find the pixels belonging to the current class
    class_pixels = np.where(out_image == class_value)

    # Calculate the center point of the class
    center_x = np.average(class_pixels[0])
    center_y = np.average(class_pixels[1])

    # Store the center point in the dictionary
    class_centers[class_value] = (center_x, center_y)

'''# Display the center points
for class_value, center_point in class_centers.items():
    print(f"Class {class_value}: Center point coordinates - {center_point}")'''


#Implement filling algorithm

thresh = 500
for class_value, center_point in class_centers.items():
    if(class_value == 6):
        continue
    class_pixels = np.where(out_image == class_value)
    class_pixels = np.array(class_pixels)


    if(len(class_pixels[0]) < thresh or class_value == 5):
        
        
        min_dst = np.full(len(class_pixels[0]), np.inf)
        val = np.zeros(len(class_pixels[0]))
        for class_value1, center_point1 in class_centers.items():
            class_pixels1 = np.where(out_image == class_value1)
            class_pixels1 = np.array(class_pixels1)
            if(class_value1 == 6 or class_value == class_value1 or len(class_pixels1[0]) < thresh):
                continue
            tmp = np.subtract(class_pixels.T, np.array([center_point1]))
            dst = tmp[:,0]**2 + tmp[:,1] **2

            a = np.less(dst.T, min_dst)
            if(len(a) > 0):
                min_dst[a] = dst[a]
                val[a] = class_value1

        out_img_processed[class_pixels[0], class_pixels[1]] = val.reshape(len(val),1)
          
            

#Implement Harris corner detection algorithm
image = out_img_processed

block_size = 3
ksize = 9
k = 0.15

dx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=ksize)
dy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=ksize)

dx2 = dx * dx
dy2 = dy * dy
dxy = dx * dy

sigma = 1.0
dx2 = cv2.GaussianBlur(dx2, (block_size, block_size), sigma)
dy2 = cv2.GaussianBlur(dy2, (block_size, block_size), sigma)
dxy = cv2.GaussianBlur(dxy, (block_size, block_size), sigma)

det = dx2 * dy2 - dxy * dxy
trace = dx2 + dy2
R = det - k * trace * trace



threshold = 0.0001
corners = np.argwhere(R > threshold * R.max())
corners = corners[:, ::-1]

image_with_corners = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
for corner in corners:
    x, y = corner
    cv2.circle(image_with_corners, (x, y), 3, (5), 5)

image_with_corners = image_with_corners[:,:,0]

#Perform point filtering 
intersections = corners
img = np.copy(out_img_processed)
intersections_new = []

write = True
thresh = 10
for i, inter in enumerate(intersections):
    if(inter[0] < 0 or inter[1] < 0 or inter[0] > img.shape[0] or inter[1] > img.shape[1]):
        continue
    else:
        for j in range(len(intersections_new)):
            if(intersections_new[j][0] >= inter[0] - thresh and intersections_new[j][0] <= inter[0] + thresh and intersections_new[j][1] >= inter[1] - thresh and intersections_new[j][1] <= inter[1] + thresh):
                write = False
                break
        if(write):
            intersections_new.append(inter)

        
        write = True


intersections = []
control_points = []

classes = []
thresh = 20
img = img.reshape(512,512)
img = img.T
for i, inter in enumerate(intersections_new):
    tmp_cl = []
    tmp_con = []
    if(inter[0] + thresh >= 512 or inter[1] + thresh >= 512 or inter[0] - thresh < 0 or inter[1] - thresh < 0):
        continue
    if(img[inter[0] + thresh, inter[1]] != 6):
        tmp_con.append([inter[0] + thresh, inter[1]])
        tmp_cl.append(img[inter[0] + thresh, inter[1]])
    if(img[inter[0] - thresh, inter[1]] != 6):
        if(not img[inter[0] - thresh, inter[1]] in tmp_cl):
            tmp_con.append([inter[0] - thresh, inter[1]])
            tmp_cl.append(img[inter[0] - thresh, inter[1]])
    if(img[inter[0], inter[1] + thresh] != 6):
        if(not img[inter[0], inter[1] + thresh] in tmp_cl):
            tmp_con.append([inter[0], inter[1] + thresh])
            tmp_cl.append(img[inter[0], inter[1] + thresh])
    if(img[inter[0], inter[1] - thresh] != 6):
        if(not img[inter[0], inter[1] - thresh] in tmp_cl):
            tmp_con.append([inter[0], inter[1] - thresh])
            tmp_cl.append(img[inter[0], inter[1] - thresh])
    
    if(len(tmp_cl) > 0 ):
        control_points.append(tmp_con)
        intersections.append(inter)
        classes.append(tmp_cl)


#Transform coordinates picture to ESPG4326
corners = []

for p in intersections:
    corners.append(out_transform*p)

control_points_t = []
for p in control_points:
    tmp = []
    for k in range(len(p)):
        tmp.append(out_transform*p[k])
    control_points_t.append(tmp)

#Transform coordinates EPSG4326 to EPSG3006
from pyproj import Transformer
corners_transformed = []
input_crs = "EPSG:4326"

# Define the target coordinate system (4326 - latitude-longitude)
target_crs = "EPSG:3006"

# Create a transformer for the coordinate transformation
transformer = Transformer.from_crs(input_crs, target_crs)

for p in corners:
    corners_transformed.append(transformer.transform(p[1], p[0]))

control_points_t3006 = []
for p in control_points_t:
    tmp = []
    for k in range(len(p)):
        tmp.append(transformer.transform(p[k][1], p[k][0]))
    control_points_t3006.append(tmp)

#Match corners with 3D point cloud points 

final = np.zeros((len(corners_transformed), 3))
lim = max(building[:,2])- (max(building[:,2])-min(building[:,2]))/2
lim = 3600
for i, p in enumerate(corners_transformed):


    
    wh = np.where(np.all([np.abs(np.subtract(building[:,0], p[1])) < 1, np.abs(np.subtract(building[:,1], p[0])) < 1, building[:,2] > lim], axis=0))[0]
    tmp = building[wh]
    
    final[i] = [corners_transformed[i][1], corners_transformed[i][0], np.mean(tmp[:,2])]


#Scale 3d points
from sklearn.preprocessing import StandardScaler

stc = StandardScaler()
final = stc.fit_transform(final)

#Assign points to surfaces
done = []
surfaces = []

for i in range(len(classes)):
    for j in range(len(classes[i])):
        if not classes[i][j] in done:
            surfaces.append([])
            done.append(classes[i][j])
            surfaces[-1].append(final[i])
        else:
            
            ind = done.index(classes[i][j])

            surfaces[ind].append(final[i])

#Reconstruction completed!