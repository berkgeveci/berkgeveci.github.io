#include <vtkNew.h>
#include <vtkImageData.h>
#include <vtkPointData.h>
#include <vtkPoints.h>
#include <vtkRTAnalyticSource.h>
#include <vtkDoubleArray.h>
#include <vtkPolyData.h>
#include <vtkTimerLog.h>
#include <vtkContourFilter.h>
#include <vtkIdTypeArray.h>

#include "vtkImagePointsArray.h"
#include "vtkCellSet.h"
#include "vtkThreshold3.h"

int main()
{
  vtkNew<vtkTimerLog> timer;

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

  vtkNew<vtkCellSet> cellSet;
  cellSet->SetPoints(points.GetPointer());
  cellSet->GetPointData()->PassData(wavelet->GetPointData());
  cellSet->GetImplementation()->SetDataSet(wavelet);

  vtkNew<vtkIdTypeArray> ids;
  vtkIdType ncells = wavelet->GetNumberOfCells();
  ids->SetNumberOfTuples(ncells);
  cerr << "NCells: " << ncells << endl;
  for (vtkIdType i=0; i<ncells; i++)
    {
    ids->SetValue(i, i);
    }

  cellSet->GetImplementation()->SetCellIds(ids.GetPointer());

  vtkNew<vtkThreshold3> threshold;
  threshold->ThresholdByLower(200);
  threshold->SetInputData(wavelet);
  timer->StartTimer();
  threshold->Update();
  timer->StopTimer();
  cerr << "Threshold " << timer->GetElapsedTime() << endl;
  cerr << threshold->GetOutput()->GetNumberOfCells() << endl;

  vtkNew<vtkContourFilter> contour;
  contour->SetValue(0, 150);
  contour->SetInputData(threshold->GetOutput());
  timer->StartTimer();
  contour->Update();
  timer->StopTimer();
  cerr << "Contour " << timer->GetElapsedTime() << endl;
  cerr << contour->GetOutput()->GetNumberOfPoints() << endl;

  cout << "Success" << endl;
  return 0;
}