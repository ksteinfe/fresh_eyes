import sys, os, math
import numpy as np
from zipfile import ZipFile
from PIL import Image
from hilbert import HilbertCurve


src_directory = r"Y:\GitHub\fresh-eyes\utility scripts\voxel_to_image\samples"
output_directory = r"C:\Users\ksteinfe\Desktop\TEMP"

vxl_filename = "pyramid_16"
vxl_zip_pth = os.path.join(src_directory, "{}.zip".format(vxl_filename))

def load_image_stack(pth):
    imgs = []
    with ZipFile(vxl_zip_pth) as archive:
        img_cnt = len(archive.infolist())
        for entry in archive.infolist():
            with archive.open(entry) as file:
                img = Image.open(file)
                if any([img.size[0] != img.size[1], img.size[0] != img_cnt]):
                    raise Exception("Zip archive contains non-cubic voxel information at image {}: {}".format(file.name, "img.size:{} != img_cnt:{}".format(img.size, img_cnt)))
                imgs.append(img)
    return imgs

def is_power_2(num):
    return ((num & (num - 1)) == 0) and num > 0
    
def eval(vxl_stack,crd):
    z,crd = crd[2], (crd[0],crd[1])
    img = vxl_stack[z]
    # TODO: what if this is a color and not greyscale?
    val = img.getpalette()[img.getpixel(crd)]
    if val > 128: return False # white is empty
    else: return True # black is filled
            
            
vstk = load_image_stack(vxl_zip_pth)
dim = len(vstk)
print("loaded a voxel image of dimension {}".format(dim))
if not is_power_2(dim):
    raise Exception("Voxel cube must be a dimension that is a power of 2. dim:{}".format(dim))

if dim==16:
    cube_p = int(math.log(dim,2))
    curve_p = cube_p+2
elif dim==64:
    cube_p = int(math.log(dim,2))
    curve_p = cube_p+3
else: 
    raise Exception("Because we want to avoid interpolation, voxel cube must be either 16 units or 64 units on a side. dim:{}".format(dim))

img_dim = 2**curve_p
print("creating a hilbert cube of side length: {} voxels: {}".format(2**cube_p, (2**cube_p)**3))
hilbert_cube = HilbertCurve(cube_p, 3)
print("creating a hilbert curve of side length: {} pixels: {}".format(img_dim, img_dim**2))
hilbert_curve = HilbertCurve(curve_p, 2)

crds_cube = [(xi,yi,zi) for xi in range(dim) for yi in range(dim) for zi in range(dim)]
tarr = [ hilbert_cube.distance_from_coordinates(crd) for crd in crds_cube ]
crds_curve = [ hilbert_curve.coordinates_from_distance(t) for t in tarr ]
            
#print(crds_curve)

img = Image.new('RGB', (img_dim,img_dim), color='white')
pixels = img.load() # create the pixel map

for n, crd in enumerate(crds_curve):
    #t = n/len(crds_curve)
    #clr = (int(255*t),0,int(255*t))
    if eval(vstk,crds_cube[n]): clr = (0,0,0)
    else: clr = (255,255,255)
    pixels[crd[0],crd[1]] = clr

img.save("out.jpg")