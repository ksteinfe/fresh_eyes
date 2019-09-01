import os, json
from PIL import Image
dir_path = os.path.dirname(os.path.realpath(__file__))

if not os.path.exists('imgs'): os.makedirs('imgs') 

def process_file(filepath):
    dirname = os.path.splitext(os.path.split(filepath)[-1])[0]
    if not os.path.exists(os.path.join('imgs',dirname)): os.makedirs(os.path.join('imgs',dirname))    
    print("====== ", dirname)
    
    with open(filepath) as data_file:
        for n, img_data in enumerate(json.load(data_file)):
            img = Image.new('L',(60,30),128)
            pix = img.load()
            
            for c, col in enumerate(img_data):
                for r, val in enumerate(col):
                    #print(c,r)
                    val = (val / 10000)*256
                    #print (val)
                    pix[c,r] = int(val)
            
            img = img.resize((60, 60))
            img.save(os.path.join('imgs',dirname,"%03d" %n+".png"))

for root, dirs, filenames in os.walk(dir_path):
    for filename in filenames:
        if ".json" == os.path.splitext(filename)[-1].lower():
            process_file(os.path.join(root, filename))
