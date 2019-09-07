
import glob, os, shutil, tempfile, argparse, csv, io
from PIL import Image, ImageFont, ImageDraw
from zipfile import ZipFile
import imageio
import numpy as np

frames_per_sec = 32
LOCAL_BEST_RANGE = frames_per_sec * 5 # range of past iterations to find local best. compare to frames_per_sec

FONT = ImageFont.truetype("fonts/OpenSans-Light.ttf", 12)
PAD = 10
SRC_EXT = "jpg"
LAYOUT_STYLE = 0
BK_COLOR = (255,255,255)

def main(pth_zip, pth_dst):
    pth_mp4 = os.path.join(pth_dst, "{}.mp4".format(os.path.splitext(os.path.split(pth_zip)[1])[0])) # output_filename mimics zip file name
    print ("will save an MP4 file to {}".format(pth_mp4))


    with tempfile.TemporaryDirectory() as pth_unzip:
        print("unzipping {}".format(pth_zip))
        with ZipFile(pth_zip, 'r') as zf: zf.extractall(pth_unzip)
        print("done unzipping.")

        try:
            # the first CSV file we come across in the zip file root must be the log file
            pth_log = next(os.path.join(pth_unzip, file) for file in os.listdir(pth_unzip) if os.path.isfile(os.path.join(pth_unzip, file)) and file.endswith(".csv"))
            print("will use {} as the log file.".format(os.path.basename(pth_log)))
        except StopIteration:
            print("NO LOG FILE FOUND - are there TXT files in this ZIP file?")
            exit()

        log_data, viewnames = process_log_data(pth_log, pth_unzip)
        log_data = rank_log_data(log_data)

        im_size = Image.open(log_data[0]['imgs'][viewnames[0]]).size
        viewframes = {viewname: viewport_frames(log_data, viewname, im_size) for viewname in viewnames}

        fitness_text_format = "{0:.3%}"
        text_size = FONT.getsize(fitness_text_format.format(99))
        text_ofst_w = im_size[0]/2.0 - text_size[0]/2.0
        text_ofst_h = text_size[1]
        font_color = (50,50,50)

        frames = []
        for step in log_data:
            img = False
            if LAYOUT_STYLE == 0:
                try:
                    w = im_size[0]*3 + PAD*4
                    h = ((im_size[1]+PAD)*len(viewframes)) + PAD + text_size[1]
                    img = Image.new('RGB', (w,h) , BK_COLOR)
                    for row, name in enumerate(viewframes):
                        img.paste(viewframes[name][step['step']],(0,row*(im_size[1])+((row+1)*PAD) ))

                    draw = ImageDraw.Draw(img)
                    y = im_size[1]*len(viewframes)+text_ofst_h
                    draw.text(( (0*im_size[0])+(PAD*1)+text_ofst_w , y ),fitness_text_format.format(step['ftns']),font_color,font=FONT)
                    draw.text(( (1*im_size[0])+(PAD*2)+text_ofst_w , y ),fitness_text_format.format(step['rnkg']['fit_locl']),font_color,font=FONT)
                    draw.text(( (2*im_size[0])+(PAD*3)+text_ofst_w , y ),fitness_text_format.format(step['rnkg']['fit_glbl']),font_color,font=FONT)
                except:
                    print("!!!!!!!!!! - not all steps recorded to animiation")
                    break
            else:
                raise NotImplementedError("layout style {} is not ready".format(LAYOUT_STYLE))

            if img: frames.append(img)


        print("saving mp4 file to {}".format(pth_mp4))
        writer = imageio.get_writer(pth_mp4, fps=frames_per_sec)
        for im in frames: writer.append_data(np.array(im))
        writer.close()


def process_log_data(pth_log, pth_unzip):

    with open(pth_log) as f: csv_head = next(csv.reader(f))
    viewnames = sorted([ s for s in csv_head if 'img_' in s ])
    genenames = sorted([ s for s in csv_head if 'gene_' in s ])

    steps = []
    with open(pth_log) as f:
        for row in csv.DictReader(f):
            step = {}
            step['step'] = int(row['step'])
            step['ftns'] = float(row['fitness'])
            step['imgs'] = {}
            step['gnes'] = []
            for viewname in viewnames: step['imgs'][viewname] = os.path.join(pth_unzip, row[viewname])
            for genename in genenames: step['gnes'].append(float(row[genename]))
            steps.append(step)
    return steps, viewnames

