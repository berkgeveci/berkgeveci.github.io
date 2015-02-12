#include <vtkNew.h>
#include <vtkImageData.h>
#include <vtkPointData.h>
#include <vtkProbeFilter.h>
#include <vtkLineSource.h>

#include "vtkImagePointsArray.h"

int main()
{
  vtkNew<vtkImageData> img;
  img->SetDimensions(10, 10, 10);

  vtkNew<vtkImagePointsArray<double> > testScalars;
  testScalars->InitializeArray(img.GetPointer());
  testScalars->SetName("scalars");

  cout << testScalars->GetValue(10) << endl;
  cout << testScalars->GetNumberOfTuples() << endl;

  vtkNew<vtkImageData> image;
  image->SetDimensions(10, 10, 10);
  image->GetPointData()->SetScalars(testScalars.GetPointer());

  image->Print(cout);

  vtkNew<vtkLineSource> line;
  line->SetPoint1(0, 0, 1);
  line->SetPoint2(9, 9, 1);
  line->SetResolution(50);

  vtkNew<vtkProbeFilter> probe;
  probe->SetSourceData(image.GetPointer());
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