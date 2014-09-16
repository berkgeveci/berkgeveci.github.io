---
layout: post
title:  "vtkPythonAlgorithm is great"
---

Here is the blog I meant to write [last time]({% post_url 2014-9-2-programmable-filter %}). In this
blog, I will actually talk about `vtkPythonAlgorithm`. I will also cover some VTK pipeline and
algorithm basics so those that want to start developing C++ algorithms will also benefit from
reading it.

As I covered previously, `vtkProgrammableFilter` is a great tool and useful for many purposes.
However, it has the following drawbacks:

* Its output type is always the same as its input type. So one cannot implement filters such as a
contour filter (which accepts a `vtkDataSet` and outputs a `vtkPolyData`) using it.
* It is not possible to properly manipulate pipeline execution by setting keys when using a
`vtkProgrammableFilter`.
* The source counterpart of `vtkProgrammableFilter`, `vtkProgrammableSource`, is very difficult to
use and is very limited.

We developed `vtkPythonAlgorithm` to remedy these issues. At its heart, `vtkPythonAlgorithm` is
very simple (although more complicated than `vtkProgrammableFilter`).

* It is an algorithm,
* You assign to it a Python object using `SetPythonObject()`,
* It calls `Initialize(self, vtkself)` on this Python object, passing a reference of itself,
* It delegates the following methods to the Python object:
    - `ProcessRequest(self, vtkself, request, inInfo, outInfo)`
    - `FillInputPortInformation(self, vtkself, port, info)`
    - `FillOutputPortInformation(self, vtkself, port, info)`

By implementing some of these 4 methods in your Python class, you have access to the entire
pipeline execution capability of VTK, including managing parallel execution, streaming, passing
arbitrary keys up and down the pipeline etc.

For those that are not familiar with how VTK algorithms work, it is worthwhile to explain what
these methods do.

**Initialize**: The main purpose of this method is to initialize the number of input and output
ports an algorithm has. This is normally done in a C++ algorithm's constructor. But since the
Python object's constructor is called _before_ it is passed to `vtkPythonAlgorithm`, we can't do
it there. Hence `Initialize()`. This method takes 1 argument : the `vtkPythonAlgorithm` calling it.
Here is a simple example:

{% highlight python %}
import vtk

class MyAlgorithm(object):
    def Initialize(self, vtkself):
        vtkself.SetNumberOfInputPorts(1)
        vtkself.SetNumberOfOutputPorts(1)
{% endhighlight %}

* 1 input port + 1 output port == your common VTK filter.
* 0 input port + 1 output port == your common VTK source.
* 1 input port + 0 output port == your common VTK sink (writer, mapper etc.).

**FillInputPortInformation and FillOutputPortInformation**: These methods are overwritten to
tell the VTK pipeline what data type an algorithm expects as input and what data type it will
produce. This information is used to do run-time sanity checking. It can also be used to ask
the pipeline to automatically create the output of the algorithm, if an concrete data type is
known when the algorithm is initialized.

Here is a simple example:

{% highlight python %}
import vtk

class MyAlgorithm(object):

    def FillInputPortInformation(self, vtkself, port, info):
        info.Set(vtk.vtkAlgorithm.INPUT_REQUIRED_DATA_TYPE(), "vtkDataSet")
        return 1

    def FillOutputPortInformation(self, vtkself, port, info):
        info.Set(vtk.vtkDataObject.DATA_TYPE_NAME(), "vtkPolyData")
        return 1
{% endhighlight %}

This is a classic VTK filter that accepts a `vtkDataSet` and produces `vtkPolyData`. Think a
contour filter, a streamline filter, a slice filter etc. Note that this is impossible to achieve
with `vtkProgrammableFilter`, which always produces the same type of output as input.

A few things to note here:

