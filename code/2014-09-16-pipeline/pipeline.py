import vtk
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtk.util import keys

metaDataKey = keys.MakeKey(keys.DataObjectMetaDataKey, "a meta-data", "my module")

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
#        print outInfo.GetInformationObject(0)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        print "MySource RequestData:"
#        print outInfo.GetInformationObject(0)
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
#        print outInfo.GetInformationObject(0)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        print "MyFilter RequestData:"
#        print outInfo.GetInformationObject(0)
        return 1

s = MySource()

f = MyFilter()
f.SetInputConnection(s.GetOutputPort())

f.UpdateInformation()