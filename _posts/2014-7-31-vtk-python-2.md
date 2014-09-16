---
layout: post
title:  "Improved VTK - numpy integration (part 2)"
---

This is my second blog about the recently introduced `numpy_interface` module. In the [first one]({% post_url 2014-7-28-vtk-python %}), I gave a brief overview of the module and shared a few teasers. In this one, I will go over the `dataset_adapter` module which is part of `numpy_interface`. This module was designed to simplify accessing VTK datasets and arrays from Python and to provide a numpy-style interface.

The first step to use the `dataset_adapter` module is to convert an existing VTK dataset object to a `dataset_adapter.VTKObjectWrapper`. Let's see how this is done by examining the teaser from the last blog:

{% highlight python %}
import vtk
from vtk.numpy_interface import dataset_adapter as dsa

s = vtk.vtkSphereSource()

e = vtk.vtkElevationFilter()
e.SetInputConnection(s.GetOutputPort())
e.Update()

sphere = dsa.WrapDataObject(e.GetOutput())

print sphere
print isinstance(sphere, dsa.VTKObjectWrapper)
{% endhighlight %}

will print:

{% highlight python %}
<vtk.numpy_interface.dataset_adapter.PolyData object at 0x1101fbb50>
True
{% endhighlight %}

What we did here is to create an instance of the `dataset_adapter.PolyData ` class, which refers to the output of the `vtkElevationFilter` filter. We can access the underlying VTK object using the `VTKObject` member:

{% highlight python %}
>> print type(sphere.VTKObject)
<type 'vtkobject'>
{% endhighlight %}

Note that the `WrapDataObject()` function will return an appropriate wrapper class for all `vtkDataSet` subclasses, `vtkTable` and all `vtkCompositeData` subclasses. Other `vtkDataObject` subclasses are not currently supported.

`VTKObjectWrapper` forwards VTK methods to its `VTKObject` so the VTK API can be accessed directy as follows:

{% highlight python %}
>> print sphere.GetNumberOfCells()
96L
{% endhighlight %}

However, `VTKObjectWrapper`s cannot be directly passed to VTK methods as an argument.

{% highlight python %}
>> s = vtk.vtkShrinkPolyData()
>> s.SetInputData(sphere)
TypeError: SetInputData argument 1: method requires a VTK object
>> s.SetInputData(sphere.VTKObject)
{% endhighlight %}

## Dataset Attributes ##

So far, pretty boring, right? We have a wrapper for VTK data objects that partially behaves like a VTK data object. This gets a little bit more interesting when we start looking how one can access the fields (arrays) contained within this dataset.

{% highlight python %}
>> sphere.PointData
<vtk.numpy_interface.dataset_adapter.DataSetAttributes at 0x110f5b750>

>> sphere.PointData.keys()
['Normals', 'Elevation']

>> sphere.CellData.keys()
[]

>> sphere.PointData['Elevation']
VTKArray([ 0.5       ,  0.        ,  0.45048442,  0.3117449 ,  0.11126047,
        0.        ,  0.        ,  0.        ,  0.45048442,  0.3117449 ,
        0.11126047,  0.        ,  0.        ,  0.        ,  0.45048442,
        ...,
        0.11126047,  0.        ,  0.        ,  0.        ,  0.45048442,
        0.3117449 ,  0.11126047,  0.        ,  0.        ,  0.        ], dtype=float32)

>> elevation = sphere.PointData['Elevation']

>> elevation[:5]
VTKArray([0.5, 0., 0.45048442, 0.3117449, 0.11126047], dtype=float32)
{% endhighlight %}

Note that this works with composite datasets as well:

{% highlight python %}
>> mb = vtk.vtkMultiBlockDataSet()
>> mb.SetNumberOfBlocks(2)
>> mb.SetBlock(0, sphere.VTKObject)
>> mb.SetBlock(1, sphere.VTKObject)
>> mbw = dsa.WrapDataObject(mb)
>> mbw.PointData
<vtk.numpy_interface.dataset_adapter.CompositeDataSetAttributes instance at 0x11109f758>

>> mbw.PointData.keys()
['Normals', 'Elevation']

>> mbw.PointData['Elevation']
<vtk.numpy_interface.dataset_adapter.VTKCompositeDataArray at 0x1110a32d0>
{% endhighlight %}

It is possible to access PointData, CellData, FieldData, Points (subclasses of vtkPointSet only), Polygons (vtkPolyData only) this way. We will continue to add accessors to more types of arrays through this API.

This is it for now. In my next blog in this series, I will talk about the array API and various algorithms the `numpy_interface` module provides.

_Note: This article was originally published on the [Kitware blog](http://www.kitware.com/blog/home/post/713).
Please see the [Kitware web site](http://www.kitware.com), the [VTK web site](http://www.vtk.org) and the
[ParaView web site](http://www.paraview.org) for more information._

