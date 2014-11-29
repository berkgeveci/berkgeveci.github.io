import numpy as np
from vtk.numpy_interface import dataset_adapter as dsa
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import vtk

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
        # We produce only the extent that we are asked (UPDATE_EXTENT)
        ue = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT())
        ue = np.array(ue)

        output = vtk.vtkImageData.GetData(outInfo)

        # Parameters of the grid to produce
        dims = ue[1::2] - ue[0::2] + 1
        origin = 0
        spacing = 0.1

        # The time step requested
        t = info.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP())

        # The velocity vs y
        y = origin + spacing*np.arange(ue[2],  ue[3]+1)
        u = np.exp(-y/np.sqrt(2))*np.sin(t-y/np.sqrt(2))

        # Set the velocity for all points of the grid which
        # has of dimensions 3, dims[0], dims[1]. The first number
        # is because of 3 components in the vector. Note the
        # memory layout VTK uses is a bit unusual. It's Fortran
        # ordered but the velocity component increases fastest.
        a = np.zeros((3, dims[0], dims[1]), order='F')
        nx = a.shape[0]
        a[0, :] = u

        output.SetExtent(*ue)
        output.SetSpacing(0.5, 0.1, 0.1)

        # Make a VTK array from the numpy array (using pointers)
        v = dsa.numpyTovtkDataArray(a.ravel(order='A').reshape(dims[0]*dims[1], 3))
        v.SetName("vectors")
        output.GetPointData().SetVectors(v)

        return 1
