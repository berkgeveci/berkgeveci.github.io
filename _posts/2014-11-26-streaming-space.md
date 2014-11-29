---
layout: post
title: "Streaming in VTK : Spatial"
---

In my last 2 blogs ([1]({% post_url 2014-11-09-streaming-time %}),
[2]({% post_url 2014-11-16-simple-particle %})), I covered temporal streaming
in VTK. Let's check out how these ideas can be applied to spatial streaming. By
spatial streaming, I mean processing a larger dataset in multiple pipeline
executions wherein each execution processes a spatial subset of the data.
There are 3 ways of spatial streaming in VTK:

1. Extent based,
2. Piece based,
3. Block based.

In this blog, we'll cover 1 and 2. I'll talk about 3 later. Let's dive into an
example right away.

{% highlight python %}
from vtk.numpy_interface import dataset_adapter as dsa
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import vtk
import numpy as np

class StreamExtents(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkImageData',
            nOutputPorts=1, outputType='vtkMultiBlockDataSet')

        self.Contour = vtk.vtkContourFilter()
        self.Contour.SetValue(0, 180)
        self.UpdateIndex = 0
        self.NumberOfBlocks = 20
        self.ExtentTranslator = vtk.vtkExtentTranslator()
        self.ExtentTranslator.SetNumberOfPieces(self.NumberOfBlocks)

    def RequestInformation(self, request, inInfo, outInfo):
        # We need to report that we are a time source to downstream.
        # We will use the TIME_VALUES from upstream for this.
        info = inInfo[0].GetInformationObject(0)
        wholeExtent = info.Get(
            vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT())
        self.ExtentTranslator.SetWholeExtent(wholeExtent)

        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        # Ask for the next extent.
        self.ExtentTranslator.SetPiece(self.UpdateIndex)
        self.ExtentTranslator.PieceToExtent()
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT(),
            self.ExtentTranslator.GetExtent(), 6)
        print self.ExtentTranslator.GetExtent()
        return 1

    def RequestData(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        inp = dsa.WrapDataObject(vtk.vtkDataSet.GetData(info))
        output = vtk.vtkMultiBlockDataSet.GetData(outInfo)

        # Initialize the number of blocks in the output
        if output.GetNumberOfBlocks() == 0:
            output.SetNumberOfBlocks(self.NumberOfBlocks)

        # Contour the current piece and add to the output
        self.Contour.SetInputData(inp.VTKObject)
        self.Contour.Update()
        print self.UpdateIndex, self.Contour.GetOutput().GetNumberOfCells()
        contour = dsa.WrapDataObject(self.Contour.GetOutput())
        rtdata = contour.PointData['RTData']
        # We create an array to color by later. To show different
        # pieces.
        color = np.empty_like(rtdata)
        color[:] = self.UpdateIndex
        contour.PointData.append(color, "color")
        contour.PointData.SetActiveScalars("color")
        if contour.GetNumberOfCells() > 0:
            block = vtk.vtkPolyData()
            block.ShallowCopy(contour.VTKObject)
            output.SetBlock(self.UpdateIndex, block)

        # These control streaming.
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
        return 1

w = vtk.vtkRTAnalyticSource()
w.SetWholeExtent(-100, 100, -100, 100, -100, 100)

s = StreamExtents()
s.SetInputConnection(w.GetOutputPort())

m = vtk.vtkCompositePolyDataMapper()
m.SetInputConnection(s.GetOutputPort())
m.SetScalarRange(0, 20)

a = vtk.vtkActor()
a.SetMapper(m)

ren = vtk.vtkRenderer()
ren.AddActor(a)

renWin = vtk.vtkRenderWindow()
renWin.SetSize(800, 800)
renWin.AddRenderer(ren)

renWin.Render()
{% endhighlight %}

This code is almost identical to the temporal streaming code so I will not cover
pipeline details. The key pieces are the following.

{% highlight python %}
w = vtk.vtkRTAnalyticSource()
w.SetWholeExtent(-100, 100, -100, 100, -100, 100)
{% endhighlight %}

This is where we configure a synthetic data source to (potentially) produce an
image of extents `(-100, 100, -100, 100, -100, 100)`. Now, let's say that this
volume is too big to fit into memory and we want to process it in smaller chunks.
To achieve this, we can use the `vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT()`
request. This key allows a consumer to ask a producer a subset of what it
can produce. So in our `RequestUpdateExtent()`, we do the following:

{% highlight python %}
def RequestUpdateExtent(self, request, inInfo, outInfo):
    info = inInfo[0].GetInformationObject(0)
    # Ask for the next extent.
    self.ExtentTranslator.SetPiece(self.UpdateIndex)
    self.ExtentTranslator.PieceToExtent()
    info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT(),
        self.ExtentTranslator.GetExtent(), 6)
    return 1
{% endhighlight %}

The key part here is the use of the extent translator. `vtkExtentTranslator`
is a simple class that breaks an extent into smaller chunks given two
parameters: `NumberOfPieces` and `Piece`. If we print out the extent in
`RequestUpdateExtent()`, we see:

