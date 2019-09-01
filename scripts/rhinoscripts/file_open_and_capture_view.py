import rhinoscriptsyntax as rs
import Rhino
import scriptcontext
import System.Drawing
import os, time


#src_path = "C:\\Users\\ksteinfe\\Desktop\\TEST"
src_path = r"C:\Users\kstei\Desktop\Sebastian"
tar_path = r"C:\Users\kstei\Desktop\TEMP SEB"
disp_mode = "Arctic"
cam_pos = (-1,-1,1)
tar_pos = (0,0,0)
lens_len = 100
image_size = (400,400)
    
def main():
    
    max_flrs = 9999 # maximum number of folders to open
    max_fils = 9999 # maximum number of files to open in each folder
    
    folder_tic = time.clock()
    fdr_cnt = 0
    for root, dirs, files in walklevel(src_path):
        
        print ("{}\t {}".format(fdr_cnt,root))
        #if (root == src_path): continue
        
        fil_cnt = 0
        for full_filename in files:
            filename, file_extension = os.path.splitext(full_filename)
            if file_extension != ".3dm": continue
            
            file_tic = time.clock()
            filepath = os.path.join(root, full_filename)
            rs.DocumentModified(False)
            rs.Command('_-Open {} _Enter'.format('"'+filepath+'"'))
            
            pln = rs.PlaneFromPoints( (100,0,0), (0,100,0), (100,100,0))
            rs.AddRectangle(pln,100,100)
            
            set_active_view("Origin_SW_ISO")
            view = rs.CurrentView()
            set_disp_mode(disp_mode)
            rs.Redraw()
            """
            rs.ViewProjection(view,2)
            rs.ViewCameraTarget(view,cam_pos,tar_pos)
            
            rs.ViewCameraLens(view,lens_len)
            rs.ZoomExtents(view)
            #rs.ViewCameraLens(view,25)
            """
            capture_view_antialias(os.path.join(tar_path,"{}.png".format(filename)), image_size )
            
            
            
            
            t = round(time.clock()-file_tic)
            print(filename+"\ttime:\t"+str(t))
            
            fil_cnt+=1
            if fil_cnt > max_fils: break
        
        fdr_cnt+=1
        if fdr_cnt > max_flrs: break
    
    t = round(time.clock()-folder_tic)
    print("TOTAL\ttime:\t"+str(t))


def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir), "Directory not found:\t{}".format(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]
            


def set_active_view(viewportName):
    RhinoDocument = Rhino.RhinoDoc.ActiveDoc
    view = RhinoDocument.Views.Find(viewportName, False)
    if view is None: return
    RhinoDocument.Views.ActiveView = view
    return view # returns RhinoCommon view. for Rhinoscript, use rs.CurrentView()

def capture_view_antialias(filePath, save_size=1.0, scale_fac = 2.0 ): # scale_fac is capture to save size ratio
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

if __name__ == "__main__":
    # execute only if run as a script
    main()