import numpy as np
import vtk
from vtk.numpy_interface import dataset_adapter as dsa
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase

t = np.linspace(0, 2*np.pi, 20)

class VelocitySource(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=0,
            nOutputPorts=1, outputType='vtkImageData')

    def RequestInformation(self, request, inInfo, outInfo):
        info = outInfo.GetInformationObject(0)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT(),
            (0, 60, 0, 60, 0, 0), 6)

        info.Set(vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS(), t, len(t))
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.TIME_RANGE(), [t[0], t[-1]], 2)

        return 1

    def RequestData(self, request, inInfo, outInfo):
        info = outInfo.GetInformationObject(0)
        ue = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT())
        ue = np.array(ue)

        output = vtk.vtkImageData.GetData(outInfo)

        dims = ue[1::2] - ue[0::2] + 1
        origin = 0
        spacing = 0.1

        t = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP())

        y = origin + spacing*np.arange(ue[2],  ue[3]+1)
        u = np.exp(-y/np.sqrt(2))*np.sin(t-y/np.sqrt(2))

        a = np.zeros((3, dims[0], dims[1]), order='F')
        nx = a.shape[0]
        a[0, :] = u

        output.SetExtent(*ue)
        output.SetSpacing(0.5, 0.1, 0.1)

        v = dsa.numpyTovtkDataArray(a.ravel(order='A').reshape(dims[0]*dims[1], 3))
        v.SetName("vectors")
        output.GetPointData().SetVectors(v)

        return 1

s = VelocitySource()
s.UpdateInformation()
#s.SetUpdateExtent((0, 0, 1, 1, 0, 0))
s.GetOutputInformation(0).Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP(), t[2])
s.Update()
i = s.GetOutputDataObject(0)
print t[2], i.GetPointData().GetVectors().GetTuple3(0)