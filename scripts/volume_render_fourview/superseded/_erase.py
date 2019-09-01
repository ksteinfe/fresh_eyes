import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
from skimage import measure
from stl import mesh # pip install numpy-stl
    
def main():
    vx = VX()
    vx.level = 0.6
    
    vx.sum_yz( (1,1), [-0.8,-0.8,-0.8,-0.8,-0.8]) # sums given values to a "core sample" from yz side
    vx.sum_yz( (1,2), [-0.4,-0.4,-0.4,-0.1,0.0]) # sums given values to a "core sample" from yz side
    vx.sum_xy( (2,2), -1.0) # sums given values to a "core sample" from yz side
    
    print(vx.arr)
    print(vx.arr.shape)
    #vx.plot_voxl()
    vx.plot_mesh(1) # this method call pads the VX to close the form
    
    
class VX():
    DIM = 5
    FIGSIZE = (5, 5)
    
    def __init__(self):
        self.level = 0.5
        self.arr = np.ones( (VX.DIM,VX.DIM,VX.DIM) )
        #self.arr = np.random.uniform( size=(VX.DIM,VX.DIM,VX.DIM) )
        self.arr[0][0][0] = 0.0
    
    def assign_xy(self,crd,vals): self.arr[crd[0],crd[1],:] = vals
    def assign_xz(self,crd,vals): self.arr[crd[0],:,crd[1]] = vals
    def assign_yz(self,crd,vals): self.arr[:,crd[0],crd[1]] = vals
    
    def sum_xy(self,crd,vals): self.arr[crd[0],crd[1],:] += vals
    def sum_xz(self,crd,vals): self.arr[crd[0],:,crd[1]] += vals
    def sum_yz(self,crd,vals): self.arr[:,crd[0],crd[1]] += vals
    
    def to_mesh(self, step_size=1):
        verts, faces, normals, values = measure.marching_cubes_lewiner(self.arr, self.level, step_size=step_size)
        return verts, faces
        
    def plot_voxl(self):
        fig = plt.figure(figsize=VX.FIGSIZE)
        ax = fig.add_subplot(111, projection='3d')
        #ax = fig.gca(projection='3d')
        ax.voxels(self.arr, edgecolor='k')
        ax.set_xlabel("x-axis")
        ax.set_ylabel("y-axis")
        ax.set_zlabel("z-axis")
        plt.show()
        
    def save_stl(self):
        verts, faces = self.to_mesh()
        stl = mesh.Mesh(np.zeros(faces.shape[0], dtype=mesh.Mesh.dtype))
        for i, f in enumerate(faces):
            for j in range(3):
                stl.vectors[i][j] = verts[f[j],:]
        
        stl.save('out.stl')
        
    def plot_mesh(self, step_size=2):
        print("======== PLOTTING ")
        # add dimension 
        #self.arr = np.insert( self.arr, [0,-1], np.zeros( (VX.DIM,VX.DIM) ), axis=0 )
        #self.arr = np.concatenate( (self.arr, np.zeros( (0,VX.DIM,VX.DIM) )), axis=0)
        self.arr = np.pad(self.arr,2,'constant',constant_values=0)
        print(self.arr)
        #self.arr.append( np.zeros( (VX.DIM,VX.DIM) ) )
        
        fig = plt.figure(figsize=VX.FIGSIZE)
        ax = fig.add_subplot(111, projection='3d')
        verts, faces = self.to_mesh(step_size=step_size)
        ax.add_collection3d(Poly3DCollection(verts[faces]))
        ax.set_xlim(0, VX.DIM) 
        ax.set_ylim(0, VX.DIM) 
        ax.set_zlim(0, VX.DIM) 
        ax.set_xlabel("x-axis")
        ax.set_ylabel("y-axis")
        ax.set_zlabel("z-axis")

        plt.show()
        self.save_stl()
        
        
if __name__ == "__main__":
    main()