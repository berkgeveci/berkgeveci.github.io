---
layout: post
title:  "Improved VTK - numpy integration (part 5)"
---

Welcome to my last blog in the series where we  to discover VTK's
`numpy_interface` module. If you are not familiar with this module, I
recommend checking out my previous blogs on it ([[1]({% post_url 2014-7-28-vtk-python %})], 
[[2]({% post_url 2014-7-31-vtk-python-2 %})], [[3]({% post_url 2014-8-7-vtk-python-3 %})]).
In this blog, I will talk about how one can work with composite datasets and arrays using 
this module.

Let's start with defining what a composite dataset is. From a class point of view, it is
`vtkCompositeDataSet` or any of its subclasses. From a functionality point of view, it is a way of
collecting together a set of `vtkDataObject`s (usually `vtkDataSet`s). The most generic example is
`vtkMultiBlockDataSet` which allows the creation of an arbitrary tree of `vtkDataObject`s.
Another example is `vtkOverlappingAMR` which represent a Berger-Colella style AMR meshes. Here is
how we can create a multi-block dataset.

{% highlight python %}
>>> import vtk
>>> s = vtk.vtkSphereSource()
>>> s.Update()
>>> c = vtk.vtkConeSource()
>>> c.Update()
>>> mb = vtk.vtkMultiBlockDataSet()
>>> mb.SetBlock(0, s.GetOutput())
>>> mb.SetBlock(1, c.GetOutput())
{% endhighlight %}

Many of VTK's algorithms work with composite datasets without any change. For example:

{% highlight python %}
>>> e = vtk.vtkElevationFilter()
>>> e.SetInputData(mb)
>>> e.Update()
>>> mbe = e.GetOutputDataObject(0)
>>> print mbe.GetClassName()
{% endhighlight %}

This will output `'vtkMultiBlockDataSet'`. Note that I used `GetOutputDataObject()` rather than
`GetOutput()`. `GetOutput()` is simply a `GetOutputDataObject()` wrapped with a `SafeDownCast()`
to the expected output type of the algorithm - which in this case is a `vtkDataSet`. So
`GetOutput()` will return `0` even when `GetOutputDataObject()` returns an actual composite
dataset.

Now that we have a composite dataset with a scalar, we can use `numpy_interface`.

{% highlight python %}
>>> from vtk.numpy_interface import dataset_adapter as dsa
>>> mbw = dsa.WrapDataObject(mbe)
>>> mbw.PointData.keys()
['Normals', 'Elevation']
>>> elev = mbw.PointData['Elevation']
>>> elev
<vtk.numpy_interface.dataset_adapter.VTKCompositeDataArray at 0x1189ee410>
{% endhighlight %}

Note that the array type is different than we have seen previously (`VTKArray`). However, it still
works the same way.

{% highlight python %}
>>> from vtk.numpy_interface import algorithms as algs
>>> algs.max(elev)
0.5
>>> algs.max(elev + 1)
1.5
{% endhighlight %}

You can individually access the arrays of each block as follows.

{% highlight python %}
>>> elev.Arrays[0]
VTKArray([ 0.5       ,  0.        ,  0.45048442,  0.3117449 ,  0.11126047,
        0.        ,  0.        ,  0.        ,  0.45048442,  0.3117449 ,
        0.11126047,  0.        ,  0.        ,  0.        ,  0.45048442,
        0.3117449 ,  0.11126047,  0.        ,  0.        ,  0.        ,
        0.45048442,  0.3117449 ,  0.11126047,  0.        ,  0.        ,
        0.        ,  0.45048442,  0.3117449 ,  0.11126047,  0.        ,
        0.        ,  0.        ,  0.45048442,  0.3117449 ,  0.11126047,
        0.        ,  0.        ,  0.        ,  0.45048442,  0.3117449 ,
        0.11126047,  0.        ,  0.        ,  0.        ,  0.45048442,
        0.3117449 ,  0.11126047,  0.        ,  0.        ,  0.        ], dtype=float32)

{% endhighlight %}

Note that indexing is slightly different.

