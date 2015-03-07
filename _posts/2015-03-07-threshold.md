---
layout: post
title: "Threshold with Cell Set"
---

In my [last blog]({% post_url 2015-02-20-cell-set %}), I described a new
type of unstructured grid which can be used to represent a subset of a
structured dataset without explicit connectivity data structures. I mentioned
that one very good application of such a dataset is a better implementation
of the threshold filter. In the blog, we'll go over such an implementation as
shown [here](https://github.com/berkgeveci/berkgeveci.github.io/blob/jekyll/code/zero-copy/vtkThreshold3.h)
and [here](https://github.com/berkgeveci/berkgeveci.github.io/blob/jekyll/code/zero-copy/vtkThreshold3.cxx).

Let's first quickly go over the original VTK implementation as can be found
[here](https://github.com/Kitware/VTK/blob/v6.2.0/Filters/Core/vtkThreshold.cxx).
First notice that this filter accepts any `vtkDataSet` and produces an unstructured
grid.

{% highlight cpp %}
// Note that subclasses of vtkUnstructuredGridAlgorithm produce
// vtkUnstructuredGrid in the first output by default.
class VTKFILTERSCORE_EXPORT vtkThreshold : public vtkUnstructuredGridAlgorithm
{
{% endhighlight %}

{% highlight cpp %}
// FillInputPortInformation is overriden to change the required
// input from vtkUnstructuredGrid to vtkDataSet
int vtkThreshold::FillInputPortInformation(int, vtkInformation *info)
{
  info->Set(vtkAlgorithm::INPUT_REQUIRED_DATA_TYPE(), "vtkDataSet");
  return 1;
}
{% endhighlight %}

Next, let's quickly take a look at `RequestData`. I added some comments
in the excerpt to make it easier to follow. I also took out pieces that
are not very relevant to our discussion. See the full source for details.

{% highlight cpp %}
int vtkThreshold::RequestData(
  vtkInformation *vtkNotUsed(request),
  vtkInformationVector **inputVector,
  vtkInformationVector *outputVector)
{
  // get the info objects
  vtkInformation *inInfo = inputVector[0]->GetInformationObject(0);
  vtkInformation *outInfo = outputVector->GetInformationObject(0);

  // get the input and output
  vtkDataSet *input = vtkDataSet::SafeDownCast(
    inInfo->Get(vtkDataObject::DATA_OBJECT()));
  vtkUnstructuredGrid *output = vtkUnstructuredGrid::SafeDownCast(
    outInfo->Get(vtkDataObject::DATA_OBJECT()));

  // ...

  // We create an output unstructured grid. This grid will contain
  // the same set of point and cell arrays. But these will be new
  // arrays that contain only the output subset.
  outPD->CopyGlobalIdsOn();
  outPD->CopyAllocate(pd);
  outCD->CopyGlobalIdsOn();
  outCD->CopyAllocate(cd);

  // Create new output points.
  numPts = input->GetNumberOfPoints();
  output->Allocate(input->GetNumberOfCells());

  newPoints = vtkPoints::New();
  // ...
  newPoints->Allocate(numPts);

  // We need this map to find the mapping between input
  // and output point ids so that we can copy the point data.
  pointMap = vtkIdList::New(); //maps old point ids into new
  pointMap->SetNumberOfIds(numPts);
  for (i=0; i < numPts; i++)
    {
    pointMap->SetId(i,-1);
    }

  // ...

  // Check that the scalars of each cell satisfy the threshold criterion
  for (cellId=0; cellId < input->GetNumberOfCells(); cellId++)
    {
    cell = input->GetCell(cellId);
    cellPts = cell->GetPointIds();
    numCellPts = cell->GetNumberOfPoints();

    // Here whether to keep a cell is determined. The answer is stored in
    // the keepCell variable.

    // If we are keeping the cell, copy to the output.
    if (  numCellPts > 0 && keepCell )
      {
      // satisfied thresholding (also non-empty cell, i.e. not VTK_EMPTY_CELL)

      // Go over the points of the cell.
      for (i=0; i < numCellPts; i++)
        {
        ptId = cellPts->GetId(i);
        // If we didn't insert the point already, insert in the output
        if ( (newId = pointMap->GetId(ptId)) < 0 )
          {
          input->GetPoint(ptId, x);
          newId = newPoints->InsertNextPoint(x);
          // Update the point map for future use.
          pointMap->SetId(ptId,newId);
          // Also copy the data.
          outPD->CopyData(pd,ptId,newId);
          }
        // Insert the point to the output cell.
        newCellPts->InsertId(i,newId);
        }
      // ...
      // Insert the new cell to the output
      newCellId = output->InsertNextCell(cell->GetCellType(),newCellPts);
      // Copy the cell data
      outCD->CopyData(cd,cellId,newCellId);
      newCellPts->Reset();
      } // satisfied thresholding
    } // for all cells

  // ..

  output->SetPoints(newPoints);
  newPoints->Delete();

  output->Squeeze();

  return 1;
}
{% endhighlight %}

In our new filter, much of this will remain the same. In fact, to quickly
develop it, I copied `vtkThreshold` to `vtkThreshold3` and made a few changes.
First, I change the filter to produce a `vtkCellSet`:

{% highlight cpp %}
class vtkThreshold3 : public vtkUnstructuredGridBaseAlgorithm
{
{% endhighlight %}

{% highlight cpp %}
int vtkThreshold3::RequestDataObject(
  vtkInformation *vtkNotUsed(request),
  vtkInformationVector **vtkNotUsed(inputVector),
  vtkInformationVector *outputVector)
{
  vtkInformation* info = outputVector->GetInformationObject(0);
  vtkCellSet *output = vtkCellSet::SafeDownCast(
    info->Get(vtkDataObject::DATA_OBJECT()));

  if (!output)
    {
    vtkCellSet* newOutput = vtkCellSet::New();
    info->Set(vtkDataObject::DATA_OBJECT(), newOutput);
    newOutput->Delete();
    }

  return 1;
}
{% endhighlight %}

Next, I changed the part of the code that creates new points and cells to
instead keep track of the ids of the cells that we want to threshold. So
the following code

{% highlight cpp %}
// If we are keeping the cell, copy to the output.
if (  numCellPts > 0 && keepCell )
  {
  // satisfied thresholding (also non-empty cell, i.e. not VTK_EMPTY_CELL)

  // Go over the points of the cell.
  for (i=0; i < numCellPts; i++)
    {
    ptId = cellPts->GetId(i);
    // If we didn't insert the point already, insert in the output
    if ( (newId = pointMap->GetId(ptId)) < 0 )
      {
      input->GetPoint(ptId, x);
      newId = newPoints->InsertNextPoint(x);
      // Update the point map for future use.
      pointMap->SetId(ptId,newId);
      // Also copy the data.
      outPD->CopyData(pd,ptId,newId);
      }
    // Insert the point to the output cell.
    newCellPts->InsertId(i,newId);
    }
  // ...
  // Insert the new cell to the output
  newCellId = output->InsertNextCell(cell->GetCellType(),newCellPts);
  // Copy the cell data
  outCD->CopyData(cd,cellId,newCellId);
  newCellPts->Reset();
  } // satisfied thresholding
{% endhighlight %}

changes to

{% highlight cpp %}
if (  numCellPts > 0 && keepCell )
  {
  ids->InsertNextValue(cellId);
  } // satisfied thresholding
{% endhighlight %}

And the `ids` are used in creating the cell set as follows

{% highlight cpp %}
vtkIdTypeArray* ids = vtkIdTypeArray::New();
ids->Allocate(input->GetNumberOfCells());
output->GetImplementation()->SetCellIds(ids);
ids->Delete();
{% endhighlight %}

Finally, we have to create an instance of `vtkPoints` for the output
unstructured grid. This has to be handled specially in the cases where
the input does not have its own `vtkPoints` (for example `vtkImageData`).
Here is the code:

{% highlight cpp %}
vtkImageData* inputImage = vtkImageData::SafeDownCast(input);
if (inputImage)
  {
  vtkNew<vtkImageData> img;
  img->CopyStructure(inputImage);

  vtkNew<vtkImagePointsArray<double> > ptsArray;
  ptsArray->InitializeArray(img.GetPointer());
  ptsArray->SetName("pts");

  vtkNew<vtkPoints> points;
  points->SetData(ptsArray.GetPointer());

  output->SetPoints(points.GetPointer());
  }
{% endhighlight %}

This is it! The output of this filter acts as an unstructured grid but does
not store cells or points explicitly. As a bonus, the filter actually got simpler
and performs better. We can exercise this filter as follows.

{% highlight cpp %}
vtkNew<vtkRTAnalyticSource> source;
source->SetWholeExtent(-50, 50, -50, 50, -50, 50);

vtkNew<vtkThreshold3> threshold;
threshold->ThresholdByLower(200);
threshold->SetInputConnection(source->GetOutputPort());
threshold->Update();
cerr << "Threshold " << timer->GetElapsedTime() << endl;
cerr << threshold->GetOutput()->GetNumberOfCells() << endl;

vtkNew<vtkContourFilter> contour;
contour->SetValue(0, 150);
contour->SetInputConnection(threshold->GetOutputPort());
contour->Update();
cerr << "Contour " << timer->GetElapsedTime() << endl;
cerr << contour->GetOutput()->GetNumberOfPoints() << endl;
{% endhighlight %}

Careful readers probably noticed that there is a flaw in this approach: the
output of the threshold filter contains *all* of the points of the input.
Therefore, any point-based filters such as glyph and point statistics will
incorrectly produce results based on all input points. With the current VTK
data model, there is no easy way of fixing this issue. In the near future,
we will add support for masking (blanking) of points and cells to all datasets.
With this feature in place, one could easily keep track of all points touched
by the output grid during tresholding and mask all others. In fact, if masking
support was in the data model, we wouldn't have to create a new unstructured
grid but directly mask cells and points that are not needed. A blog for another
time.
