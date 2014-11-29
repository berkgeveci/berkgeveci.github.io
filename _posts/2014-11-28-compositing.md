---
layout: post
title: "Spatial Streaming and Compositing"
---

In my [last blog]({% post_url 2014-11-26-streaming-space %}), I talked about
spatial streaming in VTK. The example I covered demonstrated how a pipeline
consisting of a structured data source and a contour filter can be streamed
in smaller chunks to create a collection of polydata objects, which can then
be rendered. The downside of this approach is that the entirety of the contour
geometry needs to be stored in memory for rendering. One way of getting
around this limitation is to stream into a view. Here is an example.

{% highlight python %}
from vtk.numpy_interface import dataset_adapter as dsa
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import vtk
import numpy as np

class StreamExtents(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkImageData',
            nOutputPorts=0)

        self.Contour = vtk.vtkContourFilter()
        self.Contour.SetValue(0, 180)
        self.UpdateIndex = 0
        self.NumberOfBlocks = 20

        self.Mapper = vtk.vtkPolyDataMapper()
        self.Mapper.SetScalarRange(0, 20)

        actor = vtk.vtkActor()
        actor.SetMapper(self.Mapper)

        ren = vtk.vtkRenderer()
        ren.AddActor(actor)

        self.RenWin = vtk.vtkRenderWindow()
        self.RenWin.AddRenderer(ren)
        self.RenWin.Render()
        ren.GetActiveCamera().SetPosition(0, 0, 400)
        self.RenWin.SetSize(600, 600)
        # This allows us to stream into the view. OpenGL
        # takes care of compositing using the z-buffer
        # when Erase is set to off.
        self.RenWin.EraseOff()
        self.RenWin.DoubleBufferOff()

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        # Ask for the next extent.
        info.Set(
            vtk.vtkStreamingDemandDrivenPipeline.UPDATE_NUMBER_OF_PIECES(),
            self.NumberOfBlocks)
        info.Set(
            vtk.vtkStreamingDemandDrivenPipeline.UPDATE_PIECE_NUMBER(),
            self.UpdateIndex)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        inp = dsa.WrapDataObject(vtk.vtkDataSet.GetData(info))

        self.Contour.SetInputData(inp.VTKObject)
        self.Contour.Update()
        contour = dsa.WrapDataObject(self.Contour.GetOutput())
        rtdata = contour.PointData['RTData']
        color = np.empty_like(rtdata)
        color[:] = self.UpdateIndex
        contour.PointData.append(color, "color")
        contour.PointData.SetActiveScalars("color")

        self.Mapper.SetInputData(contour.VTKObject)
        self.RenWin.Render()

        if self.UpdateIndex < self.NumberOfBlocks - 1:
            # If we are not done, ask the pipeline to re-execute us.
            self.UpdateIndex += 1
            request.Set(
                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING(),
                1)
        else:
            # Stop execution
            request.Remove(
                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING())
            # Reset for next potential execution.
            self.UpdateIndex = 0

            w2i = vtk.vtkWindowToImageFilter()
            w2i.SetInput(self.RenWin)

            w = vtk.vtkPNGWriter()
            w.SetInputConnection(w2i.GetOutputPort())
            w.SetFileName("composite1.png")
            w.Write()

        return 1

w = vtk.vtkRTAnalyticSource()
w.SetWholeExtent(-100, 100, -100, 100, -100, 100)

s = StreamExtents()
s.SetInputConnection(w.GetOutputPort())

s.Update()
{% endhighlight %}

Note that this is very similar to the examples in the previous blog. The main
difference is that this algorithm is a sink rather than a filter and instead
of producing a polydata output which represents the contour, it produces an
image. For this, we create a rendering pipeline in the constructor and then
during each pipeline execution, we render the current contour geometry. Finally, we
save the output image after the last render. In skeleton code, this looks like
the following.

{% highlight python %}
def RequestData(self, request, inInfo, outInfo):

    self.Mapper.SetInputData(contour.VTKObject)
    self.RenWin.Render()

    if self.UpdateIndex < self.NumberOfBlocks - 1:
        # If we are not done, ask the pipeline to re-execute us.
        self.UpdateIndex += 1
        request.Set(
            vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING(),
            1)
    else:
        # Stop execution
        request.Remove(
            vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING())
        # Reset for next potential execution.
        self.UpdateIndex = 0

        w2i = vtk.vtkWindowToImageFilter()
        w.Write()
{% endhighlight %}

The trick that makes this example work is in these two lines:

{% highlight python %}
self.RenWin.EraseOff()
self.RenWin.DoubleBufferOff()
{% endhighlight %}

