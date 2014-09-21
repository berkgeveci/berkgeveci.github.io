import vtk
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase

class MySource(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=0,
            nOutputPorts=1, outputType='vtkPolyData')

    def RequestInformation(self, request, inInfo, outInfo):
        print "MySource RequestInformation:"
        print outInfo.GetInformationObject(0)
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        print "MySource RequestUpdateExtent:"
        print outInfo.GetInformationObject(0)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        print "MySource RequestData:"
        print outInfo.GetInformationObject(0)
        return 1

class MyFilter(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkPolyData',
            nOutputPorts=1, outputType='vtkPolyData')

    def RequestInformation(self, request, inInfo, outInfo):
        print "MyFilter RequestInformation:"
        print outInfo.GetInformationObject(0)
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        print "MyFilter RequestUpdateExtent:"
        print outInfo.GetInformationObject(0)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        print "MyFilter RequestData:"
        print outInfo.GetInformationObject(0)
        return 1

s = MySource()

f = MyFilter()
f.SetInputConnection(s.GetOutputPort())

f.Update()