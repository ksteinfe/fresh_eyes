from PIL import Image
import os, argparse

def xform_images(pth_src, pth_dst):
  fnames = [f for f in os.listdir(pth_src) if os.path.isfile(os.path.join(pth_src, f))]
  fnames = [f for f in fnames if f.endswith('.png') or f.endswith('.jpg')]
  #fnames = [f for f in fnames if not f.endswith('_btm.png')]
  #fnames = [f for f in fnames if not f.endswith('_top.png')]
  print("found {} image files.".format(len(fnames)))
  for n, fname in enumerate(fnames):
    print("{}\t{}/{}".format(fname,n,len(fnames)))
    sname = os.path.join(pth_dst,os.path.splitext(fname)[0]+"_{}.png")
    img = Image.open(os.path.join(pth_src,fname))
    img.rotate(90, expand=True).save(sname.format("rrt"))
    img.rotate(270, expand=True).save(sname.format("rlf"))
    img.transpose(Image.FLIP_LEFT_RIGHT).save(sname.format("flr"))
    img.transpose(Image.FLIP_TOP_BOTTOM).save(sname.format("ftb"))
    img.close()

    
if __name__ == '__main__':
    # create main parser
    parser = argparse.ArgumentParser()
    parser.add_argument('source_path', help="path at which to find source images. all JPG and PNG files will be processed.")
    parser.add_argument('destination_path', help="path at which to save transformed images.")
    args = parser.parse_args()
    
    xform_images(args.source_path, args.destination_path)
    
    

