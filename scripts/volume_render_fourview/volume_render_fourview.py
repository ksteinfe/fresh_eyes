import os, imageio, math
#import matplotlib.pyplot as plt
import numpy as np
#from mpl_toolkits.mplot3d.art3d import Poly3DCollection
#from skimage import measure
#from stl import mesh # pip install numpy-stl
from PIL import Image

import mayavi # https://docs.enthought.com/mayavi/mayavi/installation.html
from mayavi import mlab
from pyface.api import GUI
from tvtk.util.gradient_editor import GradientTable

src_directory = r"C:\Users\ksteinfe\Desktop\TEMP"
output_directory = r"C:\Users\ksteinfe\Desktop\TEMP"
img_extensions = ["png","jpg"]

DO_RENDER_ANIMATION = False
DO_MERGE_ANIMATIONS = False

IMG_SIZE = (480,480)
FPS = 24
TRNTBL_ELEV_KEYVALS = [90,30,90]
TRNTBL_AZIM_KEYVALS = [0,180,360]

    
def main():
    #return
    imgpths = [os.path.join(src_directory,file) for file in os.listdir(src_directory) if any( [ file.endswith(ext) for ext in img_extensions]) ]
    #imgpths = ["sample_01.png","sample_02.png","sample_03.png"]
    
    #imgpths = imgpths[:3]
    
    if DO_RENDER_ANIMATION:
        mlab.options.offscreen = True 
        if DO_MERGE_ANIMATIONS:
            # makes a single MP4 that shows all fourview source images
            fig_files, src_files = [], []
            frames_per_img = 10
            frames_per_turn = 192
            trntbl_range = [0,frames_per_turn/2,frames_per_turn]
            f = 0
            for i, imgpth in enumerate(imgpths):
                print("file {} of {} at frame {} is {}".format(i,len(imgpths),f,os.path.splitext(os.path.basename(imgpth))[0]))
                vx = vgrid_from_image(imgpth)
                fig = plot_vgrid_vol_to_figure(vx, IMG_SIZE)
                
                for n in range(frames_per_img):
                    t = f%frames_per_turn
                    elev = np.interp(t,trntbl_range, TRNTBL_ELEV_KEYVALS)
                    azim = np.interp(t,trntbl_range, TRNTBL_AZIM_KEYVALS)
                    mlab.view(azim,elev)
                    figpth = os.path.join(output_directory, "{}.jpg".format(f))
                    mayavi.mlab.savefig(figpth)
                    fig_files.append(figpth)
                    src_files.append(imgpth)
                    f += 1
                    
                mayavi.mlab.close(all=True)
                #print("{} scenes are open".format(len(mayavi.mlab.get_engine().scenes)))
            
            # save fig mp4
            out_filepath = os.path.join(output_directory,'{}.mp4'.format("merged_fig"))
            writer = imageio.get_writer(out_filepath, fps=FPS)
            for im in fig_files: writer.append_data(imageio.imread(im))
            writer.close()
            for f in fig_files: os.remove(f)
            
            # save src mp4
            out_filepath = os.path.join(output_directory,'{}.mp4'.format("merged_src"))
            writer = imageio.get_writer(out_filepath, fps=FPS)
            for im in src_files: writer.append_data(imageio.imread(im))
            writer.close()
            
        else:
            # makes an MP4 for each fourview source image
            for i, imgpth in enumerate(imgpths):
                print("file {} of {}".format(i,len(imgpths)))
                imgname = os.path.splitext(os.path.basename(imgpth))[0]
                vx = vgrid_from_image(imgpth)
                fig = plot_vgrid_vol_to_figure(vx, IMG_SIZE)
                animate_single_fig(fig,imgname)
            
        mlab.options.offscreen = False
        
    else:
        print("plotting single tile: {}".format(os.path.splitext(os.path.basename(imgpths[0]))[0]))
        vx = vgrid_from_image(imgpths[0])
        print("arr bounds: [{}->{}]".format(vx.arr.min(),vx.arr.max()))
        fig = plot_vgrid_vol_to_figure(vx, IMG_SIZE)
        mlab.show()

