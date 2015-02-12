#include <vtkNew.h>
#include <vtkImageData.h>
#include <vtkPointData.h>
#include <vtkProbeFilter.h>
#include <vtkLineSource.h>
#include <vtkUnstructuredGrid.h>
#include <vtkPoints.h>
#include <vtkRTAnalyticSource.h>
#include <vtkDoubleArray.h>
#include <vtkPolyData.h>
#include <vtkTimerLog.h>
#include <vtkContourFilter.h>
#include <vtkThreshold.h>

#include "vtkThreshold2.h"
#include "vtkImagePointsArray.h"
#include "vtkCleanUnstructuredGrid.h"

int main()
{
  vtkNew<vtkTimerLog> timer;

  vtkNew<vtkRTAnalyticSource> source;
  source->SetWholeExtent(-50, 50, -50, 50, -50, 50);
  source->Update();

  vtkImageData* wavelet = source->GetOutput();

  /*
  vtkNew<vtkImageData> img;
  img->CopyStructure(wavelet);

  vtkNew<vtkImagePointsArray<double> > testPts;
  testPts->InitializeArray(img.GetPointer());
  testPts->SetName("pts");

  vtkNew<vtkPoints> points;
  points->SetData(testPts.GetPointer());

  vtkNew<vtkCleanUnstructuredGrid> toUGrid;
  toUGrid->SetInputData(wavelet);
  toUGrid->Update();

  vtkUnstructuredGrid* ugrid = toUGrid->GetOutput();
  */

  vtkNew<vtkThreshold> threshold;
  threshold->SetInputData(wavelet);
  threshold->ThresholdByLower(200);
  timer->StartTimer();
  threshold->Update();
  timer->StopTimer();
  cerr << "Deep copy execute " << timer->GetElapsedTime() << endl;
  cerr << threshold->GetOutput()->GetNumberOfPoints() << endl;

  vtkNew<vtkContourFilter> contour;
  contour->SetValue(0, 150);
  contour->SetInputData(threshold->GetOutput());
  timer->StartTimer();
  contour->Update();
  timer->StopTimer();
  cerr << "Deep copy contour " << timer->GetElapsedTime() << endl;
  cerr << contour->GetOutput()->GetNumberOfPoints() << endl;

  vtkNew<vtkThreshold2> threshold2;
  threshold2->SetInputData(wavelet);
  threshold2->ThresholdByLower(200);
  timer->StartTimer();
  threshold2->Update();
  timer->StopTimer();
  cerr << "Zero copy execute " << timer->GetElapsedTime() << endl;
  cerr << threshold2->GetOutput()->GetNumberOfPoints() << endl;

  contour->SetInputData(threshold2->GetOutput());
  timer->StartTimer();
  contour->Update();
  timer->StopTimer();
  cerr << "Zero copy contour " << timer->GetElapsedTime() << endl;
  cerr << contour->GetOutput()->GetNumberOfPoints() << endl;

  cout << "Success" << endl;
  return 0;
}