---
layout: post
title: "Streaming in VTK : Time"
---

With this blog, I am starting another series. This time we will cover streaming
in VTK. In this context, we define streaming as the process of sequentially
executing a pipeline over a collection of subsets of data. Example of streaming
include streaming over time, over logical extents, over partitions and over
ensemble members. Streaming belongs to set of techniques referred to as out-of-core
data processing techniques. Its main objective is to analyze a dataset that will not fit
in memory by breaking it into smaller pieces and processing each piece sequentially.

In this article, I will cover streaming over time. In future
ones, we will dig into other types of streaming. I am assuming that you understand
the basics of how the VTK pipeline works including pipeline passes and using
keys to provide meta-data and to make requests. If you are not familiar with these
concepts, I recommend checking out my previous blogs, specially
[[1]({% post_url 2014-09-18-pipeline %})], [[2]({% post_url 2014-10-05-pipeline-2 %})]
and [[3]({% post_url 2014-10-26-pipeline-3 %})].

## Problem statement

Let's look at a flow-field defined over a 2D uniform rectilinear grid. We will
pick a viscous flow that has a known closed-form solution so that we don't have to
write a solver. I chose a problem from my favorite graduate level fluid mechanics book:
Panton's "Incompressible Flow". From section 11.2, flow over Stoke's oscillating
plate is a great example. Without getting into a lot of details, the solution for
this problem is as follows.

![Stoke's plate](/assets/flow-over-plate.png)

This is a nice flow-field to study because it is very simple but is still time variant. This
profile looks as follows (click to animate):

<figure>
<img src="/assets/profile0.png" alt="Animation" style="margin-left:auto; margin-right:auto" onclick='javascript:this.src="/assets/profile.gif"'/>
</figure>

The code I used to generate this animation is [here](https://github.com/berkgeveci/berkgeveci.github.io/blob/jekyll/code/2014-11-06-temporal/plot.py).

## Source

Let's codify this flow field as a VTK source. Even though, the flow field is
really 1D (function of y only), we'll use a 2D uniform grid (vtkImageData) such
that we can advect particles later to further demonstrate temporal streaming.

{% highlight python %}
1    import numpy as np
2    import vtk
3    from vtk.numpy_interface import dataset_adapter as dsa
4    from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
5
6    t = np.linspace(0, 2*np.pi, 20)
7
8    class VelocitySource(VTKPythonAlgorithmBase):
9      def __init__(self):
10       VTKPythonAlgorithmBase.__init__(self,
11           nInputPorts=0,
12           nOutputPorts=1, outputType='vtkImageData')
13
14     def RequestInformation(self, request, inInfo, outInfo):
15       info = outInfo.GetInformationObject(0)
16
17       info.Set(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT(),
18           (0, 60, 0, 60, 0, 0), 6)
19
20       info.Set(vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS(),
21                  t, len(t))
22       info.Set(vtk.vtkStreamingDemandDrivenPipeline.TIME_RANGE(),
23                [t[0], t[-1]], 2)
24
25       info.Set(vtk.vtkAlgorithm.CAN_PRODUCE_SUB_EXTENT(), 1)
26
27       return 1
28
29     def RequestData(self, request, inInfo, outInfo):
30       info = outInfo.GetInformationObject(0)
31       # We produce only the extent that we are asked (UPDATE_EXTENT)
32       ue = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT())
33       ue = np.array(ue)
34
35       output = vtk.vtkImageData.GetData(outInfo)
36
37       # Parameters of the grid to produce
38       dims = ue[1::2] - ue[0::2] + 1
39       origin = 0
40       spacing = 0.1
41
42       # The time step requested
43       t = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP())
44
45       # The velocity vs y
46       y = origin + spacing*np.arange(ue[2],  ue[3]+1)
47       u = np.exp(-y/np.sqrt(2))*np.sin(t-y/np.sqrt(2))
48
49       # Set the velocity for all points of the grid which
50       # has of dimensions 3, dims[0], dims[1]. The first number
51       # is because of 3 components in the vector. Note the
52       # memory layout VTK uses is a bit unusual. It's Fortran
53       # ordered but the velocity component increases fastest.
54       a = np.zeros((3, dims[0], dims[1]), order='F')
55       a[0, :] = u
56
57       output.SetExtent(*ue)
58       output.SetSpacing(0.5, 0.1, 0.1)
59
60       # Make a VTK array from the numpy array (using pointers)
61       v = dsa.numpyTovtkDataArray(a.ravel(order='A').reshape(
62                   dims[0]*dims[1], 3))
63       v.SetName("vectors")
64       output.GetPointData().SetVectors(v)
65
66       return 1
{% endhighlight %}

This example is mostly self-explanatory. The pieces necessary for temporal
streaming are as follows.

* **Lines 20-23:** This is where the reader provides meta-data about the values
of time steps that it can produce as well as the overall range. The overall range
is redundant here but it is required because VTK also supports sources that can
produce arbitrary (not discrete) time values as requested by the pipeline.
* **Line 43:** The reader has to respond to the time value requested by downstream
using the `UPDATE_TIME_STEP()` key.

If you are not familiar with VTK's structured data memory layout, line 54 may
look a little odd. VTK uses a Fortran ordering for structured data (i is the
fastest increasing logical index). At the same time, VTK interleaves velocity
components (i.e. velocity component index increases fastest). So a velocity
array would like this in memory `u_0 v_0 w_0 u_1 v_1 w_1 ...`. Hence the
dimensions of `3, dims[0], dims[1]` and the `order='F'` (F being Fortran).

