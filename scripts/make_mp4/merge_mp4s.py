import imageio
import glob, os, shutil
#from PIL import Image, ImageSequence, ImageFont, ImageDraw
from zipfile import ZipFile

"""
VARIABLES
"""

# takes the first frame from the first file, the second from the second, etc.
# cycles back to the first frame as needed until the files are exhausted.
# only works if the MP4s are somehow equivalent
do_collate = True 
collate_ratio = 3

img_filepath = r"C:\Users\ksteinfe\Desktop\TEMP\walk_01\3d"
output_directory = r"C:\Users\ksteinfe\Desktop\TEMP"
img_extension = ".mp4"

output_filename = "OUT"
frames_per_sec = 24

src_files = [os.path.join(img_filepath,file) for file in os.listdir(img_filepath) if file.endswith(img_extension)]
out_filepath = os.path.join(output_directory,'{}.mp4'.format(output_filename))


writer = imageio.get_writer(out_filepath, fps=frames_per_sec)

if not do_collate:
    for mp4 in src_files:
        reader = imageio.get_reader(mp4)
        for i, im in enumerate(reader):
            writer.append_data(im)
else:
    datas = []
    for m, mp4 in enumerate(src_files):
        reader = imageio.get_reader(mp4)
        frm_idx = int( (m/collate_ratio) % reader.get_length()  )
        print("file {} of {} at frame {}".format(m,len(src_files),frm_idx))
        datas.append(reader.get_data(frm_idx))            
         
    for d in datas: writer.append_data(d)
         
writer.close()
