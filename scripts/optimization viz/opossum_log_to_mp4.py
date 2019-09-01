
import glob, os, shutil, tempfile, argparse
from PIL import Image, ImageFont, ImageDraw
from zipfile import ZipFile
import imageio
import numpy as np

frames_per_sec = 24
show_local_best = True
LOCAL_BEST_RANGE = frames_per_sec * 3 # range of past iterations to find local best. compare to frames_per_sec

FONT = ImageFont.truetype("fonts/OpenSans-Light.ttf", 12)
PAD = 10

SRC_EXT = "jpg"


LAYOUT_STYLE = 0

def main(pth_zip, pth_dst):
    pth_mp4 = os.path.join(pth_dst, "{}.mp4".format(os.path.splitext(os.path.split(pth_zip)[1])[0])) # output_filename mimics zip file name
    print ("will save an MP4 file to {}".format(pth_mp4))


    with tempfile.TemporaryDirectory() as pth_unzip:
        print("unzipping {}".format(pth_zip))
        with ZipFile(pth_zip, 'r') as zf: zf.extractall(pth_unzip)
        print("done unzipping.")

        try:
            # the first TXT file we come across in the zip file root must be the log file
            pth_log = next(os.path.join(pth_unzip, file) for file in os.listdir(pth_unzip) if os.path.isfile(os.path.join(pth_unzip, file)) and file.endswith(".txt"))
            print("will use {} as the log file.".format(os.path.basename(pth_log)))
        except StopIteration:
            print("NO LOG FILE FOUND - are there TXT files in this ZIP file?")
            exit()


        with open(pth_log) as f: log_data = f.readlines()
        log_data = [ln.strip().split(' ') for ln in log_data if ln.strip() != ""]
        fitnesses = [float(ln[-1]) for ln in log_data]
        timestamps = [ln[1] for ln in log_data]

        src_imgs = [os.path.join(pth_unzip,f) for f in os.listdir(pth_unzip) if f.endswith(SRC_EXT)]
        viewnames = list(set([os.path.basename(pth).split('-')[-2] for pth in src_imgs])) # this is dependent on proper filename convention
        print("Found {} views: {}".format(len(viewnames), viewnames))

        rankings = ranking_per_frame(fitnesses)
        #for n, rank in enumerate(rankings): print(n, rank)

        im_size = Image.open(src_imgs[0]).size
        viewframes = {}
        for viewname in viewnames:
            viewframes[viewname] = viewport_frames(viewname, [pth for pth in src_imgs if viewname in pth], rankings, fitnesses, im_size)
            #print(frames_test)


        fitness_text_format = "{0:.3%}"
        text_size = FONT.getsize(fitness_text_format.format(99))
        text_ofst_w = im_size[0]/2.0 - text_size[0]/2.0
        text_ofst_h = text_size[1] * 2
        font_color = (50,50,50)


        frames = []
        for n in range(len(rankings)):
            fit_crnt = fitnesses[n]
            fit_glbl = rankings[n]['fit_glbl']
            fit_locl = rankings[n]['fit_locl']

            img = False
            if LAYOUT_STYLE == 0:
                img = Image.new('RGB', (im_size[0]*3 + PAD*4, (im_size[1]*len(viewframes)) + PAD*(len(viewframes)+1) + text_size[1] ) , (255,255,255))
                for row, name in enumerate(viewframes):
                    img.paste(viewframes[name][n],(0,row*(im_size[1])+((row+1)*PAD) ))

                draw = ImageDraw.Draw(img)
                draw.text(( (0*im_size[0])+(PAD*1)+text_ofst_w , im_size[1]*len(viewframes)+text_ofst_h ),fitness_text_format.format(fit_crnt),font_color,font=FONT)
                draw.text(( (1*im_size[0])+(PAD*2)+text_ofst_w , im_size[1]*len(viewframes)+text_ofst_h ),fitness_text_format.format(fit_locl),font_color,font=FONT)
                draw.text(( (2*im_size[0])+(PAD*3)+text_ofst_w , im_size[1]*len(viewframes)+text_ofst_h ),fitness_text_format.format(fit_glbl),font_color,font=FONT)
            else:
                raise NotImplementedError("layout style {} is not ready".format(LAYOUT_STYLE))

            if img: frames.append(img)


        print("saving mp4 file to {}".format(pth_mp4))
        writer = imageio.get_writer(pth_mp4, fps=frames_per_sec)
        for im in frames: writer.append_data(np.array(im))
        writer.close()

