---
layout: post
title: "Block-Based Streaming"
---

This is it. My last blog on streaming, at least for a while.
Looking back, I have been writing about the VTK pipeline and
how it can be leveraged to do cool things since September.
This will be a cool topic to wrap this series up with.

In the [last blog]({% post_url 2015-01-08-h5py-writer-reader %}),
I demonstrated how to write a dataset in blocks using h5py and
reading it with a simple reader. When writing the blocks, we also
saved meta-data for the spatial bounds of each block. We will
leverage this meta-data here. Here is the reader.

{% highlight python %}
class HDF5Reader(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=0,
            nOutputPorts=1, outputType='vtkMultiBlockDataSet')

        self.__FileName = ""

    def RequestInformation(self, request, inInfo, outInfo):
        import re
        p = re.compile('piece([0-9]*)')

        md = vtk.vtkMultiBlockDataSet()
        f = h5py.File(self.__FileName, 'r')
        for grp_name in f:
            idx = int(p.match(grp_name).groups()[0])
            md.SetBlock(idx, None)
            bmd = md.GetMetaData(idx)
            idx += 1
            grp = f[grp_name]
            bds = grp.attrs['bounds']
            bmd.Set(vtk.vtkDataObject.BOUNDING_BOX(), bds, 6)

        f.close()

        outInfo.GetInformationObject(0).Set(
            vtk.vtkCompositeDataPipeline.COMPOSITE_DATA_META_DATA(),
            md)

        return 1

    def RequestData(self, request, inInfo, outInfo):
        output = dsa.WrapDataObject(vtk.vtkMultiBlockDataSet.GetData(outInfo))

        import re
        p = re.compile('piece([0-9]*)')

        f = h5py.File(self.__FileName, 'r')

        if outInfo.GetInformationObject(0).Has(
            vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES()):
            uci = outInfo.GetInformationObject(0).Get(
                vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES())
            if uci is None:
                pieces = []
            else:
                pieces = ["piece%d" % num for num in uci]
        else:
            pieces = f
        idx = 0
        nblocks = len(pieces)
        output.SetNumberOfBlocks(nblocks)
        idx = 0
        for grp_name in pieces:
            ug = vtk.vtkUnstructuredGrid()
            output.SetBlock(idx, ug)
            idx += 1
            ug = dsa.WrapDataObject(ug)
            grp = f[grp_name]
            cells = grp['cells'][:]
            locations = grp['cell_locations'][:]
            types = grp['cell_types'][:]
            ug.SetCells(types, locations, cells)
            pts = grp['points'][:]
            ug.Points = pts
            pt_arrays = grp['point_data']
            for pt_array in pt_arrays:
                array = pt_arrays[pt_array][:]
                ug.PointData.append(array, pt_array)
        f.close()

        return 1

    def SetFileName(self, fname):
        if fname != self.__FileName:
            self.Modified()
            self.__FileName = fname

    def GetFileName(self):
        return self.__FileName
{% endhighlight %}

The part that reads data is almost identical to the reader in
the last blog so I won't cover that here. The interesting part
is related to meta-data and request. Here is the meta-data part.

{% highlight python %}
1  def RequestInformation(self, request, inInfo, outInfo):
2      import re
3      p = re.compile('piece([0-9]*)')
4
5      md = vtk.vtkMultiBlockDataSet()
6      f = h5py.File(self.__FileName, 'r')
7      for grp_name in f:
8          idx = int(p.match(grp_name).groups()[0])
9          md.SetBlock(idx, None)
10         bmd = md.GetMetaData(idx)
11         idx += 1
12         grp = f[grp_name]
13         bds = grp.attrs['bounds']
14         bmd.Set(vtk.vtkDataObject.BOUNDING_BOX(), bds, 6)
15
16     f.close()
17
18     outInfo.GetInformationObject(0).Set(
19         vtk.vtkCompositeDataPipeline.COMPOSITE_DATA_META_DATA(),
20         md)
21
22     return 1
{% endhighlight %}

Lines 5-14 are the meat of this function. On line 5, we create
a multi-block dataset that will be used to hold meta-data to
be sent downstream. Note that, this object is used for transmitting
meta-data only. On line 8, we extract
a block number from the name of an HDF5 group. On lines 12-13,
we read the bounds for that block. This meta-data is assigned to
the corresponding block's meta-data object obtained on line 10.
Finally, we set this dataset as the `COMPOSITE_DATA_META_DATA()` on
lines 18-20. This information entry is propagated downstream automatically
by the pipeline during the `RequestInformation()` pass.

