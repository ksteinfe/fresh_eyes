from PIL import Image
import os, argparse

crop_boxes = [
    ( (0,232,1664,1432), "lft"),
    ( (1664,232,3328,1432), "rig")
]


def crop_images(pth_src, pth_dst):
  fnames = [f for f in os.listdir(pth_src) if os.path.isfile(os.path.join(pth_src, f))]
  fnames = [f for f in fnames if f.endswith('.png') or f.endswith('.jpg')]
  print("found {} image files.".format(len(fnames)))
  for n, fname in enumerate(fnames):
    print("{}\t{}/{}".format(fname,n,len(fnames)))
    sname = os.path.join(pth_dst,os.path.splitext(fname)[0]+"_{}.png")
    img = Image.open(os.path.join(pth_src,fname))
    for bx,name in crop_boxes:
        img.crop(bx).save(sname.format(name))
    img.close()

    
if __name__ == '__main__':
    # create main parser
    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="path at which to find source images. all JPG and PNG files will be processed.")
    parser.add_argument('destination_path', help="path at which to save transformed images.")
    args = parser.parse_args()
    
    crop_images(args.source_path, args.destination_path)
    
    

