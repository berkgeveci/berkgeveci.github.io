import vtk
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtk.util import keys

metaDataKey = keys.MakeKey(keys.DataObjectMetaDataKey, "a meta-data", "my module")
requestKey = keys.MakeKey(keys.IntegerRequestKey, "a request", "my module")

class MySource(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=0,
            nOutputPorts=1, outputType='vtkPolyData')

    def RequestInformation(self, request, inInfo, outInfo):
        print "MySource RequestInformation:"
        outInfo.GetInformationObject(0).Set(metaDataKey, vtk.vtkPolyData())
        print outInfo.GetInformationObject(0)
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        print "MySource RequestUpdateExtent:"
        print outInfo.GetInformationObject(0)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        print "MySource RequestData:"
        outInfo0 = outInfo.GetInformationObject(0)
        areq = outInfo0.Get(requestKey)
        s = vtk.vtkSphereSource()
        s.SetRadius(areq)
        s.Update()
        output = outInfo0.Get(vtk.vtkDataObject.DATA_OBJECT())
        output.ShallowCopy(s.GetOutput())
        print output
        return 1

class MyFilter(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkPolyData',
            nOutputPorts=1, outputType='vtkPolyData')

    def RequestInformation(self, request, inInfo, outInfo):
        print "MyFilter RequestInformation:"
        print outInfo.GetInformationObject(0)
        metaData = inInfo[0].GetInformationObject(0).Get(
            metaDataKey)
        newMetaData = metaData.NewInstance()
        newMetaData.ShallowCopy(metaData)
        someArray = vtk.vtkCharArray()
        someArray.SetName("someArray")
        newMetaData.GetFieldData().AddArray(someArray)
        outInfo.GetInformationObject(0).Set(metaDataKey, newMetaData)
        print outInfo.GetInformationObject(0)
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        print "MyFilter RequestUpdateExtent:"
        print outInfo.GetInformationObject(0)
        areq = outInfo.GetInformationObject(0).Get(requestKey)
        inInfo[0].GetInformationObject(0).Set(requestKey, areq + 1)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        print "MyFilter RequestData:"
        inInfo0 = inInfo[0].GetInformationObject(0)
        outInfo0 = outInfo.GetInformationObject(0)
        input = inInfo0.Get(vtk.vtkDataObject.DATA_OBJECT())
        output = outInfo0.Get(vtk.vtkDataObject.DATA_OBJECT())
        sh = vtk.vtkShrinkPolyData()
        sh.SetInputData(input)
        sh.Update()
        output.ShallowCopy(sh.GetOutput())
        print output
        return 1

s = MySource()

f = MyFilter()
f.SetInputConnection(s.GetOutputPort())

f.UpdateInformation()
outInfo = f.GetOutputInformation(0)
outInfo.Set(requestKey, 0)
f.Update()
