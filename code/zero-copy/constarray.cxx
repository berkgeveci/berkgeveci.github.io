#include <vtkNew.h>
#include <vtkImageData.h>
#include <vtkPointData.h>
#include <vtkProbeFilter.h>
#include <vtkLineSource.h>

#include "vtkConstantArray.h"

int main()
{
  vtkNew<vtkConstantArray<double> > testScalars;
  testScalars->InitializeArray(10, 1000, 1);
  testScalars->SetName("scalars");

  cout << testScalars->GetValue(10) << endl;
  cout << testScalars->GetNumberOfTuples() << endl;

  vtkNew<vtkImageData> image;
  image->SetDimensions(10, 10, 10);
  image->GetPointData()->SetScalars(testScalars.GetPointer());

  image->Print(cout);

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

  return 0;
}