* `port` is an integer referring to the index of the current input or output port. These methods
are called once for each input and output port.
* `info` is a key-value store object (`vtkInformation`) used to hold meta-data about the current input
or output port. The keys are `vtkObject`s that are accessed through class methods. This allows VTK 
to avoid any key collisions while still supporting run-time addition of keys.
* If the output `DATA_TYPE_NAME()` is a concrete class name, the pipeline (executive) will create
the output data object for that port automatically before the filter executes. If it is the name of
an abstract class, it is the developer's responsibility to create the output data object later.

In addition to setting the input and output data types, these methods can be used to define
additional properties. Here are a few:

* `vtkAlgorithm.INPUT_IS_REPEATABLE()` : This means that a particular input port can accept
multiple connections. Think `vtkAppendFilter`.
* `vtkAlgorithm.INPUT_IS_OPTIONAL()` : Can be used to mark an input as optional. Which means that
it is not an error if a connection is not made to that port.

**ProcessRequest:** This is the meat of the algorithm. This method is called for each pipeline pass
VTK implements. It is used to ask the algorithm to create its output data object(s), to provide
meta-data to downstream, to modify a request coming from downstream and to fill the output data
object(s). Each of these pipeline passes are identified by the request type. Let's look at an
example:

{% highlight python %}
import vtk

class MyAlgorithm(object):
    def ProcessRequest(self, vtkself, request, inInfo, outInfo):
        if request.Has(vtk.vtkDemandDrivenPipeline.REQUEST_DATA()):
            print 'I am supposed to execute'
        return 1
{% endhighlight %}

The arguments need explaining:

* `request`: What the pipeline is asking of the algorithm. Common requests are 
    - `REQUEST_DATA_OBJECT()` : create your output data object(s)
    - `REQUEST_INFORMATION()` : provide meta-data for downstream
    - `REQUEST_UPDATE_EXTENT()` : modify any data coming from downstream or create a data request
(for sinks)
    - `REQUEST_DATA()` : do your thing. Take input data (if any), do something with it, produce
output data (if any)
* `inInfo` : a list of vectors of key-value store objects (`vtkInformation`). It is a list because
each member corresponds to an input port. The list contains vectors because each input port can
have multiple connections.
* `outInfo` : a vector of key-value store objects. Each entry in the vector corresponds to an
output port.

Let's put it all together

{% highlight python %}
import vtk

class MyAlgorithm(object):
    def Initialize(self, vtkself):
        vtkself.SetNumberOfInputPorts(1)
        vtkself.SetNumberOfOutputPorts(1)

    def FillInputPortInformation(self, vtkself, port, info):
        info.Set(vtk.vtkAlgorithm.INPUT_REQUIRED_DATA_TYPE(), "vtkDataSet")
        return 1

    def FillOutputPortInformation(self, vtkself, port, info):
        info.Set(vtk.vtkDataObject.DATA_TYPE_NAME(), "vtkPolyData")
        return 1

    def ProcessRequest(self, vtkself, request, inInfo, outInfo):
        if request.Has(vtk.vtkDemandDrivenPipeline.REQUEST_DATA()):
            print 'I am supposed to execute'
        return 1

w = vtk.vtkRTAnalyticSource()

pa = vtk.vtkPythonAlgorithm()
pa.SetPythonObject(MyAlgorithm())
pa.SetInputConnection(w.GetOutputPort())

pa.Update()
print pa.GetOutputDataObject(0).GetClassName()
print pa.GetOutputDataObject(0).GetNumberOfCells()
{% endhighlight %}

This will print:

{% highlight python %}
I am supposed to execute
vtkPolyData
0
{% endhighlight %}

## Dealing With Data

Let's change `ProcessRequest()` to accept input data and produce output data.

{% highlight python %}
1     def ProcessRequest(self, vtkself, request, inInfo, outInfo):
2         if request.Has(vtk.vtkDemandDrivenPipeline.REQUEST_DATA()):
3             inp = inInfo[0].GetInformationObject(0).Get(vtk.vtkDataObject.DATA_OBJECT())
4             opt = outInfo.GetInformationObject(0).Get(vtk.vtkDataObject.DATA_OBJECT())
5 
6             cf = vtk.vtkContourFilter()
7             cf.SetInputData(inp)
8             cf.SetValue(0, 200)
9 
10            sf = vtk.vtkShrinkPolyData()
11            sf.SetInputConnection(cf.GetOutputPort())
12            sf.Update()
13
14            opt.ShallowCopy(sf.GetOutput())
15        return 1
{% endhighlight %}

