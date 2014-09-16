---
layout: post
title:  "Improved VTK - numpy integration (part 3)"
excerpt: "So far, I have briefly introduced the numpy_interface module and discussed the dataset interface. Finally, we get to something more interesting: working with arrays, datasets and algorithms. This is where the numpy_interface shines and makes certain data analysis tasks significantly easier."
---

So far, I have briefly [introduced]({% post_url 2014-7-28-vtk-python %}) the `numpy_interface` module and [discussed the dataset interface]({% post_url 2014-7-31-vtk-python-2 %}). Finally, we get to something more interesting: working with arrays, datasets and algorithms. This is where the `numpy_interface` shines and makes certain data analysis tasks significantly easier. Let's start with a simple example.

{% highlight python %}
from vtk.numpy_interface import dataset_adapter as dsa
from vtk.numpy_interface import algorithms as algs
import vtk

w = vtk.vtkRTAnalyticSource()
w.Update()
image = dsa.WrapDataObject(w.GetOutput())
rtdata = image.PointData['RTData']

tets = vtk.vtkDataSetTriangleFilter()
tets.SetInputConnection(w.GetOutputPort())
tets.Update()
ugrid = dsa.WrapDataObject(tets.GetOutput())
rtdata2 = ugrid.PointData['RTData']
{% endhighlight %}

Here we created two datasets: an image data (vtkImageData) and an unstructured grid (vtkUnstructuredGrid). They essentially represent the same data but the unstructured grid is created by tetrahedralizing the image data. So we expect that unstructured grid to have the same points but more cells (tetrahedra).

## Array API

`Numpy_interface` array objects behave very similar to numpy arrays. In fact, arrays from `vtkDataSet` subclasses are instances of `VTKArray`, which is a subclass of `numpy.ndarray`. Arrays from `vtkCompositeDataSet` and subclasses are not numpy arrays but behave very similarly. I will outline the differences in a separate article. Let's start with the basics. All of the following work as expected.

{% highlight python %}
>>> rtdata[0]
60.763466

>>> rtdata[-1]
57.113735

>>> rtdata[0:10:3]
VTKArray([  60.76346588,   95.53707886,   94.97672272,  108.49817657], dtype=float32)

>>> rtdata + 1
VTKArray([ 61.
76346588,  86.87795258,  73.80931091, ...,  68.51051331,
        44.34006882,  58.1137352 ], dtype=float32)

>>> rtdata < 70
VTKArray([ True , False, False, ...,  True,  True,  True], dtype=bool)

# We will cover algorithms later. This is to generate a vector field.
>>> avector = algs.gradient(rtdata)

# To demonstrate that avector is really a vector
>>> algs.shape(rtdata)
(9261,)

>>> algs.shape(avector)
(9261, 3)

>>> avector[:, 0]
VTKArray([ 25.69367027,   6.59600449,   5.38400745, ...,  -6.58120966,
        -5.77147198,  13.19447994])
{% endhighlight %}

A few things to note in this example:

* Single component arrays always have the following shape: (ntuples,) and not (ntuples, 1)
* Multiple component arrays have the following shape: (ntuples, ncomponents)
* Tensor arrays have the following shape: (ntuples, 3, 3)
* The above holds even for images and other structured data. All arrays have 1 dimension (1 component arrays), 2 dimensions (multi-component arrays) or 3 dimensions (tensor arrays).

One more cool thing. It is possible to use boolean arrays to index arrays. So the following works very nicely:

{% highlight python %}
>>> rtdata[rtdata < 70]
VTKArray([ 60.76346588,  66.75043488,  69.19681549,  50.62128448,
        64.8801651 ,  57.72655106,  49.75050354,  65.05570221,
        57.38450241,  69.51113129,  64.24596405,  67.54656982,
        ...,
        61.18143463,  66.61872864,  55.39360428,  67.51051331,
        43.34006882,  57.1137352 ], dtype=float32)

>>> avector[avector[:,0] > 10]
VTKArray([[ 25.69367027,   9.01253319,   7.51076698],
       [ 13.1944809 ,   9.01253128,   7.51076508],
       [ 25.98717642,  -4.49800825,   7.80427408],
       ...,
       [ 12.9009738 , -16.86548471,  -7.80427504],
       [ 25.69366837,  -3.48665428,  -7.51076889],
       [ 13.19447994,  -3.48665524,  -7.51076794]])
{% endhighlight %}

## Algorithms

