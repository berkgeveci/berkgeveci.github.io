---
layout: post
title:  "Developing HDF5 readers using vtkPythonAlgorithm"
---

In my [last article]({% post_url 2014-9-5-vtk-python-algorithm %}), I introduced the new
`vtkPythonAlgorithm` and showed how it can be used to developed fully functional VTK algorithms in
Python. In this one, we are going to put this knowledge to use and develop a set of
[HDF5](http://www.hdfgroup.org/HDF5/) readers using the wonderful [h5py](http://www.h5py.org/)
package.

First, let's use h5py to write a series of simple HDF5 files.

{% highlight python %}
import vtk, h5py
from vtk.numpy_interface import dataset_adapter as dsa

def write_file(data, xfreq):
    wdata = dsa.WrapDataObject(data)
    array = wdata.PointData['RTData']
    # Note that we flip the dimensions here because
    # VTK's order is Fortran whereas h5py writes in
    # C order. We don't want to do deep copies so we write
    # with dimensions flipped and pretend the array is
    # C order.
    array = array.reshape(wdata.GetDimensions()[::-1])
    f = h5py.File('data%d.h5' % xfreq, 'w')
    f.create_dataset("RTData", data=array)


rt = vtk.vtkRTAnalyticSource()

for xfreq in range(60, 80):
    rt.SetXFreq(xfreq)
    rt.Update()
    write_file(rt.GetOutput(), xfreq)
{% endhighlight %}

Here I used the `vtkRTAnalyticSource` which generates synthetic data for testing purposes. I varied
its X Frequency parameter in order to create a file series. The output will be a set of files
ranging from `data60.h5` to `data79.h5`. Each file will contain one 3D dataset.

{% highlight sh %}
>> h5ls data60.h5
RTData                   Dataset {21, 21, 21}
{% endhighlight %}

Here is my first pass at a `vtkPythonAlgorithm` based reader.

{% highlight python %}
import vtk, h5py
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtk.numpy_interface import dataset_adapter as dsa

class HDF5Source(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=0,
            nOutputPorts=1, outputType='vtkImageData')

        self.__FileName = ""

    def RequestData(self, request, inInfo, outInfo):
        f = h5py.File(self.__FileName, 'r')
        data = f['RTData'][:]
        output = dsa.WrapDataObject(vtk.vtkImageData.GetData(outInfo))
        # Note that we flip the dimensions here because
        # VTK's order is Fortran whereas h5py writes in
        # C order.
        output.SetDimensions(data.shape[::-1])
        output.PointData.append(data.ravel(), 'RTData')
        output.PointData.SetActiveScalars('RTData')
        return 1

    def SetFileName(self, fname):
        if fname != self.__FileName:
            self.Modified()
            self.__FileName = fname

    def GetFileName(self):
        return self.__FileName

{% endhighlight %}

Note that this is fairly basic. It performs no error checking and hard-codes the `RTData`
dataset in `RequestData`. We can test the reader with a script like this:

{% highlight python %}
alg = HDF5Source()
alg.SetFileName("data60.h5")

cf = vtk.vtkContourFilter()
cf.SetInputConnection(alg.GetOutputPort())
cf.SetValue(0, 200)

m = vtk.vtkPolyDataMapper()
m.SetInputConnection(cf.GetOutputPort())

a = vtk.vtkActor()
a.SetMapper(m)

ren = vtk.vtkRenderer()
ren.AddActor(a)

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetSize(600, 600)

for xfreq in range(60, 80):
    alg.SetFileName('data%d.h5' % xfreq)
    renWin.Render()
    import time
    time.sleep(0.1)
{% endhighlight %}

Guess what. It doesn't work :-) This is because the producer of any structured dataset
(`vtkImageData`, `vtkRectilinearGrid` and `vtkStructuredGrid`) has to report the _whole extent_ of
the data in the index space. So we need to add the method to do that:

{% highlight python %}
    def RequestInformation(self, request, inInfo, outInfo):
        f = h5py.File(self.__FileName, 'r')
        # Note that we flip the shape because VTK is Fortran order
        # whereas h5py reads in C order. When writing we pretend that the
        # data was C order so we have to flip the extents/dimensions.
        dims = f['RTData'].shape[::-1]
        info = outInfo.GetInformationObject(0)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT(),
            (0, dims[0]-1, 0, dims[1]-1, 0, dims[2]-1), 6)
        return 1
{% endhighlight %}

With this addition, we get the following result (click on the picture to see the
animation).

<figure>
<img src="/assets/image60.png" alt="Animation" style="margin-left:auto; margin-right:auto" onclick='javascript:this.src="/assets/rtdata-anim.gif"'/>
</figure>

As I discussed previously, `RequestInformation` provides meta-data downstream. This meta-data is
most of the time lightweight. In this example, we used  `f['RTData'].shape` to read extent meta-data
from the HDF5 file. This does not read any heavyweight data. Later on, we will see other examples of
meta-data that is provided during `RequestInformation`.

Let's make our reader a bit more sophisticated. Notice that the `RequestData` we implemented above
always reads the whole dataset. However, VTK's pipeline is designed such that algorithms can ask a
data producer for a subset of its whole extent. This is done using the `UPDATE_EXTENT` key. Let's
change our `RequestData` to handle UPDATE_EXTENT:

