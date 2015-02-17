---
layout: post
title: "Converting Pointer-Based Algorithms to Zero Copy Arrays"
---

In my [last blog]({% post_url 2015-02-12-zero-copy-arrays %}), I demonstrated
how VTK's new "zero copy" infrastructure can be used to develop data arrays
that use memory layouts different than VTK's default. Many of VTK's algorithm
will work out of box with these arrays - the ones that depend on virtual
methods such as `SetTuple()/GetTuple()` and `SetValue()/GetValue()`. However,
certain algorithms need to be modified slightly. We'll cover how this can
be achieved here.

If you pass a subclass of `vtkMappedDataArray<>` to an algorithm that accesses
the raw data pointer of an array via the `GetVoidPointer()` method or its ilk,
you will see the following error at runtime:

{% highlight sh %}
Warning: In /Users/berk/Work/VTK/git/Common/Core/vtkMappedDataArray.txx, line 47
19vtkImagePointsArrayIdE (0x7fa939c0ecd0): GetVoidPointer called.
This is very expensive for vtkMappedDataArray subclasses, since the
scalar array must be generated for each call. Consider using a
vtkTypedDataArrayIterator instead.
{% endhighlight %}

If you see this error, it may be a good idea to refactor the offending algorithm
to avoid this deep copy (which is slow and wastes memory). As an example, let's
consider a piece of code that uses the `vtkImagePointsArray` from the last blog.

{% highlight cpp %}
vtkNew<vtkRTAnalyticSource> source;
source->SetWholeExtent(-100, 100, -100, 100, -100, 100);
source->Update();

vtkImageData* wavelet = source->GetOutput();

vtkNew<vtkImageData> img;
img->CopyStructure(wavelet);

vtkNew<vtkImagePointsArray<double> > testPts;
testPts->InitializeArray(img.GetPointer());
testPts->SetName("pts");

vtkNew<vtkPoints> points;
points->SetData(testPts.GetPointer());

vtkNew<vtkStructuredGrid> sgrid;
sgrid->SetDimensions(wavelet->GetDimensions());
sgrid->SetPoints(points.GetPointer());
sgrid->GetPointData()->SetScalars(wavelet->GetPointData()->GetScalars());

vtkNew<vtkGridSynchronizedTemplates3D> contour2;
contour2->SetInputData(sgrid.GetPointer());
contour2->SetValue(0, 200);
contour2->Update();
{% endhighlight %}

The idea behind this is to treat an image data as a `vtkStructuredGrid` without
creating an explicit point array. Not very useful on its own but it can
be extended fairly easily to represent dataset not currently efficiently handled by VTK
such as a grid curvilinear in x-y but regular in z, a regular spherical grid etc.
When you run this example, you will notice the warning I mentioned above. The result
will be correct, however. If you track down the origin of the warning, you end
up in `vtkGridSynchronizedTemplates3D()` :

{% highlight cpp %}
template <class T, class PointsType>
void ContourGrid(vtkGridSynchronizedTemplates3D *self, ...)
{
  int *inExt = input->GetExtent();
  int xdim = exExt[1] - exExt[0] + 1;
  int ydim = exExt[3] - exExt[2] + 1;
  double n0[3], n1[3];  // used in gradient macro
  double *values = self->GetValues();
  int numContours = self->GetNumberOfContours();
  PointsType *inPtPtrX, *inPtPtrY, *inPtPtrZ;
  PointsType *p0, *p1, *p2, *p3;
  T *inPtrX, *inPtrY, *inPtrZ;
  T *s0, *s1, *s2, *s3;
  int XMin, XMax, YMin, YMax, ZMin, ZMax;
  int incY, incZ;
  PointsType* points =
    static_cast<PointsType*>(
    input->GetPoints()->GetData()->GetVoidPointer(0));
{% endhighlight %}

The problem is in the `GetVoidPointer(0)` call that asks for a raw pointer of type
`PointsType` (double in this case). The solution to this issue is described in
detail in David Lonie's excellent [Wiki page](http://www.vtk.org/Wiki/VTK/InSituDataStructures).
Using the method described by David, I converted `vtkGridSynchronizedTemplates3D`.
The full code can be found [here](https://github.com/berkgeveci/berkgeveci.github.io/blob/jekyll/code/zero-copy/vtkGridSynchronizedTemplates3D2.cxx). The change is minimal. I first made
a change to the following function:

{% highlight cpp %}
template <class T>
void ContourGrid(vtkGridSynchronizedTemplates3D *self,
                 int *exExt, T *scalars, vtkStructuredGrid *input,
                 vtkPolyData *output, vtkDataArray *inScalars,
                 bool outputTriangles)
{
  switch(input->GetPoints()->GetData()->GetDataType())
    {
    vtkTemplateMacro(
      ContourGrid(self, exExt, scalars, input, output,
        static_cast<VTK_TT *>(0), inScalars, outputTriangles));
    }
}
{% endhighlight %}

For those not familiar with VTK's template macros, `vtkTemplateMacro` expands
to a switch statement that looks like the following.

{% highlight cpp %}
#define vtkTemplateMacroCase(typeN, type, call)     \
  case typeN: { typedef type VTK_TT; call; }; break
#define vtkTemplateMacro(call)                                              \
  vtkTemplateMacroCase(VTK_DOUBLE, double, call);                           \
  vtkTemplateMacroCase(VTK_FLOAT, float, call);                             \
  vtkTemplateMacroCase_ll(VTK_LONG_LONG, long long, call)                   \
  vtkTemplateMacroCase_ll(VTK_UNSIGNED_LONG_LONG, unsigned long long, call) \
...
{% endhighlight %}

This allows calling a templated function such as `ContourGrid` with the right
template type. See above for the original `ContourGrid` signature with 2 template
arguments. I changed the single template argument `ContourGrid` to the following.

{% highlight cpp %}
template <class T>
void ContourGrid(vtkGridSynchronizedTemplates3D2 *self,
                 int *exExt, T *scalars, vtkStructuredGrid *input,
                 vtkPolyData *output, vtkDataArray *inScalars,
                 bool outputTriangles)
{
  vtkDataArray* pts = input->GetPoints()->GetData();
  switch(pts->GetDataType())
    {
    vtkDataArrayIteratorMacro(pts,
      ContourGrid(self, exExt, scalars,
        input, output, static_cast<vtkDAValueType*>(0),
        inScalars, outputTriangles, vtkDABegin));
    }
}
{% endhighlight %}

Note the usage of `vtkDataArrayIteratorMacro` macro. This macro was introduced
by David along with `vtkDABegin` and `vtkDAValueType`. See his Wiki page for details.
I then changed the other `ContourGrid` method as follows.

{% highlight cpp %}
template <class T, class PointsType, class InputIterator>
void ContourGrid(vtkGridSynchronizedTemplates3D2 *self,
                 int *exExt, T *scalars,
                 vtkStructuredGrid *input, vtkPolyData *output,
                 PointsType*, vtkDataArray *inScalars, bool outputTriangles,
                 InputIterator points)
{
...
}
{% endhighlight %}

Note how `points` is now of type `InputIterator` which is a template argument
magically defined within the `vtkDataArrayIteratorMacro`. This class leverages
the `vtkMappedDataArray<>` API to provide pointer style semantics. This is it!
After these changes, the pipeline shown above can now be run without any deep
copies.

In future blogs, I will continue to expand on zero copy structures as well as
dig into the cost of using these abstractions in terms of performance.