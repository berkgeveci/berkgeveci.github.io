---
layout: post
title:  "Sending and receiving VTK data objects using MPI"
---

Someone asked me on Twitter if it is possible to send VTK objects to slave nodes using mpi4py. The
answer is sometimes. In the most general case, you need to use something like
[tvtk](http://docs.enthought.com/mayavi/tvtk/) to make use of mpi4py's ability to send/receive any
pickled Python object. Even then, tvtk does not pickle references to other VTK objects so you can't
send an arbitrary graph of objects using mpi4py.

In the less general case, one can use VTK communicators to send/receive data objects. Here is a
simple example:

{% highlight python %}
import vtk

c = vtk.vtkMultiProcessController.GetGlobalController()

rank = c.GetLocalProcessId()

if rank == 0:
    ssource = vtk.vtkSphereSource()
    ssource.Update()
    c.Send(ssource.GetOutput(), 1, 1234)
else:
    sphere = vtk.vtkPolyData()
    c.Receive(sphere, 0, 1234)
    print sphere
{% endhighlight %}

See the documentation for `vtkMultiProcessController` and `vtkMPIController` to see which methods
are available in C++. Note that not all of these methods are accessible in Python. It is also
possible to broadcast a data object as follows.

{% highlight python %}
import vtk

c = vtk.vtkMultiProcessController.GetGlobalController()

rank = c.GetLocalProcessId()

if rank == 0:
    ssource = vtk.vtkSphereSource()
    ssource.Update()
    sphere = ssource.GetOutput()
else:
    sphere = vtk.vtkPolyData()

c.Broadcast(sphere, 0)

if rank == 1:
    print sphere
{% endhighlight %}

Both of these methods depend on serializing a data object to a buffer using writers and reading
back using readers. The legacy readers and writers are used for this. Here is how one can
directly use this marshaling/unmarshaling capability with mpi4py:

{% highlight python %}
from vtk.numpy_interface import dataset_adapter as dsa
from mpi4py import MPI
comm = vtk.vtkMPI4PyCommunicator.ConvertToPython(c.GetCommunicator())
import numpy

if rank == 0:
    ssource = vtk.vtkSphereSource()
    ssource.Update()
    ca = vtk.vtkCharArray()
    vtk.vtkCommunicator.MarshalDataObject(ssource.GetOutput(), ca)
    a = dsa.vtkDataArrayToVTKArray(ca)
    comm.send(a.shape[0], 1)
    comm.Send([a, MPI.CHAR], 1)
else:
    sz = comm.recv()
    buff = numpy.empty(sz, dtype=numpy.int8)
    comm.Recv([buff, MPI.CHAR])
    pd = vtk.vtkPolyData()
    vtk.vtkCommunicator.UnMarshalDataObject(dsa.numpyTovtkDataArray(buff), pd)
    print pd
{% endhighlight %}

It would be fairly easy to extend this example to use non-blocking communication methods
available in MPI.

Finally, here is a list of data object types that are supported by the marshaling code:

* VTK_DIRECTED_GRAPH
* VTK_UNDIRECTED_GRAPH
* VTK_IMAGE_DATA
* VTK_POLY_DATA
* VTK_RECTILINEAR_GRID
* VTK_STRUCTURED_GRID
* VTK_STRUCTURED_POINTS
* VTK_TABLE
* VTK_TREE
* VTK_UNSTRUCTURED_GRID
* VTK_MULTIBLOCK_DATA_SET
* VTK_UNIFORM_GRID_AMR

I hope that this answers the question.

_Note: This article was originally published on the [Kitware blog](http://www.kitware.com/blog/home/post/721).
Please see the [Kitware web site](http://www.kitware.com), the [VTK web site](http://www.vtk.org) and the
[ParaView web site](http://www.paraview.org) for more information._