def ranking_per_frame(fits):
    rankings = [{'idx_glbl':0, 'idx_locl':0, 'fit_glbl':fits[0], 'fit_locl':fits[0]}]
    for n in range(1,len(fits)):
        glb = sorted([(f,i) for i,f in enumerate(fits[:n])])
        lcl = sorted([(f,max(0,n-LOCAL_BEST_RANGE) + i) for i,f in enumerate(fits[max(0,n-LOCAL_BEST_RANGE):n])])
        rankings.append({'idx_glbl':glb[-1][1], 'idx_locl':lcl[-1][1], 'fit_glbl':glb[-1][0], 'fit_locl':lcl[-1][0]})
    return rankings

def viewport_frames(name, pth_imgs, ranks, fits, im_size):
    if len(pth_imgs) - len(ranks) == 1:
        print("There is one more images than there are log entries.\n\tThis is usually because Opossum displays the most fit candidate at the end of the optimization.\n\tWill remove the last image and continue.")
        pth_imgs = pth_imgs[:-1]
    if len(pth_imgs) != len(ranks):
        raise Exception("Number of images for this viewport in ZIP ({}) don't match the number of log entries ({})".format(len(pth_imgs),len(ranks)))

    print("cutting frames for {} with {} images and {} log entries".format(name,len(pth_imgs),len(ranks)))

    w,h = im_size[0],im_size[1]
    fitness_text_format = "{0:.4f}%"
    text_size = FONT.getsize(fitness_text_format.format(99))
    text_ofst_w = w/2.0 - text_size[0]/2.0
    text_ofst_h = text_size[1] * 1.5
    font_color = (50,50,50)

    frames = []
    for n in range(len(ranks)):
        img_crnt, fit_crnt = Image.open(pth_imgs[n]), fits[n]
        img_glbl, fit_glbl = Image.open(pth_imgs[ranks[n]['idx_glbl']]), ranks[n]['fit_glbl']
        img_locl, fit_locl = Image.open(pth_imgs[ranks[n]['idx_locl']]), ranks[n]['fit_locl']

        img = False
        if LAYOUT_STYLE == 0:
            img = Image.new('RGB', ((w+PAD)*3, h), (255,255,255))
            img.paste(img_crnt,(PAD,0))
            img.paste(img_locl,(w+PAD*2,0))
            img.paste(img_glbl,(w*2+PAD*3,0))

            #draw = ImageDraw.Draw(img)
            #draw.text(( (0*w)+text_ofst_w , h-text_ofst_h ),fitness_text_format.format(fit_crnt),font_color,font=FONT)
            #draw.text(( (1*w)+text_ofst_w , h-text_ofst_h ),fitness_text_format.format(fit_locl),font_color,font=FONT)
            #draw.text(( (2*w)+text_ofst_w , h-text_ofst_h ),fitness_text_format.format(fit_glbl),font_color,font=FONT)
        elif LAYOUT_STYLE == 1:
            img = Image.new('RGB', (w, h*3), (255,255,255))
            img.paste(img_crnt,(0,0))
            img.paste(img_locl,(0,h))
            img.paste(img_glbl,(0,h*2))
            raise NotImplementedError("not done with vertical style")
        else:
            raise NotImplementedError("layout style {} is not ready".format(LAYOUT_STYLE))

        if img: frames.append(img)
        else:
            raise ValueError("what happened here? error in creating viewport frame image")

    return frames




if __name__ == '__main__':

    """Checks if a path is an actual file"""
    def is_file(pth):
        if not os.path.isfile(pth):
            msg = "{0} is not a file".format(pth)
            raise argparse.ArgumentTypeError(msg)
        else:
            return os.path.abspath(os.path.realpath(os.path.expanduser(pth)))

    # create main parser

    parser = argparse.ArgumentParser()
    parser.add_argument('zip_path', help="path at which to find a ZIP file containing images and Opossum log file.", type=is_file)
    #parser.add_argument('destination_path', help="path at which to save resulting MP4", nargs='?', default=os.getcwd())
    args = parser.parse_args()

    pth_zip = os.path.abspath(args.zip_path)
    pth_dst = os.path.dirname(pth_zip)

    #print(args)
    main(pth_zip, pth_dst)
