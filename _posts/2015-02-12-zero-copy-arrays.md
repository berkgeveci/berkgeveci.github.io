---
layout: post
title: "Zero Copy Arrays"
---

With this blog, I start a new series covering some of the new
features in VTK's data model. Please note that a lot of these improvements are
very new and are likely to change as we address various kinks we encounter
as we apply them to various problems.

In these blogs, I will depend heavily on the excellent work done by [David
Lonie](http://www.kitware.com/company/team/lonie.html),
which is summarized [here](http://www.vtk.org/Wiki/VTK/InSituDataStructures)
and [here](http://www.kitware.com/blog/home/post/577). I recommend taking a close
look at the Wiki page before digging too deep into these blogs as I will not
provide the same level of detail. In summary, we made a number of changes to
VTK to allow easy creation of datasets and data arrays that use memory layouts
different than VTK's defaults. The main objective of these changes was to enable
tight coupling of VTK with other codes without the need to deep copy data structures
back and forth. Our main application for this is _in situ_ analysis and
visualization where the **other code** is a simulation, usually running on a
supercomputer. However, as I will demonstrate, these changes open the door for
a lot more. Let's get down to it.

## Constant Array

The simplest example that I could think of is a VTK data array that has one
unique value. Normally, such an array would be created and populated as follows.

{% highlight cpp %}
vtkNew<vtkFloatArray> constArray;
constArray->SetNumberOfTuples(nvalues);
for(vtkIdType i=0; i<nvales; i++)
{
  constArray->SetValue(i, constValue);
}
{% endhighlight %}

Obviously, this array uses `nvalues * sizeof(float)` bytes of memory in addition
to whatever memory an array requires internally. Pretty wasteful. Wouldn't  it be
great if we could create an array that uses only `sizeof(float)` bytes (+ whatever
the array uses internally)? With the zero copy infrastructure, we can. Take a quick
look at the [header](https://github.com/berkgeveci/berkgeveci.github.io/blob/jekyll/code/zero-copy/vtkConstantArray.h)  and the [implementation](https://github.com/berkgeveci/berkgeveci.github.io/blob/jekyll/code/zero-copy/vtkConstantArray.txx).
I shamelessly copied and pasted much of this from [`vtkCPExodusIIResultsArrayTemplate`](https://github.com/Kitware/VTK/blob/master/IO/Exodus/vtkCPExodusIIResultsArrayTemplate.txx)
as one can probably guess from the comments I left. This class looks fairly long but
I actually had to change only a few lines of code, mainly:

{% highlight cpp %}
template <class Scalar> Scalar& vtkConstantArray<Scalar>
::GetValueReference(vtkIdType idx)
{
  return this->Value;
}
{% endhighlight %}

Note that this code ignores the value index, `idx`, which is expected for a
constant array. We can exercise this code with the following.

{% highlight cpp %}
vtkNew<vtkConstantArray<double> > testScalars;
testScalars->InitializeArray(10, 1000, 1);
testScalars->SetName("scalars");

vtkNew<vtkImageData> image;
image->SetDimensions(10, 10, 10);
image->GetPointData()->SetScalars(testScalars.GetPointer());

vtkNew<vtkLineSource> line;
line->SetPoint1(0, 0, 0);
line->SetPoint2(9, 9, 9);
line->SetResolution(50);

vtkNew<vtkProbeFilter> probe;
probe->SetSourceData(image.GetPointer());
probe->SetInputConnection(line->GetOutputPort());
probe->Update();

vtkDataArray* outScalars =
  probe->GetOutput()->GetPointData()->GetArray("scalars");
for (int i=0; i<50; i++)
  {
  cout << i << " : " << outScalars->GetTuple1(i) << endl;
  }
{% endhighlight %}

This prints 10 for each point as expected.

## Struct of Arrays

Let's do something a bit more involved. As you probably know, VTK stores
vectors in an interleaved way. When linearly traversing a vector array, the
component index increases faster than the tuple index. This is commonly referred
to as array of structs (AOS, see [this link](http://stackoverflow.com/questions/17924705/structure-of-arrays-vs-array-of-structures-in-cuda) for example).
Many simulation codes store their vectors as struct of arrays (SOA).
[Dave](http://www.kitware.com/company/team/lonie.html) developed an array that
can handle AOS vectors. See the full code [here](https://github.com/Kitware/VTK/blob/master/IO/Exodus/vtkCPExodusIIResultsArrayTemplate.h) and
[here](https://github.com/Kitware/VTK/blob/master/IO/Exodus/vtkCPExodusIIResultsArrayTemplate.txx).
This class is very similar to `vtkConstantArray`, which is no surprise given
that I copied from it for my implementation. The meat of this array is the following
piece of code.

{% highlight cpp %}
template <class Scalar> Scalar& vtkCPExodusIIResultsArrayTemplate<Scalar>
::GetValueReference(vtkIdType idx)
{
  const vtkIdType tuple = idx / this->NumberOfComponents;
  const vtkIdType comp = idx % this->NumberOfComponents;
  return this->Arrays[comp][tuple];
}
{% endhighlight %}

Note how this method maps a value reference to the right array and index in
an SOA data structure. The equivalent of this for VTK's AOS data structure
is the following.

{% highlight cpp %}
template <class Scalar> Scalar& vtkCPExodusIIResultsArrayTemplate<Scalar>
::GetValueReference(vtkIdType idx)
{
  return this->Array[idx];
}
{% endhighlight %}

## Implicit Points Array

This requires explanation. In VTK, there are two types of datasets. In one type,
subclasses of `vtkPointSet`, the point coordinates are stored explicitly as a
`vtkDataArray` (inside a `vtkPoints`). In the other type, the points coordinates
are stored implicitly (`vtkImageData` and `vtkRectilinearGrid`). There are occasions
where we may want an implementation that is in between these two types. For example,
when we threshold an image, the filter produces a `vtkUnstructuredGrid`, which
stores its points explicitly. This causes a significant increase in memory usage.
Wouldn't it be nice if the threshold filter could create an unstructured grid but
still refer to the points implicitly? In a future blog, I will describe how
we can implement a threshold filter that does this and more. Here, let's look
at a data array that can used to develop such a filter. See [here](https://github.com/berkgeveci/berkgeveci.github.io/blob/jekyll/code/zero-copy/vtkImagePointsArray.h)
and [here](https://github.com/berkgeveci/berkgeveci.github.io/blob/jekyll/code/zero-copy/vtkImagePointsArray.txx) for the implementation.
The meat of this class is as follows.

{% highlight cpp %}
template <class Scalar> Scalar& vtkImagePointsArray<Scalar>
::GetValueReference(vtkIdType idx)
{
  assert(this->Points);

  const vtkIdType tuple = idx / 3;
  const vtkIdType comp = idx % 3;

  return this->Points->GetPoint(tuple)[comp];
}
{% endhighlight %}

Note that `Points` is actually a `vtkImageData`, which calculates point coordinates
implicitly with the following code.

{% highlight cpp %}
void vtkImageData::GetPoint(vtkIdType ptId, double x[3])
{
  int i, loc[3];
  const double *origin = this->Origin;
  const double *spacing = this->Spacing;
  const int* extent = this->Extent;

  vtkIdType dims[3];
  dims[0] = extent[1] - extent[0] + 1;
  dims[1] = extent[3] - extent[2] + 1;
  dims[2] = extent[5] - extent[4] + 1;

  loc[0] = ptId % dims[0];
  loc[1] = (ptId / dims[0]) % dims[1];
  loc[2] = ptId / (dims[0]*dims[1]);

  for (i=0; i<3; i++)
    {
    x[i] = origin[i] + (loc[i]+extent[i*2]) * spacing[i];
    }
}
{% endhighlight %}

I left out some of the code for simplicity. We can exercise this class with the following.

{% highlight cpp %}
vtkNew<vtkRTAnalyticSource> source;
source->SetWholeExtent(-50, 50, -50, 50, -50, 50);
source->Update();

vtkImageData* wavelet = source->GetOutput();

vtkNew<vtkImageData> img;
img->CopyStructure(wavelet);

vtkNew<vtkImagePointsArray<double> > testPts;
testPts->InitializeArray(img.GetPointer());
testPts->SetName("pts");

vtkNew<vtkPoints> points;
points->SetData(testPts.GetPointer());

// This creates an unstructured grid from the input
// image data.
vtkNew<vtkCleanUnstructuredGrid> toUGrid;
toUGrid->SetInputData(wavelet);
toUGrid->Update();

vtkUnstructuredGrid* ugrid = toUGrid->GetOutput();
// Here we substitute the implicit points.
ugrid->SetPoints(points.GetPointer());

vtkNew<vtkContourFilter> contour2;
contour2->SetInputData(ugrid);
contour2->SetValue(0, 200);
contour2->Update();
{% endhighlight %}

The full code which can be found [here](https://github.com/berkgeveci/berkgeveci.github.io/blob/jekyll/code/zero-copy/imageugrid.cxx)
verifies that the output of the contour filter matches the output that is generated
from an unstructured grid with explicit points.

We covered a few examples of data array subclasses that use memory
layouts different than VTK's default. Most filters should work out-of-box
when they encounter these arrays. However, some filters, especially those that
directly access raw pointers, need to be changed. In my next blog, I will
demonstrate how such filters can be easily updated. Until then, happy zero
copying.
