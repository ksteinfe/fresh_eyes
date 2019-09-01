
import rhinoscriptsyntax as rs
import Rhino
import scriptcontext
import System.Drawing
import os

def main():
    #basepath = "C:\\Users\\ksteinfe\\Desktop\\TEMP" #Kyle's Desktop
    basepath = "G:\\TEMP" #Matt's Desktop
    #basepath = "C:\\Users\\Matt\\Desktop\\Temp" #Matt's Laptop

    max_flrs = 99 # maximum number of folders to open
    max_fils = 99 # maximum number of files to open in each folder

    folder_tic = time.clock()
    fdr_cnt = 0
    for root, dirs, files in walklevel(basepath):
        
        print ("{}\t {}".format(fdr_cnt,root))
        #if (root == basepath): continue
        
        fil_cnt = 0
        for full_filename in files:
            filename, file_extension = os.path.splitext(full_filename)
            if file_extension != ".3dm": continue

            file_tic = time.clock()
            filepath = os.path.join(root, full_filename)
            rs.DocumentModified(False)
            rs.Command('_-Open {} _Enter'.format('"'+filepath+'"'))
            t = round(time.clock()-file_tic)
            print(filename+"\ttime:\t"+str(t))
            
            #massing color
            rs.CurrentLayer("MASSING")
            m=235#patch color
            rs.LayerColor("MASSING",(m,m,m))

            #patch openings
            p=200#patch color
            patch_opening("DOOR",(p,p,p))#set color here
            patch_opening("WINDOW",(p,p,p))#set color here
            rs.LayerPrintWidth("SITE", width=0.4)#set print width here

            #setting view & site lines
            rs.CurrentLayer("SITE")
            s=120#patch color
            rs.LayerColor("SITE",(s,s,s))
            rs.Command("SelText Delete SelPts Delete") #delete text for zoom_viewer to work...
            zoom_viewer("SITE",(1,-1.5,1),(0,0,0))#set focus layer,camera, target
            zoom_out()
            zoom_out()
            zoom_out()
            
            #add ground plane
            g=255#patch color
            rs.AddLayer("GROUND_PLANE",(g,g,g))
            rs.CurrentLayer("GROUND_PLANE")
            rs.Command("plane c 0 1000 enter ")#create ground plane for site
            rs.Command("PrintDisplay"+"s"+" _-Enter"+"o"+" _-Enter"+" _-Enter")#ensures lineweights are displaying
            capture_view_antialias(os.path.join(basepath,filename+"_antialias.png"), (800,800) )#changeimagesize

            #update
            fil_cnt+=1
            if fil_cnt > max_fils: break

        fdr_cnt+=1
        if fdr_cnt > max_flrs: break
    
    t = round(time.clock()-folder_tic)
    print("TOTAL\ttime:\t"+str(t))


def zoom_viewer(layername,camera,focus):
        rs.CurrentLayer(layername)
        rhobjs = scriptcontext.doc.Objects.FindByLayer(layername)
        set_active_view("Perspective")
        view = rs.CurrentView()
        set_disp_mode("Arctic")
        rs.ViewProjection(view,1)
        rs.ViewCameraTarget(view,camera,focus)#adjust view
        rs.ViewCameraLens(view,30)
        rhobjs = scriptcontext.doc.Objects.FindByLayer(layername)
        rs.SelectObject(rhobjs[0])
        rs.ZoomSelected()
        rs.UnselectAllObjects()

def zoom_out():
        rs.Command("Zoom o ")#ZoomOut

def patch_site(layername,color):
    rs.CurrentLayer(layername)
    rhobjs = scriptcontext.doc.Objects.FindByLayer(layername)
    surface=rs.AddPlanarSrf(rhobjs[0])
    material_index = rs.AddMaterialToObject(surface)# add new material and get its index
    rs.MaterialColor(material_index, color)# assign material color
    rs.LayerColor(layername,(0,0,0))
    try:
        return surface
    except:
        return False

def patch_opening(layername,color):
    rs.CurrentLayer(layername)
    rs.LayerColor(layername,color)
    crvs = scriptcontext.doc.Objects.FindByLayer(layername)
    for crv in crvs:
        rs.SelectObject(crv)
        rs.Command("extrudecrv solid=yes bothsides=yes 0.05 delete")

def set_active_view(viewportName):
    RhinoDocument = Rhino.RhinoDoc.ActiveDoc
    view = RhinoDocument.Views.Find(viewportName, False)
    if view is None: return
    RhinoDocument.Views.ActiveView = view
    return view # returns RhinoCommon view. for Rhinoscript, use rs.CurrentView()


# scale_fac is capture to save size ratio
def capture_view_antialias(filePath, save_size=1.0, scale_fac = 2.0 ): 
    RhinoDocument = Rhino.RhinoDoc.ActiveDoc
    view = RhinoDocument.Views.ActiveView    
    vp = view.ActiveViewport
    
    try:
        capture_size = System.Drawing.Size(save_size[0]*scale_fac,save_size[1]*scale_fac)
    except:
        save_size = vp.Size.Width*save_size,vp.Size.Height*save_size
        capture_size = System.Drawing.Size(save_size[0]*scale_fac,save_size[1]*scale_fac)
    
    capture = view.CaptureToBitmap( capture_size )
    capture = resize_bitmap(capture,save_size)
    capture.Save(filePath);

def capture_view(filePath, save_size=1.0):
    RhinoDocument = Rhino.RhinoDoc.ActiveDoc
    view = RhinoDocument.Views.ActiveView    
    vp = view.ActiveViewport
    
    try:
        capture_size = System.Drawing.Size(save_size[0],save_size[1])
    except:
        save_size = vp.Size.Width*save_size,vp.Size.Height*save_size
        capture_size = System.Drawing.Size(save_size[0],save_size[1])
    
    capture = view.CaptureToBitmap( capture_size )

    capture.Save(filePath);


def resize_bitmap(src_img,size):
    dest_rect = System.Drawing.Rectangle(0,0,size[0],size[1])
    dest_img = System.Drawing.Bitmap(size[0],size[1])
    dest_img.SetResolution(src_img.HorizontalResolution, src_img.VerticalResolution)
    
    with System.Drawing.Graphics.FromImage(dest_img) as g:
        g.CompositingMode = System.Drawing.Drawing2D.CompositingMode.SourceCopy
        g.CompositingQuality = System.Drawing.Drawing2D.CompositingQuality.HighQuality
        g.InterpolationMode = System.Drawing.Drawing2D.InterpolationMode.HighQualityBicubic
        g.SmoothingMode = System.Drawing.Drawing2D.SmoothingMode.HighQuality
        g.PixelOffsetMode = System.Drawing.Drawing2D.PixelOffsetMode.HighQuality
        
        with System.Drawing.Imaging.ImageAttributes() as wrap_mode:
            wrap_mode.SetWrapMode(System.Drawing.Drawing2D.WrapMode.TileFlipXY)
            g.DrawImage(src_img, dest_rect, 0,0, src_img.Width, src_img.Height, System.Drawing.GraphicsUnit.Pixel, wrap_mode)
    return dest_img


def set_disp_mode(modename):
    desc = Rhino.Display.DisplayModeDescription.FindByName(modename)
    if desc: 
        scriptcontext.doc.Views.ActiveView.ActiveViewport.DisplayMode = desc
        #scriptcontext.doc.Views.Redraw()

import rhinoscriptsyntax as rs
import os, time

def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir), "Directory not found:\t{}".format(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]
            

if __name__ == "__main__":
    # execute only if run as a script
    main()