def rank_log_data(log_data):
    fits = [step['ftns'] for step in log_data]

    rankings = [{'idx_glbl':0, 'idx_locl':0, 'fit_glbl':fits[0], 'fit_locl':fits[0]}]
    for n in range(1,len(fits)):
        glb = sorted([(f,i) for i,f in enumerate(fits[:n])])
        lcl = sorted([(f,max(0,n-LOCAL_BEST_RANGE) + i) for i,f in enumerate(fits[max(0,n-LOCAL_BEST_RANGE):n])])
        rankings.append({'idx_glbl':glb[-1][1], 'idx_locl':lcl[-1][1], 'fit_glbl':glb[-1][0], 'fit_locl':lcl[-1][0]})

    for step, rnkg in zip(log_data,rankings):
        step['rnkg'] =rnkg

    return log_data

def viewport_frames(log_data, name, im_size):
    w,h = im_size[0],im_size[1]
    fitness_text_format = "{0:.4f}%"
    text_size = FONT.getsize(fitness_text_format.format(99))
    text_ofst_w = w/2.0 - text_size[0]/2.0
    text_ofst_h = text_size[1] * 1.5
    font_color = (50,50,50)

    frames = []
    for n in range(len(log_data)):
        ranks = log_data[n]['rnkg']

        try:
            img_crnt, fit_crnt = Image.open(log_data[n]['imgs'][name]), log_data[n]['ftns']
            img_glbl, fit_glbl = Image.open(log_data[ranks['idx_glbl']]['imgs'][name]), ranks['fit_glbl']
            img_locl, fit_locl = Image.open(log_data[ranks['idx_locl']]['imgs'][name]), ranks['fit_locl']
        except:
            print("!!!!!!!!!! - Could not open an image associated with step {}. Images missing from log, will do the best I can.".format(n))
            break

        img = False
        if LAYOUT_STYLE == 0:
            img = Image.new('RGB', ((w+PAD)*3, h), BK_COLOR)
            img.paste(img_crnt,(PAD,0))
            img.paste(img_locl,(w+PAD*2,0))
            img.paste(img_glbl,(w*2+PAD*3,0))

        elif LAYOUT_STYLE == 1:
            #img = Image.new('RGB', (w, h*3), (255,255,255))
            #img.paste(img_crnt,(0,0))
            #img.paste(img_locl,(0,h))
            #img.paste(img_glbl,(0,h*2))
            raise NotImplementedError("not done with vertical style")
        else:
            raise NotImplementedError("layout style {} is not ready".format(LAYOUT_STYLE))

        if img:
            frames.append(img)
        else:
            raise ValueError("what happened here? error in creating viewport frame image")

    return frames



if __name__ == '__main__' and __package__ is None:
    # ---- FEUTIL ---- #
    from os import sys, path
    sys.path.append(path.dirname(path.dirname(path.abspath(__file__)))) # add grandparent folder to the module search path
    import _fresh_eyes_script_utilities as feu # import fresh eyes fe_util
    # ---- FEUTIL ---- #


    # ---- ARGPARSE ---- #
    """Checks if a path is an actual file"""
    def is_file(pth):
        if not os.path.isfile(pth):
            npth = os.path.join(feu.PTH_TEMP,pth)
            if os.path.isfile(npth):
                return os.path.abspath(os.path.realpath(os.path.expanduser(npth)))
            else:
                msg = "Given path is not a full file path, and was not found in the PTH_TEMP.\n{}".format(pth)
                raise argparse.ArgumentTypeError(msg)
        else:
            return os.path.abspath(os.path.realpath(os.path.expanduser(pth)))

    parser = argparse.ArgumentParser()
    parser.add_argument('zip_path', help="path at which to find a ZIP file containing images and Opossum log file. Searches at PTH_TEMP defined in cfg file.", type=is_file)
    #parser.add_argument('destination_path', help="path at which to save resulting MP4", nargs='?', default=os.getcwd())
    args = parser.parse_args()
    # ---- ARGPARSE ---- #

    pth_zip = os.path.abspath(args.zip_path)
    pth_dst = os.path.dirname(pth_zip)

    #print(args)
    main(pth_zip, pth_dst)