Once this meta-data is propagated downstream, consumers can ask for
a subset of blocks to be read during the `RequestUpdateExtent()` pass.
This pass will likely set a `UPDATE_COMPOSITE_INDICES()` which the
reader has to respond to. We will demonstrate how this key is set
later. Let's first look at how the reader uses it in `RequestData()`.

{% highlight python %}
def RequestData(self, request, inInfo, outInfo):
    output = dsa.WrapDataObject(vtk.vtkMultiBlockDataSet.GetData(outInfo))

    import re
    p = re.compile('piece([0-9]*)')

    f = h5py.File(self.__FileName, 'r')

    if outInfo.GetInformationObject(0).Has(
        vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES()):
        uci = outInfo.GetInformationObject(0).Get(
            vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES())
        if uci is None:
            pieces = []
        else:
            pieces = ["piece%d" % num for num in uci]
    else:
        pieces = f

    for grp_name in pieces:
        # ...
{% endhighlight %}

The main difference from a standard reader is that we look at which
blocks (referred to as `pieces` in this example but not to be confused
with the pipeline piece) are requested to decide what to read. This
code handles 3 different cases:

* No `UPDATE_COMPOSITE_INDICES()` is set. In this case, we read all
of the blocks. `pieces == f`.
* `UPDATE_COMPOSITE_INDICES()` is set but is empty. We read nothing.
`pieces == []`
* `UPDATE_COMPOSITE_INDICES()` is set to a non-empty list. We read
what is requested. `pieces == ["piece%d" % num for num in uci]`.

This is it for the reader. Now let's look at a simple streaming writer.
This is very similar to writer in the previous blog but uses blocks
instead of pieces to stream.

