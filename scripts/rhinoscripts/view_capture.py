import rhinoscriptsyntax as rs
import Rhino
import scriptcontext
import System.Drawing
import os

def main():
    set_active_view("Perspective")
    view = rs.CurrentView()
    set_disp_mode("Arctic")
    
    rs.ViewProjection(view,2)
    rs.ViewCameraTarget(view,(-1,-1,0.5),(0,0,0))
    
    rs.ViewCameraLens(view,25)
    rs.ZoomExtents(view)
    #rs.ViewCameraLens(view,25)
    
    #basepath = "C:\\Users\\ksteinfe\\Desktop\\TEMP"
    basepath = "G:\\TEMP"
    #capture_view_antialias(os.path.join(basepath,"anti 1.png"), (200,200) )
    capture_view_antialias(os.path.join(basepath,"anti 2.png"), (200,200), 4.0 )
    #capture_view(os.path.join(basepath,"reg.png"), (200,200) )

#def fetch(
#    obj = rs.GetObject("Pick any object")

#def patch(curve)

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