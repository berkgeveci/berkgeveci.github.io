---
layout: post
title:  "Improved VTK - numpy integration (part 4)"
---

Welcome to another blog where we continue to discover VTK's `numpy_interface` module. If you are not familiar with this module, I recommend checking out my previous blogs on it ([[1]({% post_url 2014-7-28-vtk-python %})], [[2]({% post_url 2014-7-31-vtk-python-2 %})], [[3]({% post_url 2014-8-7-vtk-python-3 %})]). In this blog, I will talk about how `numpy_interface` can be used in a data parallel way. We will be using VTK's MPI support for this - through VTK's own vtkMultiProcessController and mpi4py. You may want to check [my last blog](http://www.kitware.com/blog/home/post/716) on VTK's mpi4py integration for some details.

Let's get started. First, if you want to run these examples yourself, make sure that VTK is compiled with MPI support on by setting VTK_Group_MPI to ON during the CMake configuration step. The simplest way to run these examples is to use the pvtkpython executable that gets compiled when Python and MPI support are on. Pvtkpython can be run from the command line as follows (check out your MPI documentation for details).

~~~
mpiexec -n 3 ./bin/pvtkpython
~~~

Now, let's start with a simple example.

{% highlight python %}
import vtk

c = vtk.vtkMultiProcessController.GetGlobalController()

rank = c.GetLocalProcessId()
size = c.GetNumberOfProcesses()

w = vtk.vtkRTAnalyticSource()
w.UpdateInformation()
w.SetUpdateExtent(rank, size, 0)
w.Update()

print w.GetOutput().GetPointData().GetScalars().GetRange()
{% endhighlight %}

When I run this example on my laptop, I get the following output:

{% highlight python %}
(37.35310363769531, 251.69105529785156)
(49.75050354003906, 276.8288269042969)
(37.35310363769531, 266.57025146484375)
{% endhighlight %}

Depending on a particular run and your OS, you may see something similar or something a bit garbled. Since I didn't restrict the `print` call to a particular rank, all processes will print out roughly at the same time and depending on the timing and buffering, may end up mixing up with each others' output. If you examine the output above, you will notice that the overall range of the scalars is (37.35310363769531, 276.8288269042969), which we can confirm by running the example serially.

Note that `vtkRTAnalyticSource` is a parallel-aware source and produces partitioned data. The following lines are what tell `vtkRTAnalyticSource` to produce its output in a distributed way

{% highlight python %}
w = vtk.vtkRTAnalyticSource()

# First we need to ask the source to produce
# meta-data. Unless UpdateInformation() is
# called first, SetUpdateExtent() below will
# have no effect
w.UpdateInformation()

# Ask the source to produce "size" pieces and
# select the piece of index "rank" for this process.
w.SetUpdateExtent(rank, size, 0)

# Cause execution. Note that the source has to
# be updated directly for the above request to
# work. Otherwise, downstream pipeline can overwrite
# requested piece information.
w.Update()
{% endhighlight %}

For more details, see [this page](http://www.vtk.org/Wiki/VTK/Parallel_Pipeline).

So how can we find out the global min and max of the scalars (RTData) array? One way is to use mpi4py to perform a reduction of local values of each process. Or we can use the `numpy_interface.algorithms` module. Add the following code to the end of our example.

{% highlight python %}
from vtk.numpy_interface import dataset_adapter as dsa
from vtk.numpy_interface import algorithms as algs

w = dsa.WrapDataObject(w.GetOutput())
rtdata = w.PointData['RTData']
_min = algs.min(rtdata)
_max = algs.max(rtdata)

if rank == 0:
    print _min, _max
{% endhighlight %}

This should print the following.

{% highlight python %}
37.3531036377 276.828826904
{% endhighlight %}

That simple! All algorithms in the `numpy_interface.algorithms` module work properly in parallel. Note that `min`, `max` and any other parallel algorithm will return the same value on all ranks.

It is possible to force these algorithms to produce local values by setting their controller argument as follows.

{% highlight python %}
# vtkDummyController is a replacement for vtkMPIController
# that works only locally to each rank.
_min = algs.min(rtdata, controller = vtk.vtkDummyController())
_max = algs.max(rtdata, controller = vtk.vtkDummyController())

if rank == 0:
    print _min, _max
{% endhighlight %}

This will print the following.

{% highlight python %}
37.3531036377 251.691055298
{% endhighlight %}

All algorithms in the `numpy_interface.algorithms` module were designed to work in parallel. If you use numpy algorithms directly, you will have to use mpi4py and do the proper reduction.

One final thing. `Numpy.dataset_adapter` and `numpy.algorithms` were designed to work properly even when an array does not exist on one or more of the ranks. This occurs when a source can produce a limited number of pieces (1 being the most common case) and the size of the parallel job is larger. Let's start with an example:

{% highlight python %}
import vtk

c = vtk.vtkMultiProcessController.GetGlobalController()

rank = c.GetLocalProcessId()
size = c.GetNumberOfProcesses()

c = vtk.vtkCubeSource()
c.UpdateInformation()
c.SetUpdateExtent(rank, size, 0)
c.Update()

from vtk.numpy_interface import dataset_adapter as dsa
from vtk.numpy_interface import algorithms as algs

c = dsa.WrapDataObject(c.GetOutput())
normals = c.PointData['Normals']

print normals
{% endhighlight %}

On my machine, this prints out the following.

{% highlight python %}
<vtk.numpy_interface.dataset_adapter.VTKNoneArray object at 0x119176490>
<vtk.numpy_interface.dataset_adapter.VTKNoneArray object at 0x11b128490>
[[-1.  0.  0.]
 [-1.  0.  0.]
 [-1.  0.  0.]
 [-1.  0.  0.]
 ...
 [ 0.  0.  1.]
 [ 0.  0.  1.]]
{% endhighlight %}

Note how the normals is a `VTKNoneArray` on 2 of the ranks. This is because `vtkCubeSource` is not parallel-aware and will produce output only on the first rank. On all other ranks, it will produce empty output. Consider the use case where we want to do something like this with normals.

{% highlight python %}
print algs.max(normals + 1)
{% endhighlight %}

One would expect that this would throw an exception on ranks where the normals array does not exist. In fact, the first implementation of the `numpy_interface.dataset_adapter` returned a `None` object and threw an exception in such cases as expected. However, this design had a significant flaw. Because of the exception, ranks that did not have the array could not participate in the calculation of global values, which are calculated by performing `MPI_Allreduce`. This function will hang unless all ranks participate in the reduction. We addressed this flaw by developing the `VTKNoneArray` class. This class supports all operators that regular arrays support and always returns `VTKNoneArray`. Furthermore, parallel algorithms function properly when asked to work on a `VTKNoneArray`.

We have covered a lot ground so far. In the next blog, which will be the last one in this series, I will talk about composite datasets and composite arrays.

_Note: This article was originally published on the [Kitware blog](http://www.kitware.com/blog/home/post/720).
Please see the [Kitware web site](http://www.kitware.com), the [VTK web site](http://www.vtk.org) and the
[ParaView web site](http://www.paraview.org) for more information._

