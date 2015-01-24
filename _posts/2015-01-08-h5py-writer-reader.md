---
layout: post
title: "HDF5 Reader and Writer for Unstructured Grids"
---

We are taking a quick break from the series of blogs on streaming. Instead,
in preparation for a discussion on block-based streaming, I will discuss how
you can write multi-block unstructured grid readers and writers in Python using
the `h5py` library. Let's get right down business. Here is the writer code.

{% highlight python %}
import vtk
import h5py
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtk.numpy_interface import dataset_adapter as dsa

class HDF5Writer(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkUnstructuredGrid',
            nOutputPorts=0)

        self.__FileName = ""
        self.__NumberOfPieces = 1
        self.__CurrentPiece = 0

    def RequestData(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        inp = dsa.WrapDataObject(vtk.vtkDataSet.GetData(info))

        if self.__CurrentPiece == 0:
              self.__File = h5py.File(self.__FileName, 'w')

        grp = self.__File.create_group("piece%d" % self.__CurrentPiece)
        grp.attrs['bounds'] = inp.GetBounds()

        grp.create_dataset("cells", data=inp.Cells)
        grp.create_dataset("cell_types", data=inp.CellTypes)
        grp.create_dataset("cell_locations", data=inp.CellLocations)

        grp.create_dataset("points", data=inp.Points)

        pdata = grp.create_group("point_data")
        for name in inp.PointData.keys():
            pdata.create_dataset(name, data=inp.PointData[name])

        if self.__CurrentPiece < self.__NumberOfPieces - 1:
            # If we are not done, ask the pipeline to re-execute us.
            self.__CurrentPiece += 1
            request.Set(
                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING(),
                1)
        else:
            # Stop execution
            request.Remove(
                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING())
            self.__File.close()
            del self.__File
        return 1

    def RequestInformation(self, request, inInfo, outInfo):
        # Reset values.
        self.__CurrentPiece = 0
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        info.Set(
            vtk.vtkStreamingDemandDrivenPipeline.UPDATE_NUMBER_OF_PIECES(),
            self.__NumberOfPieces)
        info.Set(
            vtk.vtkStreamingDemandDrivenPipeline.UPDATE_PIECE_NUMBER(),
            self.__CurrentPiece)
        return 1

    def SetFileName(self, fname):
        if fname != self.__FileName:
            self.Modified()
            self.__FileName = fname

    def GetFileName(self):
        return self.__FileName

    def SetNumberOfPieces(self, npieces):
        if npieces != self.__NumberOfPieces:
            self.Modified()
            self.__NumberOfPieces = npieces

    def GetNumberOfPieces(self):
        return self.__NumberOfPieces

{% endhighlight %}

First of all, this writer uses streaming as described in
[a previous blog]({% post_url 2014-11-26-streaming-space %}). See also
[this blog]({% post_url 2014-11-09-streaming-time %}) for a more detailed
description of how streaming works. The meat of the writer is actually just
a few lines:

{% highlight python %}
grp = self.__File.create_group("piece%d" % self.__CurrentPiece)
grp.attrs['bounds'] = inp.GetBounds()

grp.create_dataset("cells", data=inp.Cells)
grp.create_dataset("cell_types", data=inp.CellTypes)
grp.create_dataset("cell_locations", data=inp.CellLocations)

pdata = grp.create_group("point_data")
for name in inp.PointData.keys():
    pdata.create_dataset(name, data=inp.PointData[name])
{% endhighlight %}

This block of code writes the 3 data arrays specific to `vtkUnstructuredGrid`s:
cells, cell types and cell locations. In short, `cells` describes the connectivity
of cells (which points they contain), `cell_types` describe the type of each cell
and `cell_locations` stores the offset of each cell in the `cells` array for quick
random access. I will not describe these in further detail here.
See the VTK Users' Guide for more information. I also added support for point arrays.
Writing out cell arrays is left to you as an exercise.

Note that, in addition to writing these arrays, I wrote the spatial bounds of
each block as a meta-data (attribute). Why will become clear in the next blog (hint:
think demand-driven pipeline and streaming).

We can exercise this writer with the following code:

{% highlight python %}
s = vtk.vtkRTAnalyticSource()

c = vtk.vtkClipDataSet()
c.SetInputConnection(s.GetOutputPort())
c.SetValue(157)

w = HDF5Writer()
w.SetInputConnection(c.GetOutputPort())
w.SetFileName("test.h5")
w.SetNumberOfPieces(5)

w.Update()
{% endhighlight %}

This produces a file like this:

{% highlight sh %}
>>> h5ls -r test.h5
/                        Group
/piece0                  Group
/piece0/cell_locations   Dataset {4778}
/piece0/cell_types       Dataset {4778}
/piece0/cells            Dataset {26534}
/piece0/point_data       Group
/piece0/point_data/RTData Dataset {2402}
/piece0/points           Dataset {2402, 3}
/piece1                  Group
/piece1/cell_locations   Dataset {4609}
/piece1/cell_types       Dataset {4609}
/piece1/cells            Dataset {25609}
/piece1/point_data       Group
/piece1/point_data/RTData Dataset {2284}
/piece1/points           Dataset {2284, 3}
/piece2                  Group
/piece2/cell_locations   Dataset {4173}
/piece2/cell_types       Dataset {4173}
/piece2/cells            Dataset {23265}
/piece2/point_data       Group
/piece2/point_data/RTData Dataset {2156}
/piece2/points           Dataset {2156, 3}
/piece3                  Group
/piece3/cell_locations   Dataset {6065}
/piece3/cell_types       Dataset {6065}
/piece3/cells            Dataset {33073}
/piece3/point_data       Group
/piece3/point_data/RTData Dataset {2672}
/piece3/points           Dataset {2672, 3}
/piece4                  Group
/piece4/cell_locations   Dataset {5971}
/piece4/cell_types       Dataset {5971}
/piece4/cells            Dataset {32407}
/piece4/point_data       Group
/piece4/point_data/RTData Dataset {2574}
/piece4/points           Dataset {2574, 3}
{% endhighlight %}

Here is a very simple reader for this data:

{% highlight python %}
import vtk, h5py
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtk.numpy_interface import dataset_adapter as dsa

class HDF5Reader(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=0,
            nOutputPorts=1, outputType='vtkMultiBlockDataSet')

        self.__FileName = ""

    def RequestData(self, request, inInfo, outInfo):
        output = dsa.WrapDataObject(vtk.vtkMultiBlockDataSet.GetData(outInfo))
        f = h5py.File(self.__FileName, 'r')
        idx = 0
        for grp_name in f:
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

        return 1

    def SetFileName(self, fname):
        if fname != self.__FileName:
            self.Modified()
            self.__FileName = fname

    def GetFileName(self):
        return self.__FileName

{% endhighlight %}

This is for the most part self-explanatory (you may want to take a quick
look at the [h5py documentation](http://docs.h5py.org/en/2.3/quick.html)).
It is mostly a matter of mapping HDF5 groups and datasets to VTK data
structures:

{% highlight python %}
# Access the group containing the current block
grp = f[grp_name]
# Read unstructured grip topology
cells = grp['cells'][:]
locations = grp['cell_locations'][:]
types = grp['cell_types'][:]
# Set the topology data structures
ug.SetCells(types, locations, cells)
# Read and set the points
pts = grp['points'][:]
ug.Points = pts
# Read and set the point arrays
pt_arrays = grp['point_data']
for pt_array in pt_arrays:
    array = pt_arrays[pt_array][:]
    ug.PointData.append(array, pt_array)

{% endhighlight %}

In the next article, we will discover how we can extend this reader to
support block-based streaming. Until then, happy coding.