def vgrid_from_image(imgpth, drill_force = 0.25):        
    """
    prepare image
    """
    img_base = Image.open(imgpth).convert('L') # converts to greyscale
    if img_base.size[0] != img_base.size[1]: raise ValueError("This image isn't square: {}".format(img_base.size))
    if img_base.size[0] != img_base.size[1]: raise ValueError("This image isn't square: {}".format(img_base.size))
    if img_base.size[0]%2!=0 : raise ValueError("This image isn't divisible into quadrants: {}".format(img_base.size))
    dim = int(img_base.size[0]/2)
    #print("dim: {}".format(dim))
    
    crops = [(0,0,dim,dim), (dim,0,dim*2,dim), (0,dim,dim,dim*2), (dim,dim,dim*2,dim*2)] # top, front, left?, right?
    face_idxs = [1,2,-3,3] # voxel grid face indices that correspond to images
    img_tiles = [img_base.crop(crp) for crp in crops]
    #img_tiles[0].show()
    
    """
    prepare voxel grid
    """
    vx = VGrid(dim)
    vx.level = 0.6
    
    """
    walk
    """
    for img, face_idx in zip(img_tiles, face_idxs):
        px = img.load()
        crdvals = [(x,y, float(px[x,y]) / 255.0 ) for x in range(dim) for y in range(dim)]
        for x,y,val in crdvals:
            depth = 1-val # set depth 
            y = dim-1-y # need to flip y-axis to match bottom-left style of voxel grid
            vx.drill_at(face_idx, (x,y), depth, drill_force) # todo: muck around with depth to get views to line up?
    
    return vx
        
        
def animate_single_fig(fig,name,frame_count=48):
    fig_files = []
    for n in range(frame_count):
        # view(azimuth=None, elevation=None, distance=None, focalpoint=None, roll=None, reset_roll=True, figure=None)
        elev = np.interp(n, [0,frame_count/2,frame_count], TRNTBL_ELEV_KEYVALS)
        azim = np.interp(n, [0,frame_count/2,frame_count], TRNTBL_AZIM_KEYVALS)
        mlab.view(azim,elev)
        imgpth = os.path.join(output_directory, "{}_{}.jpg".format(name,n))
        mayavi.mlab.savefig(imgpth)
        fig_files.append(imgpth)
    
    out_filepath = os.path.join(output_directory,'{}.mp4'.format(name))
    writer = imageio.get_writer(out_filepath, fps=FPS)
    for im in fig_files: writer.append_data(imageio.imread(im))
    writer.close()
    
    for f in fig_files: os.remove(f)
    
        
