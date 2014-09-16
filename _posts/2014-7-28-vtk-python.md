---
layout: post
title:  "Improved VTK - numpy integration"
---

Recently, we have introduced a new Python module called `numpy_interface` to VTK. The main objective of this module is to make it easier to interface VTK and numpy. This article is the first in a series that introduces this module. Let's start with a teaser.

{% highlight python %}
import vtk

from vtk.numpy_interface import dataset_adapter as dsa
from vtk.numpy_interface import algorithms as algs 

s = vtk.vtkSphereSource()

e = vtk.vtkElevationFilter()
e.SetInputConnection(s.GetOutputPort())
e.Update()

sphere = dsa.WrapDataObject(e.GetOutput())

print sphere.PointData.keys()
print sphere.PointData['Elevation']
{% endhighlight %}

This example prints out the following (assuming that you have a relatively new checkout of VTK master from git).

    ['Normals', 'Elevation']
    [ 0.5         0.          0.45048442  0.3117449   0.11126047  0.          0.
      0.          0.45048442  0.3117449   0.11126047  0.          0.          0.
      0.45048442  0.3117449   0.11126047  0.          0.          0.
      0.45048442  0.3117449   0.11126047  0.          0.          0.
      0.45048442  0.3117449   0.11126047  0.          0.          0.
      0.45048442  0.3117449   0.11126047  0.          0.          0.
      0.45048442  0.3117449   0.11126047  0.          0.          0.
      0.45048442  0.3117449   0.11126047  0.          0.          0.        ]

The last 3 lines are what is new. Note how we used a different API to access the PointData and the Elevation array on the last 2 lines. Also note that when we printed the Elevation array, the output didn't look like one from a vtkDataArray. In fact:

{% highlight python %}
elevation = sphere.PointData['Elevation']
print type(elevation)
import numpy
print isinstance(elevation, numpy.ndarray)
{% endhighlight %}

prints the following.

    <class 'vtk.numpy_interface.dataset_adapter.VTKArray'>
    True

So a VTK array is a numpy array? What kind of trickery is this you say? What kind of magic makes the following possible?

{% highlight python %}
sphere.PointData.append(elevation + 1, 'e plus one')
print algs.max(elevation)
print algs.max(sphere.PointData['e plus one'])
print sphere.VTKObject
{% endhighlight %}

Output:

    0.5
    1.5
    vtkPolyData (0x7fa20d011c60)
      ...
      Point Data:
        ...
        Number Of Arrays: 3
        Array 0 name = Normals
        Array 1 name = Elevation
        Array 2 name = e plus one

It is all in the `numpy_interface` module. It ties VTK datasets and data arrays to numpy arrays and introduces a number of algorithms that can work on these objects. There is quite a bit to this module and I will introduce it piece by piece in upcoming blogs.

Let's wrap up this blog with one final teaser:

{% highlight python %}
w = vtk.vtkRTAnalyticSource() 

t = vtk.vtkDataSetTriangleFilter()
t.SetInputConnection(w.GetOutputPort())
t.Update() 

ugrid = dsa.WrapDataObject(t.GetOutput())
print algs.gradient(ugrid.PointData['RTData'])
{% endhighlight %}

Output:

    [[ 25.46767712   8.78654003   7.28477383]
     [  6.02292252   8.99845123   7.49668884]
     [  5.23528767   9.80230141   8.3005352 ]
     ...,
     [ -6.43249083  -4.27642155  -8.30053616]
     [ -5.19838905  -3.47257614  -7.49668884]
     [ 13.42047501  -3.26066017  -7.28477287]]

Please note that this example is not very easily replicated by using pure numpy. The `gradient` function returns the gradient of an unstructured grid - a concept that does not exist in numpy. However, the ease-of-use of numpy is there.

Stay tuned for more.

_Note: This article was originally published on the [Kitware blog](http://www.kitware.com/blog/home/post/709).
Please see the [Kitware web site](http://www.kitware.com), the [VTK web site](http://www.vtk.org) and the
[ParaView web site](http://www.paraview.org) for more information._
