from source import *

class PointOverTime(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkDataSet',
            nOutputPorts=1, outputType='vtkTable')

    def RequestInformation(self, request, inInfo, outInfo):
        # Reset values.
        self.UpdateTimeIndex = 0
        info = inInfo[0].GetInformationObject(0)
        self.TimeValues = info.Get(vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS())
        self.ValueOverTime = np.zeros(len(self.TimeValues))
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        # Ask for the next timestep.
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP(),
            self.TimeValues[self.UpdateTimeIndex])
        return 1

    def RequestData(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        inp = dsa.WrapDataObject(vtk.vtkDataSet.GetData(info))
        # Extract the value for the current time step.
        self.ValueOverTime[self.UpdateTimeIndex] = inp.PointData['vectors'][0, 0]
        if self.UpdateTimeIndex < len(self.TimeValues) - 1:
            # If we are not done, ask the pipeline to re-execute us.
            self.UpdateTimeIndex += 1
            request.Set(vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING(), 1)
        else:
            # We are done. Populate the output.
            output = dsa.WrapDataObject(vtk.vtkTable.GetData(outInfo))
            output.RowData.append(self.ValueOverTime, 'u over time')
            # Stop execution
            request.Remove(vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING())
        return 1

s = VelocitySource()

f = PointOverTime()
f.SetInputConnection(s.GetOutputPort())
f.Update()
vot = dsa.WrapDataObject(f.GetOutputDataObject(0)).RowData['u over time']
import matplotlib.pyplot as plt
plt.plot(f.TimeValues, vot)
plt.grid()
plt.axes().set_xlabel("t")
plt.axes().set_ylabel("u")
plt.savefig('u_over_time.png')