Also note that this algorithm can also handle a sub-extent request. To enable this
feature, it sets the `CAN_PRODUCE_SUB_EXTENT()` key on line 25 and produces
the extent requested by the `UPDATE_EXTENT()` key in RequestData.

Finally, line 55 works thanks to numpy broadcasting rules as defined [here](
http://docs.scipy.org/doc/numpy/user/basics.broadcasting.html).

Now that we have the source, we can manually update it as follows.

{% highlight python %}
s = VelocitySource()
s.UpdateInformation()
s.GetOutputInformation(0).Set(
   vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP(), t[2])
s.Update()
i = s.GetOutputDataObject(0)
print t[2], i.GetPointData().GetVectors().GetTuple3(0)
{% endhighlight %}

This will print `0.661387927072 (0.6142127126896678, 0.0, 0.0)`. To verify: if you substitute `y=0` and `t=0.6613879` in our equation, you will see that `u=sin(0.6613879)=0.6142127126`.

## Streaming Filter

So far so good. Now, let's do something more exciting. Let's write a filter that streams
multiple timesteps from this source. One simple use case for such a filter is to calculate
statistics of a data point over time. In our example, we will simply produce a table of
`u` values for the first point over time. Here is the code.

{% highlight python %}
1 class PointOverTime(VTKPythonAlgorithmBase):
2     def __init__(self):
3         VTKPythonAlgorithmBase.__init__(self,
4             nInputPorts=1, inputType='vtkDataSet',
5             nOutputPorts=1, outputType='vtkTable')
6
7     def RequestInformation(self, request, inInfo, outInfo):
8         # Reset values.
9         self.UpdateTimeIndex = 0
10        info = inInfo[0].GetInformationObject(0)
11        self.TimeValues = info.Get(
12            vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS())
13        self.ValueOverTime = np.zeros(len(self.TimeValues))
14        return 1
15
16    def RequestUpdateExtent(self, request, inInfo, outInfo):
17        info = inInfo[0].GetInformationObject(0)
18        # Ask for the next timestep.
19        info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP(),
20            self.TimeValues[self.UpdateTimeIndex])
21        return 1
22
23    def RequestData(self, request, inInfo, outInfo):
24        info = inInfo[0].GetInformationObject(0)
25        inp = dsa.WrapDataObject(vtk.vtkDataSet.GetData(info))
26        # Extract the value for the current time step.
27        self.ValueOverTime[self.UpdateTimeIndex] =\
28            inp.PointData['vectors'][0, 0]
29        if self.UpdateTimeIndex < len(self.TimeValues) - 1:
30            # If we are not done, ask the pipeline to re-execute us.
31            self.UpdateTimeIndex += 1
32            request.Set(
33                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING(),
34                1)
35        else:
36            # We are done. Populate the output.
37            output = dsa.WrapDataObject(vtk.vtkTable.GetData(outInfo))
38            output.RowData.append(self.ValueOverTime, 'u over time')
39            # Stop execution
40            request.Remove(
41                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING())
42        return 1
{% endhighlight %}

We can now setup a pipeline and execute it as follow.

{% highlight python %}
s = VelocitySource()

f = PointOverTime()
f.SetInputConnection(s.GetOutputPort())
f.Update()

vot = dsa.WrapDataObject(f.GetOutputDataObject(0)).RowData['u over time']

import matplotlib.pyplot as plt
plt.plot(f.TimeValues, vot)
plt.grid()
plt.axes().set_xlabel("t")
plt.axes().set_ylabel("u")
plt.savefig('u_over_time.png')
{% endhighlight %}

And the output looks like this.

![velocity over time](/assets/u_over_time.png)

This seemingly simple algorithm actually accomplishes something quite complex
with a few lines. The magic is in lines 32-24. When an algorithms sets the
`CONTINUE_EXECUTING()` key, the pipeline will execute again both the
`RequestUpdateExtent()` and `RequestData()` passes. So let's trace what this
algorithm does:

1. In `RequestInformation()`, it initializes a few data members including
`UpdateTimeIndex`.
2. In `RequestUpdateExtent()`, it sets the update time value to the first
time step (because `UpdateTimeIndex == 0`).
3. Upstream pipeline executes.
4. In `RequestData()`, it stores the `u` value of the first point in the
`ValueOverTime` array as the first value (using `UpdateTimeIndex` as the
index).
5. Because we didn't reach the last time step, it increments `UpdateTimeIndex`
and sets `CONTINUE_EXECUTING()`.
6. The pipeline re-executes the filter starting at 2. But this time `UpdateTimeIndex`
is 1 so the upstream will produce the 2nd time step.

This will continue until `UpdateTimeIndex == len(self.TimeValues) - 1`. Once the
streaming is done, the filter adds its cached value to its output as an array.

There you go, streaming in a nutshell. This can be used to do lots of useful things
such as computing temporal mean, min, max, standard deviation etc etc. It can be
also used to do more sophisticated things such as a particle advection. I will cover
that in my next blog. If you are up to the challenge, here are a few tips:

* Start with a set of seed points (say a line parallel to the y axis),
* Stream timesteps 2 at a time,
* For each pair of time steps, calculate the mean velocity,
* Calculate the next set of points as `pnext = pprev + vel * dt`,
* You can compute the vel at each point by using the probe filter.

This should give you a very basic first order particle integrator. The solution
in the next blog...

_Note_: A more thorough description of the temporal streaming in VTK can be found
in [this paper](http://www.sandia.gov/~kmorel/documents/TimeVis-IEEE2007.html).
