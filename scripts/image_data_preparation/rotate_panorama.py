import os, json
from PIL import Image

# image file extension
img_ext = ".jpg"


def main(img_src_path, img_tar_path):
    print("this script is not yet finished.")
    exit()

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


if __name__ == '__main__' and __package__ is None:
    # ---- FEUTIL ---- #
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__)))) # add grandparent folder to the module search path
    import _fresh_eyes_script_utilities as feu # import fresh eyes fe_util
    # ---- FEUTIL ---- #

    main()
