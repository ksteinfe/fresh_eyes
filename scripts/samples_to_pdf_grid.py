import os, sys, random
from zipfile import ZipFile
from PIL import Image

import numpy as np

from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


CNVS_SIZE = 34.75*inch
CNVS_MARG = 1.00*inch
IMG_CNT = 25 # number of images along side of grid (n*n total)
IMG_MARG = 0.1 # margin between images expressed as a ratio of image size

DSTPATH = r"/home/ksteinfe/Desktop/TEMP"
NAME = "samplegrid"
PTH_TO_SET_A = r"/media/ksteinfe/DATA/RRSYNC/projects/thesis_gan/xie_yang/groundgan/results/181113_groundgan_samples.zip"
PTH_TO_SET_B = r"/media/ksteinfe/DATA/RRSYNC/projects/thesis_gan/xie_yang/groundgan/training/181113"

def main():

    imgs_a = get_imgs(PTH_TO_SET_A)
    imgs_b = get_imgs(PTH_TO_SET_B, 300, limit_to=9999) # resizes to 300x300, limit to first N files
    random.shuffle(imgs_a)
    random.shuffle(imgs_b)

    cnvs = canvas.Canvas(os.path.join(DSTPATH,'{}.pdf'.format(NAME)), pagesize=(CNVS_SIZE,CNVS_SIZE))


    grd_crds, grd_stp = np.linspace(CNVS_MARG, CNVS_SIZE-CNVS_MARG, IMG_CNT, endpoint=False, retstep=True)
    img_mars = np.linspace(0, grd_stp*IMG_MARG, IMG_CNT)
    img_dim = grd_stp*(1-IMG_MARG)

    ai,bi = 0,0
    for xi, (x, xmar) in enumerate(zip(grd_crds,img_mars)):
        for yi, (y, ymar) in enumerate(zip(grd_crds,img_mars)):

            if pick(xi,yi):
                img = ImageReader(imgs_b[bi])
                bi+=1
                if bi >= len(imgs_b):
                    print("NOT ENOUGH IMAGES IN B")
                    bi=0
            else:
                img = ImageReader(imgs_a[ai])
                ai+=1
                if ai >= len(imgs_a):
                    print("NOT ENOUGH IMAGES IN A")
                    ai=0

            cnvs.drawImage(img, x+xmar, y+ymar, width=img_dim, height=img_dim, preserveAspectRatio=True)


    cnvs.showPage()
    cnvs.save()

def pick(xi,yi):
    #print(xi,yi)
    #return (xi+yi)%3==0 and yi%3==0
    return (xi+yi)%3==yi%2 and yi%3==0

def get_imgs(pth, resize_to=False, limit_to=False):
    valid_img_extensions = ["png","jpg"]
    imgs = []
    if os.path.isdir(pth):
        print("getting images from directory: \n{}".format(pth))
        files = os.listdir(pth)
        if limit_to: files = files[:limit_to]
        for file in files:
            if any( [ file.lower().endswith(ext) for ext in valid_img_extensions] ):
                imgs.append(Image.open(os.path.join(pth, file)))
                #imgs.append(Image.new("RGB", (200,200), (255, 0, 255) ))

    else:
        print("getting images from ZIP file: \n{}".format(os.path.split(pth)[1]))
        with ZipFile(pth) as archive:
            for entry in archive.infolist():
                if any( [ entry.filename.lower().endswith(ext) for ext in valid_img_extensions] ):
                    with archive.open(entry) as file: imgs.append(Image.open(file))

    print("found {} image files".format(len(imgs)))
    if resize_to:
        for img in imgs:
            if img.size[0] > resize_to or img.size[1] > resize_to: img.thumbnail((resize_to,resize_to), Image.ANTIALIAS)
    return imgs

if __name__ == '__main__':
    main()