On line 3, we get the data object from the information object (key-value store) associated with the
first connection of the first port (`inInfo[0]` corresponds to all connections of the first port).
This is our input. `vtkDataObject.DATA_OBJECT()` is the key used to refer to input and output data
objects. On line 4, we get the data object associated with the first output port. This is our
output. Lines 6-12 create a simple pipeline. On line 14, we copy the output from the shrink filter
to the output of the `vtkPythonAlgorithm`.

When run, this filter will produce:

{% highlight python %}
vtkPolyData
3124
{% endhighlight %}

___Tip:___ Lines 3 and 4 can be simplified by using convenience functions as follows.

{% highlight python %}
3             inp = vtk.vtkDataSet.GetData(inInfo[0])
4             opt = vtk.vtkPolyData.GetData(outInfo)
{% endhighlight %}

## A Convenience Superclass

___Note:___ For what is described here, you need VTK from a very recent master. As of writing of
this blog, VTKPythonAlgorithmBase had been in VTK git master for only a few days.

Now that we covered the basics of `vtkPythonAlgorithm`, let me introduce a convenience class that
makes algorithms development a bit more convenient. Let's start with updating our previous example.

{% highlight python %}
1   import vtk
2   from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
3   
4   class ContourShrink(VTKPythonAlgorithmBase):
5       def __init__(self):
6           VTKPythonAlgorithmBase.__init__(self)
7   
8       def RequestData(self, request, inInfo, outInfo):
9           inp = vtk.vtkDataSet.GetData(inInfo[0])
10          opt = vtk.vtkPolyData.GetData(outInfo)
11  
12          cf = vtk.vtkContourFilter()
13          cf.SetInputData(inp)
14          cf.SetValue(0, 200)
15  
16          sf = vtk.vtkShrinkPolyData()
17          sf.SetInputConnection(cf.GetOutputPort())
18          sf.Update()
19  
20          opt.ShallowCopy(sf.GetOutput())
21  
22          return 1
23  
24  w = vtk.vtkRTAnalyticSource()
25  
26  pa = ContourShrink()
27  pa.SetInputConnection(w.GetOutputPort())
28  
29  pa.Update()
30  print pa.GetOutputDataObject(0).GetClassName()
31  print pa.GetOutputDataObject(0).GetNumberOfCells()
{% endhighlight %}

Neat huh? I am not going to explain how this works under the covers because it is a bit convoluted.
Suffice it to say that you can subclass `VTKPythonAlgorithmBase` to overwrite a number of methods
and also treat it as a `vtkPythonAlgorithm`. In fact, it is a subclass of `vtkPythonAlgorithm`.
The methods available to be overwritten are:

* `FillInputPortInformation(self, port, info)` : Same as described above. Except `self == vtkself`.
* `FillOutputPortInformation(self, port, info)` : Same as described above. Except `self == vtkself`.
* `RequestDataObject(self, request, inInfo, outInfo)` : This is where you can create output
data objects if the output `DATA_TYPE_NAME()` is not a concrete type.
* `RequestInformation(self, request, inInfo, outInfo)` : Provide meta-data downstream. More on this
on later blogs.
* `RequestUpdateExtent(self, request, inInfo, outInfo)` : Modify requests coming from downstream.
More on this on later blogs.
* `RequestData(self, request, inInfo, outInfo)` : Produce data. As described before.

In addtion, you can use the constructor to manage the number of input and output ports the static
input and output types (rather than overwriting `FillInputPortInformation()` and
`FillOutputPortInformation()`). For example, we could have done this:

{% highlight python %}
class ContourShrink(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkDataSet',
            nOutputPorts=1, outputType='vtkPolyData')
{% endhighlight %}