class VGrid():
    FIGSIZE = (5, 5)
    
    def __init__(self, dim):
        self.dim = dim
        self.arr = np.ones( (self.dim,self.dim,self.dim) )
        #self.arr = np.random.uniform( size=(self.dim,self.dim,self.dim) )
        #self.arr[0][0][0] = 0.0
    
    def assign_xy(self,crd,vals): self.arr[crd[0],crd[1],:] = vals
    def assign_xz(self,crd,vals): self.arr[crd[0],:,crd[1]] = vals
    def assign_yz(self,crd,vals): self.arr[:,crd[0],crd[1]] = vals
    def sum_xy(self,crd,vals): self.arr[crd[0],crd[1],:] += vals
    def sum_xz(self,crd,vals): self.arr[crd[0],:,crd[1]] += vals
    def sum_yz(self,crd,vals): self.arr[:,crd[0],crd[1]] += vals
    
    def sum_at(self,face_idx,crd,vals):
        # crds are the coordinates of the "stack" of voxels to transform
        # vals is a single value or list of values to be summed with the existing values in the stack. if a list, should be the proper length (same as self.dim). the first given value is applied to the nearest voxel when viewed from the selected face. 
        # face_idx is the cubic face on which to apply the coordinates to find the stack to perform summation
        # primary sides are 1 = XY(top); 2 = XZ(front); 3 = YZ(right); 
        # secondary sides are -1 = XY(bottom); -2 = XZ(back); -3 = YZ(left); 
        # secondary sides require reversal of crds
        valid_idxs = [1,2,3,-1,-2,-3]
        val_reversed_face_idxs = [1,-2,3]
        crd_reversed_face_idxs = [-1,-2,-3]
        if face_idx not in valid_idxs: raise ValueError("I got face_idx={}, but should be one of the following: {}".format(face_idx, valid_idxs))
        
        if len(vals)>1:
            if face_idx in val_reversed_face_idxs: vals.reverse()
        
        if face_idx in crd_reversed_face_idxs: 
            crd = ( self.dim-1 - crd[0], crd[1] )
        
        if abs(face_idx)==1:
            self.arr[crd[0],crd[1],:] += vals
            return True
        elif abs(face_idx)==2:
            self.arr[crd[0],:,crd[1]] += vals
            return True
        elif abs(face_idx)==3:
            self.arr[:,crd[0],crd[1]] += vals
            return True
        raise ValueError("This code should be unreachable")
        return False
        
        
    def drill_at(self,face_idx,crd,depth,force=1.0):
        if depth <= 0.0: return
        # depth is normalized, scaled to self.dim
        depth = int( (self.dim-1) * max(min(depth, 1.0), 0.0) )
        #print("drilling on face {} at crd {} to depth {}".format(face_idx, crd, depth))
        
        vals = [-force if n <= depth else 0.0 for n in range(self.dim)]
        self.sum_at(face_idx,crd,vals)
        
        
    def plot_as_voxl(self):
        def f(x):
            if x>0: return 1
            return 0
        vfunc = np.vectorize(f)
        nparr = vfunc(self.arr)
        
        fig = plt.figure(figsize=VGrid.FIGSIZE)
        ax = fig.add_subplot(111, projection='3d')
        #ax = fig.gca(projection='3d')
        ax.voxels(nparr, edgecolor='k')
        ax.set_xlabel("x-axis")
        ax.set_ylabel("y-axis")
        ax.set_zlabel("z-axis")
        
        plt.plot([0,self.dim,self.dim,0,0,self.dim,self.dim,0], [0,0,self.dim,self.dim,0,0,self.dim,self.dim], [0,0,0,0,self.dim,self.dim,self.dim,self.dim], 'ro', markersize=2)
        
        plt.show()
        
        
    def plot_as_mesh(self, level, step_size=1, do_pad=True):
        nparr = self.arr
        if do_pad: nparr = np.pad(nparr,2,'constant',constant_values=0) # pad boundary
        
        fig = plt.figure(figsize=VGrid.FIGSIZE)
        ax = fig.add_subplot(111, projection='3d')
        verts, faces = self.to_mesh(nparr, level, step_size=step_size)
        ax.add_collection3d(Poly3DCollection(verts[faces]))
        ax.set_xlim(0, self.dim) 
        ax.set_ylim(0, self.dim) 
        ax.set_zlim(0, self.dim) 
        ax.set_xlabel("x-axis")
        ax.set_ylabel("y-axis")
        ax.set_zlabel("z-axis")
        
        plt.plot([0,self.dim,self.dim,0,0,self.dim,self.dim,0], [0,0,self.dim,self.dim,0,0,self.dim,self.dim], [0,0,0,0,self.dim,self.dim,self.dim,self.dim], 'ro', markersize=2)

        plt.show()
        
    def plot_as_stl(self, level, step_size=1, do_pad=True):
        nparr = self.arr
        if do_pad: nparr = np.pad(nparr,2,'constant',constant_values=0) # pad boundary
        verts, faces = self.to_mesh(nparr, level, step_size=step_size)
        lvlstr = "{:06.3F}".format(level)
        VGrid.write_mesh_to_stl(verts, faces,"out_{}".format(lvlstr.replace(".","-")))
        
        
    def to_meshgrid(self, sx=1.0, sy=1.0, sz=1.0): # note that size of plotted volume can be changed here
        nx,ny,nz = (self.dim, self.dim, self.dim)
        xv, yv, zv = np.linspace(0,sx,nx), np.linspace(0,sy,ny), np.linspace(0,sz,nz)
        xv, yv, zv = np.meshgrid(xv, yv, zv, indexing='ij')
        return xv, yv, zv
        
    def to_mlab_scalar_field(self, sx=1.0, sy=1.0, sz=1.0):
        xv, yv, zv = self.to_meshgrid(sx,sy,sz)        
        sf = mlab.pipeline.scalar_field(xv, yv, zv, self.arr)
        return sf
        
    def plot_as_mlab_contour3d(self):
        xv, yv, zv = self.to_meshgrid()        
        mlab.contour3d(xv, yv, zv, self.arr)
        mlab.show()
        
        
    @staticmethod
    def to_mesh(nparr, level, step_size=1):
        verts, faces, normals, values = measure.marching_cubes_lewiner(nparr, level, step_size=step_size)
        return verts, faces        
        
    @staticmethod
    def write_mesh_to_stl(verts, faces, filepath):
        stl = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                stl.vectors[i][j] = verts[f[j],:]
        
        stl.save(filepath+'.stl')

    

def plot_vgrid_vol_to_figure(vg,img_size):
    #fig = mlab.figure(1, bgcolor=(1, 1, 1), size=(350, 350))
    fig = mlab.figure(bgcolor=(1, 1, 1), size=img_size)
    mlab.clf() # clear current figure
    mlab_force_render(fig)
    min, max = vg.arr.min(), vg.arr.max()
    min, max = 0,1
    sf = vg.to_mlab_scalar_field(1.0,1.5,0.6) # pass in x,y,z scale factor
    vol = mlab.pipeline.volume(sf, vmin=min, vmax=max)
    mlab_load_grad(vol, 'ksteinfe_color_02.grad')
    mlab_force_render(fig)
    return fig

def mlab_load_grad(v, grad_filepath):
    gt = GradientTable(300)
    gt.load(grad_filepath)
    gt.store_to_vtk_volume_prop(v.volume_property, (0.0, 1.0))
        
def mlab_force_render(figure):
    """Ensure plots are updated before properties are used"""
    _gui = GUI()
    orig_val = _gui.busy
    _gui.set_busy(busy=True)
    _gui.process_events()
    figure.render()
    mlab.draw(figure=figure)
    _gui.set_busy(busy=orig_val)
    _gui.process_events()


        
if __name__ == "__main__":
    main()