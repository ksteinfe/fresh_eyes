

def save_temp_image(im):
    #TODO: is the PNG format an issue here?
    if not os.path.exists(PTH_TMP): os.makedirs(PTH_TMP)

    pth_im = os.path.join(PTH_TMP,"{}.png".format(str(uuid.uuid4())))
    im.save(pth_im)
    return(pth_im)

def req_string_to_image(s):
    try:
        data = base64.decodestring(bytes(s, 'utf-8'))
        im = Image.open(io.BytesIO(data))
        return im
    except:
        return False

def chan_count_to_mode(nc):
    if nc==1: return "L"
    if nc==3: return "RGB"
    if nc==4: return "RGBA"
    print("Encountered an unexpected number of channels ({})".format(nc))
    return False
