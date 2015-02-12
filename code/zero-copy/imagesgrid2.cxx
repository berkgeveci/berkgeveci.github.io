#include <vtkNew.h>
#include <vtkImageData.h>
#include <vtkPointData.h>
#include <vtkProbeFilter.h>
#include <vtkLineSource.h>
#include <vtkStructuredGrid.h>
#include <vtkPoints.h>
#include <vtkRTAnalyticSource.h>
#include <vtkDoubleArray.h>
#include <vtkPolyData.h>
#include <vtkTimerLog.h>

#include "vtkGridSynchronizedTemplates3D.h"
#include "vtkGridSynchronizedTemplates3D2.h"
#include "vtkImagePointsArray.h"

int main()
{
  vtkNew<vtkTimerLog> timer;

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

  vtkNew<vtkGridSynchronizedTemplates3D2> contour;
  contour->SetInputData(sgrid.GetPointer());
  contour->SetValue(0, 200);
  timer->StartTimer();
  contour->Update();
  timer->StopTimer();
  cerr << "Zero copy execute " << timer->GetElapsedTime() << endl;

  timer->StartTimer();
  double* ptsPtr = reinterpret_cast<double*>(testPts->GetVoidPointer(0));
  timer->StopTimer();
  cerr << "Array copy " << timer->GetElapsedTime() << endl;
  vtkNew<vtkDoubleArray> pts;
  pts->SetNumberOfComponents(3);
  pts->SetArray(ptsPtr, wavelet->GetNumberOfPoints() * 3, 1);
  points->SetData(pts.GetPointer());

  vtkNew<vtkGridSynchronizedTemplates3D> contour2;
  contour2->SetInputData(sgrid.GetPointer());
  contour2->SetValue(0, 200);
  timer->StartTimer();
  contour2->Update();
  timer->StopTimer();
  cerr << "Deep copy execute " << timer->GetElapsedTime() << endl;

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
      if (pt1[j] != pt2[j])
        {
        cerr << "Point mismatch " << i << " " << j << " " << pt1[j] << " " << pt2[j] << endl;
        return 1;
        }
      }
    }

  cout << "Success" << endl;
  return 0;
}