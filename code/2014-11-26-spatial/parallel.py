from vtk.numpy_interface import dataset_adapter as dsa
import vtk
import numpy as np
from mpi4py import MPI

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if size != 2:
    print 'This example needs 2 MPI processes'
    import sys
    sys.exit(0)

w = vtk.vtkRTAnalyticSource()
w.SetWholeExtent(-100, 100, -100, 100, -100, 100)

c = vtk.vtkContourFilter()
c.SetInputConnection(w.GetOutputPort())
c.SetValue(0, 180)

ps = vtk.vtkPieceScalars()
ps.SetInputConnection(c.GetOutputPort())

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(ps.GetOutputPort())
# For streaming
mapper.SetNumberOfSubPieces(20/size)
# For parallel execution
mapper.SetNumberOfPieces(size)
mapper.SetPiece(rank)
mapper.SetScalarRange(0, 20)

actor = vtk.vtkActor()
actor.SetMapper(mapper)

ren = vtk.vtkRenderer()
ren.AddActor(actor)

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetSize(600, 600)
ren.GetActiveCamera().SetPosition(0, 0, 400)
# We need to do this manually because we want z buffer
# values to be consistent across MPI ranks.
ren.ResetCameraClippingRange(-100, 100, -100, 100, -100, 100)
renWin.Render()

# Grab the famebuffer
a = vtk.vtkUnsignedCharArray()
renWin.GetRGBACharPixelData(0, 0, 599, 599, 1, a)
rgba = dsa.vtkDataArrayToVTKArray(a)

# Grab the zbuffer
z = vtk.vtkFloatArray()
renWin.GetZbufferData(0, 0, 599, 599, z)
z = dsa.vtkDataArrayToVTKArray(z)

# Write individual framebuffers
i = vtk.vtkImageData()
i.SetDimensions(600, 600, 1)
i.GetPointData().SetScalars(a)

w = vtk.vtkPNGWriter()
w.SetInputData(i)
w.SetFileName("composite2_%d.png" % rank)
w.Write()

if rank == 0:
    # Receive the frame and zbuffers from rank 1
    rgba2 = np.empty_like(rgba)
    z2 = np.empty_like(z)
    comm.Recv([rgba2, MPI.CHAR], source=1, tag=77)
    comm.Recv([z2, MPI.FLOAT], source=1, tag=77)
    # Compositing.
    # Find where the zbuffer values of the remote
    # image are smaller (pixels are closer).
    loc = np.where(z2 < z)
    # Use those locations to overwrite local pixels
    # with remote pixels.
    rgba[loc[0], :] = rgba2[loc[0], :]

    # Write the composited image.
    i = vtk.vtkImageData()
    i.SetDimensions(600, 600, 1)
    i.GetPointData().SetScalars(a)

    w = vtk.vtkPNGWriter()
    w.SetInputData(i)
    w.SetFileName("composite2.png")
    w.Write()
else:
    comm.Send([rgba, MPI.CHAR], dest=0, tag=77)
    comm.Send([z, MPI.FLOAT], dest=0, tag=77)
