# pip install pillow

import os, json
from PIL import Image
dir_path = os.path.dirname(os.path.realpath(__file__))
print(dir_path)

# image file extension
img_ext = ".jpg"
# subfolder in which to find source images
img_src_path = os.path.join(dir_path,'img_src')
# subfolder in which to save modified images
img_tar_path = os.path.join(dir_path,'img_tar')

if not os.path.exists(img_tar_path): os.makedirs(img_tar_path)  


def process_file(filepath):
    filename, ext = os.path.splitext(os.path.split(filepath)[-1])
    
    img_src = Image.open(filepath)
    img_tar = Image.new(img_src.mode,img_src.size,color=None)
    fmt = img_src.format
    w,h = img_src.size
    
    savepath = os.path.join(img_tar_path,filename+'a'+ext)
    img_src.save(savepath,fmt)
    
    div = int(w/4)
    box_a = (div*0,  0,  div*1,   h)
    box_b = (div*1,  0,  div*2,   h)
    box_c = (div*2,  0,  div*3,   h)
    box_d = (div*3,  0,  div*4,   h)
    
    img_tar.paste( img_src.crop(box_d), box_a )
    img_tar.paste( img_src.crop(box_a), box_b )
    img_tar.paste( img_src.crop(box_b), box_c )
    img_tar.paste( img_src.crop(box_c), box_d )    
    savepath = os.path.join(img_tar_path,filename+'b'+ext)
    img_tar.save(savepath,fmt)
    
    img_tar.paste( img_src.crop(box_c), box_a )
    img_tar.paste( img_src.crop(box_d), box_b )
    img_tar.paste( img_src.crop(box_a), box_c )
    img_tar.paste( img_src.crop(box_b), box_d )    
    savepath = os.path.join(img_tar_path,filename+'c'+ext)
    img_tar.save(savepath,fmt)
    
    img_tar.paste( img_src.crop(box_b), box_a )
    img_tar.paste( img_src.crop(box_c), box_b )
    img_tar.paste( img_src.crop(box_d), box_c )
    img_tar.paste( img_src.crop(box_a), box_d )    
    savepath = os.path.join(img_tar_path,filename+'d'+ext)
    img_tar.save(savepath,fmt)

for root, dirs, filenames in os.walk(img_src_path):
    for filename in filenames:
        if img_ext == os.path.splitext(filename)[-1].lower():
            process_file(os.path.join(root, filename))
