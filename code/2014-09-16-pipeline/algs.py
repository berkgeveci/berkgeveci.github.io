import vtk
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase

class Source(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=0,
            nOutputPorts=1, outputType='vtkPolyData')

    def RequestData(self, request, inInfo, outInfo):
        info = outInfo.GetInformationObject(0)
        output = vtk.vtkPolyData.GetData(info)
        print info
        return 1

class Filter0(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=2, inputType='vtkPolyData',
            nOutputPorts=2, outputType='vtkPolyData')

    def FillInputPortInformation(self, port, info):
        if port == 0:
            info.Set(vtk.vtkAlgorithm.INPUT_IS_REPEATABLE(), 1)
        return 1

    def RequestData(self, request, inInfo, outInfo):
#        print inInfo
#        print inInfo[0], inInfo[1]
        info = inInfo[0].GetInformationObject(0)
        input = vtk.vtkPolyData.GetData(info)
#        print input
        info = outInfo.GetInformationObject(0)
        output = vtk.vtkPolyData.GetData(info)
#        print output
        return 1

class Filter1(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkPolyData',
            nOutputPorts=1, outputType='vtkPolyData')

    def RequestData(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        input = vtk.vtkPolyData.GetData(info)
        info = outInfo.GetInformationObject(0)
        output = vtk.vtkPolyData.GetData(info)
        return 1

s0 = Source()
s1 = Source()
s2 = Source()

f0 = Filter0()
f0.AddInputConnection(0, s0.GetOutputPort())
f0.AddInputConnection(0, s1.GetOutputPort())
f0.SetInputConnection(1, s2.GetOutputPort())

f1 = Filter1()
f1.SetInputConnection(f0.GetOutputPort(0))

f2 = Filter1()
f2.SetInputConnection(f0.GetOutputPort(1))

f1.Update()
f2.Update()