{% highlight python %}
(-100, -20, -100, 0, -100, -50)
(-100, -20, -100, 0, -50, 0)
(-20, 20, -100, 0, -100, 0)
(20, 100, -100, 0, -100, -50)
(20, 100, -100, 0, -50, 0)
(-100, -20, 0, 100, -100, -50)
(-100, -20, 0, 100, -50, 0)
(-20, 20, 0, 100, -100, 0)
(20, 100, 0, 100, -100, -50)
(20, 100, 0, 100, -50, 0)
(-100, -20, -100, 0, 0, 50)
(-100, -20, -100, 0, 50, 100)
(-20, 20, -100, 0, 0, 100)
(20, 100, -100, 0, 0, 50)
(20, 100, -100, 0, 50, 100)
(-100, -20, 0, 100, 0, 50)
(-100, -20, 0, 100, 50, 100)
(-20, 20, 0, 100, 0, 100)
(20, 100, 0, 100, 0, 50)
(20, 100, 0, 100, 50, 100)
{% endhighlight %}

Finally, we use the following to create the output:

{% highlight python %}
self.Contour.SetInputData(inp.VTKObject)
self.Contour.Update()
contour = self.Contour.GetOutput()
if contour.GetNumberOfCells() > 0:
    block = vtk.vtkPolyData()
    block.ShallowCopy(contour)
    output.SetBlock(self.UpdateIndex, block)
{% endhighlight %}

This code contours the current block and adds the result to the output, which
is a multi-block dataset.

The output looks like this:

![multi extent](/assets/multi-extent.png)

Next, let see how we can do piece based streaming. Actually, this is almost
identical to extent based streaming. Here is the code.

{% highlight python %}
from vtk.numpy_interface import dataset_adapter as dsa
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import vtk

class StreamExtents(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkImageData',
            nOutputPorts=1, outputType='vtkMultiBlockDataSet')

        self.Contour = vtk.vtkContourFilter()
        self.Contour.SetValue(0, 180)
        self.UpdateIndex = 0
        self.NumberOfBlocks = 20

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        # Ask for the next extent.
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_NUMBER_OF_PIECES(),
            self.NumberOfBlocks)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_PIECE_NUMBER(),
            self.UpdateIndex)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        inp = dsa.WrapDataObject(vtk.vtkDataSet.GetData(info))
        output = vtk.vtkMultiBlockDataSet.GetData(outInfo)

        if output.GetNumberOfBlocks() == 0:
            output.SetNumberOfBlocks(self.NumberOfBlocks)

        self.Contour.SetInputData(inp.VTKObject)
        self.Contour.Update()
        print self.UpdateIndex, self.Contour.GetOutput().GetNumberOfCells()
        contour = self.Contour.GetOutput()
        if contour.GetNumberOfCells() > 0:
            block = vtk.vtkPolyData()
            block.ShallowCopy(contour)
            output.SetBlock(self.UpdateIndex, block)

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
        return 1

w = vtk.vtkRTAnalyticSource()
w.SetWholeExtent(-100, 100, -100, 100, -100, 100)

s = StreamExtents()
s.SetInputConnection(w.GetOutputPort())

m = vtk.vtkCompositePolyDataMapper()
m.SetInputConnection(s.GetOutputPort())

a = vtk.vtkActor()
a.SetMapper(m)

ren = vtk.vtkRenderer()
ren.AddActor(a)

renWin = vtk.vtkRenderWindow()
renWin.SetSize(800, 800)
renWin.AddRenderer(ren)

renWin.Render()
{% endhighlight %}

The biggest difference is in `RequestUpdateExtent` where we do the following:

{% highlight python %}
def RequestUpdateExtent(self, request, inInfo, outInfo):
    info = inInfo[0].GetInformationObject(0)
    # Ask for the next extent.
    info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_NUMBER_OF_PIECES(),
        self.NumberOfBlocks)
    info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_PIECE_NUMBER(),
        self.UpdateIndex)
    return 1
{% endhighlight %}

instead of

{% highlight python %}
def RequestUpdateExtent(self, request, inInfo, outInfo):
    info = inInfo[0].GetInformationObject(0)
    # Ask for the next extent.
    self.ExtentTranslator.SetPiece(self.UpdateIndex)
    self.ExtentTranslator.PieceToExtent()
    info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT(),
        self.ExtentTranslator.GetExtent(), 6)
    return 1
{% endhighlight %}

Since the data source, which is a simple image source, did not change, the behavior
is actually identical in both cases. In fact, the executive uses the extent
translator under the cover to ask the source for the appropriate subset during
each execution. This is not the case for all data source however. For unstructured
data sources, the only choice is to use piece based streaming.

This is it for now folks. In my next blog, I will talk about how we can reduce
the memory usage of this pipeline further by streaming onto an image rather than
a set of polydata objects. Note that polydata objects produced by the contour
filter can get fairly large - sometimes larger than the original image. So
it may not always be possible to keep all of the polydata in memory for rendering.
We'll see how we can avoid it in some cases. Hint: Check out `vtkWindow::SetErase()`
and `vtkWindow::SetDoubleBuffer()`.