import imageio
import glob, os, shutil, argparse
#from PIL import Image, ImageSequence, ImageFont, ImageDraw
from zipfile import ZipFile

"""
VARIABLES
"""

def main(pth_src, pth_dst, ext, fps=24):
    src_files = [os.path.join(pth_src,file) for file in os.listdir(pth_src) if file.endswith(ext)]
    print("found {} valid source files.".format(len(src_files)))
    if len(src_files) == 0: raise Exception("No valid source files found! Check the file extension we're looking for?")
    pth_out = os.path.join(pth_dst,'{}_out.mp4'.format(os.path.basename(pth_src)))
    print("saving mp4 file to {}".format(pth_out))
    writer = imageio.get_writer(pth_out, fps=fps)
    for im in src_files: writer.append_data(imageio.imread(im))
    writer.close()


if __name__ == '__main__':
    # create main parser
    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="path at which to find source images.")
    parser.add_argument('destination_path', help="path at which to save upscaled images.")
    parser.add_argument("--source_extension", default="jpg", help="file extension of source images.")
    args = parser.parse_args()

    main(args.source_path, args.destination_path, args.source_extension)
