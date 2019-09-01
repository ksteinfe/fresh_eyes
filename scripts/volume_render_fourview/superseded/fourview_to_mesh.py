import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage import measure
from stl import mesh # pip install numpy-stl
from PIL import Image

import mayavi # https://docs.enthought.com/mayavi/mayavi/installation.html
from mayavi import mlab
from pyface.api import GUI
from tvtk.util.gradient_editor import GradientTable
    
def main():
    #return
    """
    prepare image
    """
    img_base = Image.open("sample_01.png").convert('L') # converts to greyscale
    if img_base.size[0] != img_base.size[1]: raise ValueError("This image isn't square: {}".format(img_base.size))
    if img_base.size[0] != img_base.size[1]: raise ValueError("This image isn't square: {}".format(img_base.size))
    if img_base.size[0]%2!=0 : raise ValueError("This image isn't divisible into quadrants: {}".format(img_base.size))
    dim = int(img_base.size[0]/2)
    print("dim: {}".format(dim))
    
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
    drill_force = 0.5
    for img, face_idx in zip(img_tiles, face_idxs):
        px = img.load()
        crdvals = [(x,y, float(px[x,y]) / 255.0 ) for x in range(dim) for y in range(dim)]
        for x,y,val in crdvals:
            depth = 1-val # set depth 
            y = dim-1-y # need to flip y-axis to match bottom-left style of voxel grid
            vx.drill_at(face_idx, (x,y), depth, drill_force)
    
    
    
    """
    vx.drill_at(1, (0,0), 1.0, 0.1)
    vx.drill_at(1, (0,0), 0.5, 1.0)    
    arr = [0.]* vx.dim
    arr[0] = -1.0)
    for idx in [1,2,3,-1,-2,-3]:
        vx.sum_at(idx,(0,0),arr)
        vx.sum_at(idx,(1,0),arr)
        vx.sum_at(idx,(2,0),arr)
        vx.sum_at(idx,(2,1),arr)
        vx.sum_at(idx,(2,2),arr)
    
    """
    #print(vx.arr)
    #print(vx.arr.shape)
    
    #vx.plot_as_voxl()
    vx.plot_as_mlab_volume()
        
    
    
    """
    vx.plot_as_mesh(0.5, 4, do_pad=True)
    for lvl in [0.1,0.5,0.8]:
        vx.plot_as_stl(lvl, do_pad=True)
    """
    
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
        
        
    def plot_as_mlab_volume(self):
        #mlab.options.background_color = (1.0,1.0,1.0)
        mlab.options.offscreen = True
        
        def load_grad(v, grad_filepath):
            gt = GradientTable(300)
            gt.load(grad_filepath)
            gt.store_to_vtk_volume_prop(v.volume_property, (0.0, 1.0))
        
        fig = mlab.figure(1, bgcolor=(1, 1, 1), size=(350, 350))
        mlab.clf()
        force_render(fig)
        min, max = self.arr.min(), self.arr.max()
        min, max = -1,0
        sf = self.to_mlab_scalar_field(1.0,1.5,0.6) # pass in x,y,z scale factor
        vol = mlab.pipeline.volume(sf, vmin=min, vmax=max)
        load_grad(vol, 'ksteinfe.grad')
        
        force_render(fig)
        
        
        frame_count = 30
        for n in range(frame_count):
            # view(azimuth=None, elevation=None, distance=None, focalpoint=None, roll=None, reset_roll=True, figure=None)
            elev = np.interp(n, [0,frame_count/2,frame_count], [90,20,90])
            mlab.view(320,elev)
            mayavi.mlab.savefig("{}.jpg".format(n))
        mlab.options.offscreen = False
        
        #mlab.show()
        

        
    def _OLD_plot_as_mlab_volume(self):
        mlab.options.background_color = (1.0,1.0,1.0)
        #mlab.options.offscreen = True
           
        sf = self.to_mlab_scalar_field(1.0,1.5,0.6) # pass in x,y,z scale factor
        vol = mlab.pipeline.volume(sf)
        #print(vol.actors[0].property.__dict__)
        
        #superseded_muck_with_lights(vol)
        # load volume properties from file instead
        from mayavi.modules.volume import Volume
        from tvtk.util.gradient_editor import GradientTable
        gt = GradientTable(300)
        gt.load('ksteinfe.grad')
        gt.store_to_vtk_volume_prop(vol.volume_property, (0.0, 1.0))
                
        fig = mlab.gcf()
        fig.scene.camera.zoom(1.5)
        fig.scene.render()
                
        #mayavi.mlab.draw()
        mlab.show()
        mayavi.mlab.savefig("outy.jpg")
        
        
        @mlab.animate(delay=1000, ui=False)
        def anim():
            f = mlab.gcf()
            while 1:
                f.scene.camera.azimuth(100)
                f.scene.render()
                yield

        a = anim()
        
        
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



def force_render(figure):
    """Ensure plots are updated before properties are used"""
    _gui = GUI()
    orig_val = _gui.busy
    _gui.set_busy(busy=True)
    _gui.process_events()
    figure.render()
    mlab.draw(figure=figure)
    _gui.set_busy(busy=orig_val)
    _gui.process_events()

        
def superseded_muck_with_lights(vol):
    # Changing the ctf (color) / otf (opacity)
    #        https://docs.enthought.com/mayavi/mayavi/auto/mlab_pipeline_other_functions.html#volume
    from tvtk.util.ctf import ColorTransferFunction
    ctf = ColorTransferFunction()
    #ctf.add_rgb_point(0.0, r, g, b)  # r, g, and b are float  between 0 and 1
    ctf.add_rgb_point(0.0, 0.0, 0.0, 0.0) # RGB
    ctf.add_hsv_point(1.0, 0.0, 0.0, 1.0) # HSV (crashes if both of these aren't called)
    vol._volume_property.set_color(ctf)
    vol._ctf = ctf
    vol.update_ctf = True
    
    from tvtk.util.ctf import PiecewiseFunction
    otf = PiecewiseFunction()
    otf.add_point(0.0, 0.20)
    otf.add_point(0.8, 0.90)
    otf.add_point(1.0, 0.99)
    vol._otf = otf
    vol._volume_property.set_scalar_opacity(otf)
        
if __name__ == "__main__":
    main()