We didn't have to do this in our example because these happen to be the default values.

___Important___: You have to define an `__init__()` method that chains to `VTKPythonAlgorithmBase`
for all of this to work. Don't leave it out!

## Adding Parameters

This blog has gotten long. Let's look at one more capability to wrap up. Say you want to change the
contour value or the shrink factor. You could of course edit the class every time but since that's
lame, you'd probably rather use methods. There are a few things to know to get this right. Here is
an updated version:

{% highlight python %}
1   import vtk
2   from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
3   
4   class ContourShrink(VTKPythonAlgorithmBase):
5       def __init__(self):
6           VTKPythonAlgorithmBase.__init__(self,
7               nInputPorts=1, inputType='vtkDataSet',
8               nOutputPorts=1, outputType='vtkPolyData')
9   
10          self.__ShrinkFactor = 0.5
11          self.__ContourValue = 200
12  
13      def SetShrinkFactor(self, factor):
14          if factor != self.__ShrinkFactor:
15              self.__ShrinkFactor = factor
16              self.Modified()
17  
18      def GetShrinkFactor(self):
19          return self.__ShrinkFactor
20  
21      def SetContourValue(self, value):
22          if value != self.__ContourValue:
23              self.__ContourValue = value
24              self.Modified()
25  
26      def GetContourValue(self):
27          return self.__ContourValue
28  
29      def RequestData(self, request, inInfo, outInfo):
30          print 'Executing'
31          inp = vtk.vtkDataSet.GetData(inInfo[0])
32          opt = vtk.vtkPolyData.GetData(outInfo)
33  
34          cf = vtk.vtkContourFilter()
35          cf.SetInputData(inp)
36          cf.SetValue(0, self.__ContourValue)
37  
38          sf = vtk.vtkShrinkPolyData()
39          sf.SetShrinkFactor(self.__ShrinkFactor)
40          sf.SetInputConnection(cf.GetOutputPort())
41          sf.Update()
42  
43          opt.ShallowCopy(sf.GetOutput())
44  
45          return 1
46  
47  w = vtk.vtkRTAnalyticSource()
48  
49  pa = ContourShrink()
50  pa.SetInputConnection(w.GetOutputPort())
51  
52  pa.Update()
53  print pa.GetOutputDataObject(0).GetClassName()
54  print pa.GetOutputDataObject(0).GetNumberOfCells()
55  
56  pa.SetShrinkFactor(0.7)
57  pa.SetContourValue(100)
58  pa.Update()
59  print pa.GetOutputDataObject(0).GetClassName()
60  print pa.GetOutputDataObject(0).GetNumberOfCells()
{% endhighlight %}

This will print the following.

{% highlight python %}
Executing
vtkPolyData
3124
Executing
vtkPolyData
2516
{% endhighlight %}

There are a few things to note here:

* Instead of directly setting data members, we used setters and getters. The main reason behind
this is what happens on lines 16 and 24. Unless you call `Modified()` as shown, the filter will
not re-execute after you change a value.
* We did not use Python properties for `ShrinkFactor` and `ContourValue`. As nice as this would have
been, it is not currently possible. This is because `VTKPythonAlgorithmBase` derives from a wrapped
VTK class, which does not support properties. Properties are only supported by class that descend
from `object`.
* It is good practice to do the values comparisons on lines 14 and 22 to avoid unnecessary
re-execution of the filter.

## Next

We have covered a lot of ground. In my next blog, I will put what we learned to use to develop
a simple HDF5 reader. We will cover cool concepts such as providing meta-data in a reader and asking
for a subset in a filter. Until then cheers.


Special thanks to Ben Boeckel who developed `vtkPythonAlgorithm`.

_Note: This article was originally published on the [Kitware blog](http://www.kitware.com/blog/home/post/737).
Please see the [Kitware web site](http://www.kitware.com), the [VTK web site](http://www.vtk.org) and the
[ParaView web site](http://www.paraview.org) for more information._