{% highlight python %}
    def RequestData(self, request, inInfo, outInfo):
        f = h5py.File(self.__FileName, 'r')
        info = outInfo.GetInformationObject(0)
        ue = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT())
        # Note that we flip the update extents because VTK is Fortran order
        # whereas h5py reads in C order. When writing we pretend that the
        # data was C order so we have to flip the extents/dimensions.
        data = f['RTData'][ue[4]:ue[5]+1, ue[2]:ue[3]+1, ue[0]:ue[1]+1]
        output = dsa.WrapDataObject(vtk.vtkImageData.GetData(outInfo))
        output.SetExtent(ue)
        output.PointData.append(data.ravel(), 'RTData')
        output.PointData.SetActiveScalars('RTData')
        return 1
{% endhighlight %}

Here the key is the following:

{% highlight python %}
        data = f['RTData'][ue[4]:ue[5]+1, ue[2]:ue[3]+1, ue[0]:ue[1]+1]
{% endhighlight %}

Thanks to h5py's support for reading subsets (called hyperslabs in HDF5 speak), we had to do very
little to support the `UPDATE_EXTENT` request. Let's try it out.

{% highlight python %}
alg = HDF5Source()
alg.SetFileName("data60.h5")

alg.UpdateInformation()

alg.SetUpdateExtent((5, 10, 5, 10, 0, 10))
alg.Update()

print alg.GetOutputDataObject(0).GetExtent()
{% endhighlight %}

This will print `(5, 10, 5, 10, 0, 10)` as expected. A few notes:

* `UpdateInformation()` tells the algorithm (and the pipeline upstream of the algorithm) to produce
meta-data. In our example, this will lead to a call to `HDF5Source.RequestInformation()`.
* It is essential to call `UpdateInformation()` before setting any requests. Otherwise, any user
set requests will be overwritten.
* `SetUpdateExtent()` tells the algorithms to produce a given extent; in this case based on index
space. There are other signatures of `SetUpdateExtent()` we will discover later.
* This works only if the requests are set on the algorithm that `Update()` will be called on.
If you were to set any requests on any algorithms upstream of the pipeline, they would be
overwritten by downstream filters.

As a final exercise in this article, let's write a Python filter that asks the `HDF5Source` to
produce only a sub-extent so that we can contour and render a subset (à la `vtkExtractVOI`). Here it
is.

{% highlight python %}
class RequestSubset(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkImageData',
            nOutputPorts=1, outputType='vtkImageData')
        self.__UpdateExtent = None

    def RequestInformation(self, request, inInfo, outInfo):
        info = outInfo.GetInformationObject(0)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT(), \
            self.__UpdateExtent, 6)
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        if self.__UpdateExtent is not None:
            info = inInfo[0].GetInformationObject(0)
            info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT(), \
                self.__UpdateExtent, 6)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        inp = vtk.vtkImageData.GetData(inInfo[0])
        opt = vtk.vtkImageData.GetData(outInfo)
        opt.ShallowCopy(inp)
        return 1

    def SetUpdateExtent(self, ue):
        if ue != self.__UpdateExtent:
            self.Modified()
            self.__UpdateExtent = ue

    def GetUpdateExtent(self):
        return self.__UpdateExtent
{% endhighlight %}

If you look at `RequestData()` alone, this is a pass-through filter. It shallow copies its input
to its output. The trick is in `RequestUpdateExtent()` where the filter asks for the user defined
extent from its input. When this is combined with the reader's ability of reading requested
subsets, this filter acts as a subset filter producing the user requested sub-extent.
`RequestInformation()` is written to reflect this : it tells downstream that the filter will
produce the extent requested by the user.

Let's put these two algorithms in a pipeline:

{% highlight python %}
alg = HDF5Source()
alg.SetFileName("data60.h5")

rs = RequestSubset()
rs.SetInputConnection(alg.GetOutputPort())
rs.SetUpdateExtent((5, 10, 5, 10, 0, 20))

cf = vtk.vtkContourFilter()
cf.SetInputConnection(rs.GetOutputPort())
cf.SetValue(0, 200)

m = vtk.vtkPolyDataMapper()
m.SetInputConnection(cf.GetOutputPort())

a = vtk.vtkActor()
a.SetMapper(m)

ren = vtk.vtkRenderer()
ren.AddActor(a)

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetSize(300, 300)
renWin.Render()

for xfreq in range(60, 80):
    alg.SetFileName('data%d.h5' % xfreq)

    renWin.Render()
{% endhighlight %}

This will produce the following (click on the picture to see the animation).

<figure>
<img src="/assets/image60-2.png" alt="Animation" style="margin-left:auto; margin-right:auto" onclick='javascript:this.src="/assets/rtdata-anim-2.gif"'/>
</figure>

We now have a fairly complex reader in our hands. With some digging through h5py's documentation
and a bit of numpy knowledge, you can put together readers that do a lot more very easily. In
upcoming blogs, I will build on this foundation to highlight other features of VTK's pipeline.

If you got a little lost in the details of the pipeline passes, don't worry. In my next blog,
I will discuss in a bit more detail how the various pipeline passes work and what they do.

_Note: This article was originally published on the [Kitware blog](http://www.kitware.com/blog/home/post/739).
Please see the [Kitware web site](http://www.kitware.com), the [VTK web site](http://www.vtk.org) and the
[ParaView web site](http://www.paraview.org) for more information._