{% highlight python %}
>>> print elev[0:3]
[VTKArray([ 0.5,  0.,  0.45048442], dtype=float32),
 VTKArray([ 0.,  0.,  0.43301269], dtype=float32)]
{% endhighlight %}

The return value is a composite array consisting of 2 `VTKArray`s. The `[]` operator simply returned
the first 4 values of each array. In general, all indexing operations apply to each `VTKArray` in
the composite array collection. Similarly for algorithms such as `where`.

{% highlight python %}
>>> print algs.where(elev < 0.5)
[(array([ 1,  2,  3,  4,  5,  6,  7,  8,  9, 10, 11, 12, 13, 14, 15, 16, 17,
       18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34,
       35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49]),),
       (array([0, 1, 2, 3, 4, 5, 6]),)]
{% endhighlight %}

Now, let's look at the other array called `Normals`.

{% highlight python %}
>>> normals = mbw.PointData['Normals']
>>> normals.Arrays[0]
VTKArray([[  0.00000000e+00,   0.00000000e+00,   1.00000000e+00],
       [  0.00000000e+00,   0.00000000e+00,  -1.00000000e+00],
       [  4.33883727e-01,   0.00000000e+00,   9.00968850e-01],
       [  7.81831503e-01,   0.00000000e+00,   6.23489797e-01],
       [  9.74927902e-01,   0.00000000e+00,   2.22520933e-01],
       ...
       [  6.89378142e-01,  -6.89378142e-01,   2.22520933e-01],
       [  6.89378142e-01,  -6.89378142e-01,  -2.22520933e-01],
       [  5.52838326e-01,  -5.52838326e-01,  -6.23489797e-01],
       [  3.06802124e-01,  -3.06802124e-01,  -9.00968850e-01]], dtype=float32)
>>> normals.Arrays[1]
<vtk.numpy_interface.dataset_adapter.VTKNoneArray at 0x1189e7790>
{% endhighlight %}

Notice how the second arrays is a `VTKNoneArray`. This is because `vtkConeSource` does not produce
normals. Where an array does not exist, we use a `VTKNoneArray` as placeholder. This allows us to
maintain a one-to-one mapping between datasets of a composite dataset and the arrays in the
`VTKCompositeDataArray`. It also allows us to keep algorithms working in parallel without a lot
of specialized code (see my [previous blog](http://www.kitware.com/blog/home/post/720)).

Where many of the algorithms apply independently to each array in a collection, some algorithms are
global. For example, `min` and `max` as we demonstrated above. It is sometimes useful to get per
block answers. For this, you can use `_per_block` algorithms.

{% highlight python %}
>>> print algs.max_per_block(elev)
[VTKArray(0.5, dtype=float32), VTKArray(0.4330126941204071, dtype=float32)]
{% endhighlight %}

These work very nicely together with other operations. For example, here is how we can normalize
the elevation values in each block.

{% highlight python %}
>>> _min = algs.min_per_block(elev)
>>> _max = algs.max_per_block(elev)
>>> _norm = (elev - _min) / (_max - _min)
>>> print algs.min(_norm)
0.0
>>> print algs.max(_norm)
1.0
{% endhighlight %}

Once you grasp these features, you should be able to use composite array very similarly to single
arrays as described in previous blogs.

A final note on composite datasets. The composite data wrapper provided by
`numpy_interface.dataset_adapter` offers a few convenience functions to traverse composite datasets.
Here is a simple example:

{% highlight python %}
>>> for ds in mbw:
>>>    print type(ds)
<class 'vtk.numpy_interface.dataset_adapter.PolyData'>
<class 'vtk.numpy_interface.dataset_adapter.PolyData'>
{% endhighlight %}

This wraps up the blog series on `numpy_interface`. I hope to follow these up with some concrete
examples of the module in action and some other useful information on using VTK from Python. Until
then, cheers.

_Note: This article was originally published on the [Kitware blog](http://www.kitware.com/blog/home/post/723).
Please see the [Kitware web site](http://www.kitware.com), the [VTK web site](http://www.vtk.org) and the
[ParaView web site](http://www.paraview.org) for more information._
