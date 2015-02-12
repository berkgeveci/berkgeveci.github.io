#include <vtkNew.h>
#include <vtkImageData.h>
#include <vtkPointData.h>
#include <vtkProbeFilter.h>
#include <vtkLineSource.h>
#include <vtkStructuredGrid.h>
#include <vtkPoints.h>
#include <vtkGridSynchronizedTemplates3D.h>
#include <vtkRTAnalyticSource.h>

#include "vtkImagePointsArray.h"

int main()
{
  vtkNew<vtkImageData> img;
  img->SetDimensions(10, 10, 10);

  vtkNew<vtkImagePointsArray<double> > testPts;
  testPts->InitializeArray(img.GetPointer());
  testPts->SetName("scalars");

  vtkNew<vtkPoints> points;
  points->SetData(testPts.GetPointer());

  vtkNew<vtkStructuredGrid> sgrid;
  sgrid->SetDimensions(10, 10, 10);
  sgrid->SetPoints(points.GetPointer());
  sgrid->GetPointData()->SetScalars(testPts.GetPointer());

  sgrid->Print(cout);

  sgrid->GetBounds();

  vtkNew<vtkLineSource> line;
  line->SetPoint1(0, 0, 1);
  line->SetPoint2(9, 9, 1);
  line->SetResolution(50);

  vtkNew<vtkProbeFilter> probe;
  probe->SetSourceData(sgrid.GetPointer());
  probe->SetInputConnection(line->GetOutputPort());
  probe->Update();

  vtkDataArray* outScalars =
    probe->GetOutput()->GetPointData()->GetArray("scalars");
  for (int i=0; i<50; i++)
    {
    double* val = outScalars->GetTuple3(i);
    cout << i << " : " << val[0] << " " << val[1] << " " << val[2] << endl;
    }

  return 0;
}