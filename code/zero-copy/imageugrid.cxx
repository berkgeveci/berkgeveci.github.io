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

#include "vtkImagePointsArray.h"
#include "vtkCleanUnstructuredGrid.h"

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

  vtkNew<vtkCleanUnstructuredGrid> toUGrid;
  toUGrid->SetInputData(wavelet);
  toUGrid->Update();

  vtkUnstructuredGrid* ugrid = toUGrid->GetOutput();

  vtkNew<vtkContourFilter> contour;
  contour->SetInputData(ugrid);
  contour->SetValue(0, 200);
  timer->StartTimer();
  contour->Update();
  timer->StopTimer();
  cerr << "Deep copy execute " << timer->GetElapsedTime() << endl;
  cerr << contour->GetOutput()->GetNumberOfPoints() << endl;

  ugrid->SetPoints(points.GetPointer());

  vtkNew<vtkContourFilter> contour2;
  contour2->SetInputData(ugrid);
  contour2->SetValue(0, 200);
  timer->StartTimer();
  contour2->Update();
  timer->StopTimer();
  cerr << "Zero copy execute " << timer->GetElapsedTime() << endl;
  cerr << contour2->GetOutput()->GetNumberOfPoints() << endl;

  vtkIdType numPts = contour->GetOutput()->GetNumberOfPoints();
  if (contour2->GetOutput()->GetNumberOfPoints() != numPts)
    {
    cerr << "Number of points mismatch" << endl;
    return 1;
    }
  for (vtkIdType i=0; i<numPts; i++)
    {
    double pt1[3], pt2[3];
    contour->GetOutput()->GetPoint(i, pt1);
    contour2->GetOutput()->GetPoint(i, pt2);
    for (int j=0; j<3; j++)
      {
      if (pt1[j] - pt2[j] > 10E-5)
        {
        cerr << "Point mismatch " << i << " " << j << " " << pt1[j] << " " << pt2[j]
          << pt1[j] - pt2[j] << endl;
        return 1;
        }
      }
    }

  cout << "Success" << endl;
  return 0;
}