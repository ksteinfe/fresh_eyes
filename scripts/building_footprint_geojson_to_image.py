import os, io, json, shutil, urllib.request
from scipy import interpolate
from PIL import Image
import geojson # https://github.com/frewsxcv/python-geojson
import pysvg.structure, pysvg.builders, pysvg.text # https://github.com/alorence/pysvg-py3


bing_api_key = "AkoNFaO2lG5Gvb3LxAbpwB86XbhrtBMzZfpFzC-33GPW_QNLtzZ6zSMcOnvujs4p"

#polygon_to_svg((10,10,20,20), [(15,15),(20,20),(15,20)], (1000,1000) )

    
def main():
    
    fp = os.path.join('..','geojson','DistrictofColumbia.geojson')
    geoms = False
    with open(fp) as f: 
        gjdata = geojson.loads(f.read())
        if gjdata: geoms = [feature['geometry'] for feature in gjdata['features'] if 'geometry' in feature] # convert resulting dict to a simpler list of geometry dicts (stripping away properties and such)
        
    if geoms:
        print("Found {} geoms".format(len(geoms)))
        for g in geoms: 
            if g['type'] !="Polygon": print(g['type'])
        
        geoms = geoms[:2]
        
        for g in geoms:
            coords = list(geojson.utils.coords(g))
            coords = [(tup[1],tup[0]) for tup in coords]
            cent = [sum(y) / len(y) for y in zip(*geojson.utils.coords(g))]
            meta, img = BingLoader.get_img(cent,bing_api_key)
            # print(cent) # TODO: make sure cent and meta['ctr'] are identical
            # print(meta)
            print(meta['url'])
            print(meta['bbox'])
            print(coords)
            
            img.save("test.jpg")
            
            svgbuf = polygon_to_svg(meta['bbox'], coords, (1000,1000) )
            with open("test.svg", 'w') as fd:
              svgbuf.seek(0)
              shutil.copyfileobj(svgbuf, fd)
              fd.close()
        
        
class BingLoader():
    default_height = 1000
    default_width = 1000
    vert_crop = 20
    default_zoom = 18
    baseurl = "https://dev.virtualearth.net/REST/v1/Imagery/Map/Aerial/{lat},{lng}/{zoom}?mapMetadata={meta}&mapSize={w},{h}&key={key}"
    
      
    @staticmethod
    def get_img(latlng,key,zoom=default_zoom,w=default_width,h=default_height):
        reqdict = {
            'lat': latlng[1],
            'lng': latlng[0],
            'zoom': zoom,
            'meta': 1,
            'w': w,
            'h': h + BingLoader.vert_crop * 2,
            'key': key
        }
        meta = False
        try:
            with urllib.request.urlopen(BingLoader.baseurl.format(**reqdict)) as url:
                response = json.loads(url.read().decode())
                if 'statusCode' in response and response['statusCode'] == 200 and 'resourceSets' in response and len(response['resourceSets'])==1 and 'resources' in response['resourceSets'][0] and len(response['resourceSets'][0]['resources'])==1:
                    meta = response['resourceSets'][0]['resources'][0]
                    meta = {
                        'bbox':meta['bbox'],
                        'zoom':int(meta['zoom']),
                        'cntr': (float(meta['mapCenter']['coordinates'][0]),float(meta['mapCenter']['coordinates'][1]))
                    }
                else:
                    print("BingLoader.get_img() urllib.request returned a bad statusCode:\n{}".format(response))
                    return False
                    
        except urllib.error.HTTPError as e:
            print("BingLoader.get_img() urllib.request failed with the following message:\n{}".format(e))
            return False
        
        if not meta: return False
        
        reqdict['meta'] = 0
        meta['url'] = BingLoader.baseurl.format(**reqdict)
        
        with urllib.request.urlopen(meta['url']) as url:
            f = io.BytesIO(url.read())
        
        img = Image.open(f)
        img = img.crop((0,BingLoader.vert_crop,w,h-BingLoader.vert_crop))
        img.load()
        
        return meta, img
        
        #f = open('test.jpg', 'wb')
        #f.write(urllib.request.urlopen(BingLoader.baseurl.format(**reqdict)).read())
        #f.close()




def polygon_to_svg(bbox, coords, img_size):
    svg_document = pysvg.structure.Svg(width=img_size[0],height=img_size[1])
    shape_builder = pysvg.builders.ShapeBuilder()
    svg_document.addElement(shape_builder.createRect(0,0,img_size[0],img_size[1],stroke="none",fill="rgb(200,200,200)"))
    
    # TODO: IS FLIPPING and SWAPPING of coordinates correct?
    
    fx = interpolate.interp1d((bbox[0],bbox[2]),(img_size[0],0))  # note flip of coords for northern hemi
    fy = interpolate.interp1d((bbox[1],bbox[3]),(0,img_size[1]))    
    pts = " ".join(["{},{}".format(fy(tup[1]),fx(tup[0])) for tup in coords]) # note swapping of coords
    #print(pts)
    
    svg_document.addElement(shape_builder.createPolygon(pts))
    
    return io.StringIO(svg_document.wrap_xml(svg_document.getXML()))
    #print(svg_document.getXML())
    #svg_document.save("test-pysvg.svg")




    
if __name__ == "__main__":
    main()