{% highlight python %}
class StreamBlocks(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkMultiBlockDataSet',
            nOutputPorts=1, outputType='vtkMultiBlockDataSet')

        self.UpdateIndex = 0
        self.__FileName = ""

    def RequestInformation(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        blocks = info.Get(
            vtk.vtkCompositeDataPipeline.COMPOSITE_DATA_META_DATA())
        self.NumberOfBlocks = blocks.GetNumberOfBlocks()
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        info.Set(
            vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES(),
            [self.UpdateIndex],
            1)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        if self.UpdateIndex == 0:
              self.__File = h5py.File(self.__FileName, 'w')

        info = inInfo[0].GetInformationObject(0)
        inpMB = vtk.vtkMultiBlockDataSet.GetData(info)
        if inpMB.GetBlock(0) is not None:
            inp = dsa.WrapDataObject(inpMB.GetBlock(0))

            if inp.GetNumberOfCells() > 0:
                grp = self.__File.create_group("piece%d" % self.UpdateIndex)
                grp.attrs['bounds'] = inp.GetBounds()

                grp.create_dataset("cells", data=inp.Cells)
                grp.create_dataset("cell_types", data=inp.CellTypes)
                grp.create_dataset("cell_locations", data=inp.CellLocations)

                grp.create_dataset("points", data=inp.Points)

                pdata = grp.create_group("point_data")
                for name in inp.PointData.keys():
                    pdata.create_dataset(name, data=inp.PointData[name])

        if self.UpdateIndex < self.NumberOfBlocks - 1:
            # If we are not done, ask the pipeline to re-execute us.
            self.UpdateIndex += 1
            request.Set(
                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING(), 1)
        else:
            # Stop execution
            request.Remove(
                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING())
            # Reset for next potential execution.
            self.UpdateIndex = 0

            self.__File.close()
            del self.__File
        return 1

    def SetFileName(self, fname):
        if fname != self.__FileName:
            self.Modified()
            self.__FileName = fname

    def GetFileName(self):
        return self.__FileName
{% endhighlight %}

If you compare this writer to the previous one, you will see that it has
very few minor differences. The biggest difference is in `RequestUpdateExtent()`:

{% highlight python %}
def RequestUpdateExtent(self, request, inInfo, outInfo):
    info = inInfo[0].GetInformationObject(0)
    info.Set(
        vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES(),
        [self.UpdateIndex],
        1)
    return 1
{% endhighlight %}

Note how the writer sets `UPDATE_COMPOSITE_INDICES()` rather than
`UPDATE_PIECE_NUMBER()` to achieve streaming.

Let's make things a bit more interesting. Say we want to insert a planar
cutter (slice) between the writer and the reader. This filter will need
only a subset of the input blocks - the ones that the slice plane intersects.
Since the spatial bounds of each block is available at the meta-data stage
(`RequestInformation`), this filter can actually make a smart decision on
which blocks need to be loaded by the reader. Here is such a filter.

{% highlight python %}
class PlaneCutter(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkMultiBlockDataSet',
            nOutputPorts=1, outputType='vtkMultiBlockDataSet')

        self.__Origin = (0, 0, 0)
        self.__Normal = (1, 0, 0)
        self.__BlockMap = {}

    def CheckBounds(self, bounds):
        pts = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
         (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
        import numpy
        org = numpy.array(self.__Origin, dtype = numpy.float64)
        nrm = numpy.array(self.__Normal, dtype = numpy.float64)
        point = numpy.zeros((3,), dtype = numpy.float64)
        sign = None
        all_same = True
        for pt in pts:
            point[0] = bounds[pt[0]]
            point[1] = bounds[pt[1] + 2]
            point[2] = bounds[pt[2] + 4]
            sn = numpy.sign(numpy.dot(point - org, nrm))
            if sign is None:
                sign = sn
            if sign != sn:
                all_same = False
                break
        return not all_same

    def RequestInformation(self, request, inInfo, outInfo):
        inInfo0 = inInfo[0].GetInformationObject(0)
        metaData = inInfo0.Get(
            vtk.vtkCompositeDataPipeline.COMPOSITE_DATA_META_DATA())
        nblocks = metaData.GetNumberOfBlocks()
        idx = 0
        for i in range(nblocks):
            bmd = metaData.GetMetaData(i)
            if self.CheckBounds(bmd.Get(vtk.vtkDataObject.BOUNDING_BOX())):
                self.__BlockMap[idx] = i
                idx += 1

        md = vtk.vtkMultiBlockDataSet()
        for i in self.__BlockMap.keys():
            ii = self.__BlockMap[i]
            imd = metaData.GetMetaData(ii)
            bds = imd.Get(vtk.vtkDataObject.BOUNDING_BOX())
            md.SetBlock(i, None)
            bmd = md.GetMetaData(i)
            bmd.Set(vtk.vtkDataObject.BOUNDING_BOX(), bds, 6)

        outInfo.GetInformationObject(0).Set(
            vtk.vtkCompositeDataPipeline.COMPOSITE_DATA_META_DATA(),
            md)

        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        inInfo0 = inInfo[0].GetInformationObject(0)

        if outInfo.GetInformationObject(0).Has(
            vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES()):
            uci = outInfo.GetInformationObject(0).Get(
                vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES())
            if uci is None:
                uci = []
        else:
            uci = self.__BlockMap.keys()

        requestBlocks = []
        for i in uci:
            requestBlocks.append(self.__BlockMap[i])

        nblocks = len(requestBlocks)
        if nblocks == 0:
            # Special case because the Python generated code
            # does not like None instead of a NULL pointer in
            # this case.
            inInfo0.Set(
                vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES(),
                [0],
                0)
        else:
            inInfo0.Set(
                vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES(),
                requestBlocks, len(requestBlocks))

        return 1

    def RequestData(self, request, inInfo, outInfo):
        inInfo0 = inInfo[0].GetInformationObject(0)
        inpMB = vtk.vtkMultiBlockDataSet.GetData(inInfo0)
        output = vtk.vtkMultiBlockDataSet.GetData(outInfo)

        c = vtk.vtkCutter()

        p = vtk.vtkPlane()
        p.SetNormal(self.__Normal)
        p.SetOrigin(self.__Origin)
        c.SetCutFunction(p)

        idx = 0
        itr = inpMB.NewIterator()
        while not itr.IsDoneWithTraversal():
            inp = itr.GetCurrentDataObject()
            c.SetInputData(inp)
            c.Update()
            opt = c.GetOutput().NewInstance()
            opt.ShallowCopy(c.GetOutput())
            output.SetBlock(idx, opt)
            idx += 1
            itr.GoToNextItem()

        itr.UnRegister(None)

        return 1

    def SetOrigin(self, origin):
        if origin != self.__Origin:
            self.Modified()
            self.__Origin = origin

    def GetOrigin(self):
        return self.__Origin

    def SetNormal(self, normal):
        if normal != self.__Normal:
            self.Modified()
            self.__Normal = normal

    def GetNormal(self):
        return self.__Normal
{% endhighlight %}

This filter is more complicated than what we have seen so far. Let's
break it into smaller pieces to study.

First the meta-data pass.
Since this filter will ask only for a subset of the input blocks,
it needs to replace the `COMPOSITE_DATA_META_DATA()` object with one
that takes out the blocks that will not be needed. This way, any
filter downstream will not ask for unnecessary blocks. The
following code identifies the blocks that may be loaded.

{% highlight python %}
for i in range(nblocks):
    bmd = metaData.GetMetaData(i)
    if self.CheckBounds(bmd.Get(vtk.vtkDataObject.BOUNDING_BOX())):
        self.__BlockMap[idx] = i
        idx += 1
{% endhighlight %}

It also makes a map from the output block id to the input block id.
This will be needed in `RequestUpdateExtent()` as we will see later.
Then we create a new multi-block meta-data object as follows.

{% highlight python %}
md = vtk.vtkMultiBlockDataSet()
for i in self.__BlockMap.keys():
    ii = self.__BlockMap[i]
    imd = metaData.GetMetaData(ii)
    bds = imd.Get(vtk.vtkDataObject.BOUNDING_BOX())
    md.SetBlock(i, None)
    bmd = md.GetMetaData(i)
    bmd.Set(vtk.vtkDataObject.BOUNDING_BOX(), bds, 6)

outInfo.GetInformationObject(0).Set(
    vtk.vtkCompositeDataPipeline.COMPOSITE_DATA_META_DATA(),
    md)
{% endhighlight %}

Fairly straightforward. Using the map, copy meta-data from
input to output. Now the output meta-data contains only blocks
that intersect the plane. There is one minor issue however.
Downstream filters will use an index space to request blocks
which is different than the index space for the input. The
good news is that we have a map to convert from one to another.
We use this in `RequestUpdateExtent()` as follows.

{% highlight python %}
def RequestUpdateExtent(self, request, inInfo, outInfo):

    # ...
    requestBlocks = []
    for i in uci:
        requestBlocks.append(self.__BlockMap[i])

    nblocks = len(requestBlocks)
    inInfo0.Set(
        vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES(),
        requestBlocks, len(requestBlocks))
{% endhighlight %}

Pretty easy. For each requested block (in `uci`), ask for the
corresponding input block by mapping it through the `BlockMap`
data member. By the way, `uci` is computed in a similar way
to the reader so it shouldn't need explanation.

Here you go. We can exercise these algorithms in the following
ways.

{% highlight python %}
r = HDF5Reader()
r.SetFileName("test.h5")

f = StreamBlocks()
f.SetInputConnection(r.GetOutputPort())
f.SetFileName("test2.h5")

f.Update()
{% endhighlight %}

This will produce a file identical to the input (`test.h5`).

{% highlight python %}
r = HDF5Reader()
r.SetFileName("test.h5")

c = PlaneCutter()
c.SetInputConnection(r.GetOutputPort())
c.SetOrigin((1, 0, 0))

c.Update()
print c.GetOutputDataObject(0)
{% endhighlight %}

For a `test.h5` created with 33 blocks, this will print a dataset
with 7 blocks, showing that only 7 blocks were loaded. These are
blocks with bounds intersecting the plane.

The following pipeline, with minor modifications to the writer,
would also work.

{% highlight python %}
r = HDF5Reader()
r.SetFileName("test.h5")

c = PlaneCutter()
c.SetInputConnection(r.GetOutputPort())
c.SetOrigin((1, 0, 0))

f = StreamBlocks()
f.SetInputConnection(c.GetOutputPort())
f.SetFileName("test2.h5")

f.Update()
{% endhighlight %}

For this to work, you have to change `StreamBlocks()` to
write a polydata instead of an unstructured grid (left to you
as an exercise). Once that change is made, this pipeline
will write 7 blocks of slices for a 33 blocks input dataset.

This is it folks. If you read all my blogs on the VTK pipeline,
you pretty much know everything necessary to put together very
sophisticated pipelines to solve all kinds of problems. Please
be sure to let us know on the VTK mailing list about any interesting
pipelines you put together.

In the future, I will switch gears and start talking about VTK's
data model as well as various ways of developing parallel algorithms.