When the `Erase` mode is enabled, the render window renders each time on
top of the same framebuffer and zbuffer without clearing them. OpenGL decides
to draw a particular pixel or not depending on the previous value of the z
buffer. If the old z value is smaller, it keeps the previous pixel.
Otherwise, it overwrites the pixel. This works perfectly because the object
we are rendering is opaque. Handling transparencly would require doing the
passes in a certain order and blending the pixels. I leave that to you as
an exercise. The output looks as follows. Click on the picture to see the
streaming in action.

<figure>
<img src="/assets/composite1.png" alt="Animation" style="margin-left:auto; margin-right:auto" onclick='javascript:this.src="/assets/composite_anim.gif"'/>
</figure>

This example was mainly for demonstration. The same can be achieved in VTK
without writing an algorithm. Here is the code.

{% highlight python %}
import vtk

w = vtk.vtkRTAnalyticSource()
w.SetWholeExtent(-100, 100, -100, 100, -100, 100)

c = vtk.vtkContourFilter()
c.SetInputConnection(w.GetOutputPort())
c.SetValue(0, 180)

ps = vtk.vtkPieceScalars()
ps.SetInputConnection(c.GetOutputPort())

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(ps.GetOutputPort())
mapper.SetNumberOfSubPieces(20)
mapper.SetScalarRange(0, 20)

actor = vtk.vtkActor()
actor.SetMapper(mapper)

ren = vtk.vtkRenderer()
ren.AddActor(actor)

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetSize(600, 600)
ren.GetActiveCamera().SetPosition(0, 0, 400)
renWin.Render()
{% endhighlight %}

The only special thing in this example is the `mapper.SetNumberOfSubPieces(20)`
line which tells the mapper to stream its input in 20 steps. This uses the
same logic as our example in that the mapper does multiple render passes when
it is asked to render.

## Parallel Compositing

The examples we covered so far are only one step away from parallel compositing
so we might as well cover that too. In general, parallel sort last compositing
involves rendering images with geometry local to each process, transferring
the frame and zbuffers over the network and then comparing the z values to decide
which pixels to keep from which framebuffer. For more details on compositing,
I recommend checking out some of the papers out there, for example
"An Image Compositing Solution at Scale" by Moreland et al. You should also check
out [IceT](http://icet.sandia.gov/), which has become the open-source reference
and production implementation used by many parallel tools including
VTK/ParaView.

Here is my simple two process example demonstrating compositing.

{% highlight python %}
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
{% endhighlight %}

There are a few interesting bits to this example. First, the following
sets up distributed processing pipeline as well as streaming:

{% highlight python %}
# For streaming
mapper.SetNumberOfSubPieces(20/size)
# For parallel execution
mapper.SetNumberOfPieces(size)
mapper.SetPiece(rank)
{% endhighlight %}

Note how each process is asked to process the piece with index `rank` among
a group of size `size`. In addition, each process is asked to stream using
`20/size` pieces. With 2 ranks, we still have 20 pieces total. The only
special thing we have to do for compositing to work is this.

{% highlight python %}
# We need to do this manually because we want z buffer
# values to be consistent across MPI ranks.
ren.ResetCameraClippingRange(-100, 100, -100, 100, -100, 100)
{% endhighlight %}

If we don't set a global clipping range, each rank will use clipping planes
based on local data which will lead to inconsistent zbuffer values (which
are normalized to 0-1).

Then we grab the frame and zbuffer with

{% highlight python %}
# Grab the famebuffer
a = vtk.vtkUnsignedCharArray()
renWin.GetRGBACharPixelData(0, 0, 599, 599, 1, a)
rgba = dsa.vtkDataArrayToVTKArray(a)

# Grab the zbuffer
z = vtk.vtkFloatArray()
renWin.GetZbufferData(0, 0, 599, 599, z)
z = dsa.vtkDataArrayToVTKArray(z)
{% endhighlight %}

Then transfer the buffer from rank 1 to 0 with

{% highlight python %}
if rank == 0:
    # Receive the frame and zbuffers from rank 1
    rgba2 = np.empty_like(rgba)
    z2 = np.empty_like(z)
    comm.Recv([rgba2, MPI.CHAR], source=1, tag=77)
    comm.Recv([z2, MPI.FLOAT], source=1, tag=77)
else:
    comm.Send([rgba, MPI.CHAR], dest=0, tag=77)
    comm.Send([z, MPI.FLOAT], dest=0, tag=77)
{% endhighlight %}

Finally compositing is only 2 lines:

{% highlight python %}
    # Compositing.
    # Find where the zbuffer values of the remote
    # image are smaller (pixels are closer).
    loc = np.where(z2 < z)
    # Use those locations to overwrite local pixels
    # with remote pixels.
    rgba[loc[0], :] = rgba2[loc[0], :]
{% endhighlight %}

I leave it up to the reader as an exercise to extend this to more
than 2 ranks. The paper by Ken et al. describes common ways of doing
this including using a binary tree pattern.

Here are the 2 local images and the final image:

![composite](/assets/composite3.png)

In a future blog, I will talk about block-based streaming. Until then,
happy coding.