One can do a lot simply using the array API. However, things get much more interesting when we start using the `numpy_interface.algorithms` module. I introduced it briefly in the previous examples. I will expand on it a bit more here. For a full list of algorithms, use `help(algs)`. Here are some self-explanatory examples:

{% highlight python %}
>> algs.sin(rtdata)
VTKArray([-0.87873501, -0.86987603, -0.52497   , ..., -0.99943125,
       -0.59898132,  0.53547275], dtype=float32)

>>> algs.min(rtdata)
VTKArray(37.35310363769531)

>>> algs.max(avector)
VTKArray(34.781060218811035)

>>> algs.max(avector, axis=0)
VTKArray([ 34.78106022,  29.01940918,  18.34743023])

>>> algs.max(avector, axis=1)
VTKArray([ 25.69367027,   9.30603981,   9.88350773, ...,  -4.35762835,
        -3.78016186,  13.19447994])
{% endhighlight %}

If you haven't used the axis argument before, it is pretty easy. When you don't pass an axis value, the function is applied to all values of an array without any consideration for dimensionality. When axis=0, the function will be applied to each component of the array independently. When axis=1, the function will be applied to each tuple independently. Experiment if this is not clear to you. Functions that work this way include sum, min, max, std and var.

Another interesting and useful function is `where` which returns the indices of an array where a particular condition occurs.

{% highlight python %}
>>> algs.where(rtdata < 40)
(array([ 420, 9240]),)
{% endhighlight %}

For vectors, this will also return the component index if an axis is not defined.

{% highlight python %}
>>> algs.where(avector < -29.7)
(VTKArray([4357, 4797, 4798, 4799, 5239]), VTKArray([1, 1, 1, 1, 1]))
{% endhighlight %}

So far, all of the functions that we discussed are directly provided by numpy. Many of the numpy ufuncs are included in the `algorithms` module. They all work with single arrays and composite data arrays (more on this on another blog). `Algorithms` also provides some functions that behave somewhat differently than their numpy counterparts. These include `cross`, `dot`, `inverse`, `determinant`,  `eigenvalue`, `eigenvector` etc. All of these functions are applied to each tuple rather than to a whole array/matrix. For example:

~~~python
>>> amatrix = algs.gradient(avector)
>>> algs.determinant(amatrix)
VTKArray([-1221.2732624 ,  -648.48272183,    -3.55133937, ...,    28.2577152 ,
        -629.28507693, -1205.81370163])
~~~

Note that everything above only leveraged per-tuple information and did not rely on the mesh. One of VTK's biggest strengths is that its data model supports a large variety of meshes and its algorithms work generically on all of these mesh types. The `algorithms` module exposes some of this functionality. Other functions can be easily implemented by leveraging existing VTK filters. I used `gradient` before to generate a vector and a matrix. Here it is again

~~~python
>>> avector = algs.gradient(rtdata)
>>> amatrix = algs.gradient(avector)
~~~

Functions like this require access to the dataset containing the array and the associated mesh. This is one of the reasons why we use a subclass of `ndarray` in `dataset_adapter`:

~~~python
>>> rtdata.DataSet
<vtk.numpy_interface.dataset_adapter.DataSet at 0x11b61e9d0>
~~~

Each array points to the dataset containing it. Functions such as gradient use the mesh and the array together.Numpy provides a gradient function too, you say. What is so exciting about yours? Well, this:

~~~python
>>> algs.gradient(rtdata2)
VTKArray([[ 25.46767712,   8.78654003,   7.28477383],
       [  6.02292252,   8.99845123,   7.49668884],
       [  5.23528767,   9.80230141,   8.3005352 ],
       ...,
       [ -6.43249083,  -4.27642155,  -8.30053616],
       [ -5.19838905,  -3.47257614,  -7.49668884],
       [ 13.42047501,  -3.26066017,  -7.28477287]])
>>> rtdata2.DataSet.GetClassName()
'vtkUnstructuredGrid'
~~~

`Gradient` and algorithms that require access to a mesh work whether that mesh is a uniform grid or a curvilinear grid or an unstructured grid thanks to VTK's data model. Take a look at various functions in the `algorithms` module to see all the cool things that can be accomplished using it. I will write future blogs that demonstrate how specific problems can be solved using these modules.

All of this work with composite datasets and in parallel using MPI. I will cover some specific details about these in future blogs.

_Note: This article was originally published on the [Kitware blog](http://www.kitware.com/blog/home/post/714).
Please see the [Kitware web site](http://www.kitware.com), the [VTK web site](http://www.vtk.org) and the
[ParaView web site](http://www.paraview.org) for more information._
