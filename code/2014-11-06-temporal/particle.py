from source import *
import time

class ParticleAdvection(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkDataSet',
            nOutputPorts=1, outputType='vtkPolyData')
        self.Cache = None
        self.Source = vtk.vtkLineSource()
        self.Source.SetPoint1(3, 0, 0)
        self.Source.SetPoint2(3, 6, 0)
        self.Source.SetResolution(20)
        self.Source.Update()
        pts = vtk.vtkPoints()
        pts.DeepCopy(self.Source.GetOutput().GetPoints())
        self.Points = dsa.vtkDataArrayToVTKArray(pts.GetData())
        self.Probe = vtk.vtkProbeFilter()
        self.Probe.SetInputConnection(self.Source.GetOutputPort())

        self.RenWin = vtk.vtkRenderWindow()
        self.Ren = vtk.vtkRenderer()
        self.RenWin.AddRenderer(self.Ren)
        self.PD = vtk.vtkPolyData()
        s = vtk.vtkSphereSource()
        s.SetRadius(0.1)
        glyph = vtk.vtkGlyph3D()
        glyph.SetInputData(self.PD)
        glyph.SetSourceConnection(s.GetOutputPort())
        m = vtk.vtkPolyDataMapper()
        m.SetInputConnection(glyph.GetOutputPort())
        a = vtk.vtkActor()
        a.SetMapper(m)
        self.Ren.AddActor(a)

    def RequestInformation(self, request, inInfo, outInfo):
        # Reset values.
        self.UpdateTimeIndex = 0
        info = inInfo[0].GetInformationObject(0)
        self.TimeValues = info.Get(vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS())
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        # Ask for the next timestep.
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP(),
            self.TimeValues[self.UpdateTimeIndex])
        return 1

    def DoParticle(self, t1, t2):
        self.Probe.SetSourceData(t1.VTKObject)
        self.Probe.Modified()
        self.Probe.Update()
        p = dsa.WrapDataObject(self.Probe.GetOutput())
        v1 = p.PointData['vectors']

        self.Probe.SetSourceData(t2.VTKObject)
        self.Probe.Modified()
        self.Probe.Update()
        p = dsa.WrapDataObject(self.Probe.GetOutput())
        v2 = p.PointData['vectors']

        v = (v1+v2)/2
        dt = t[self.UpdateTimeIndex] - t[self.UpdateTimeIndex - 1]
        pts = self.Points + v*dt
        self.Points = pts
        vpts = vtk.vtkPoints()
        va = dsa.numpyTovtkDataArray(pts)
        vpts.SetData(va)
        self.PD.SetPoints(vpts)
        self.RenWin.Render()
        time.sleep(0.2)

    def RequestData(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        inp = dsa.WrapDataObject(vtk.vtkDataSet.GetData(info))

        if self.Cache is not None:
            self.DoParticle(self.Cache, inp)

        if self.UpdateTimeIndex < len(self.TimeValues) - 1:
            # If we are not done, ask the pipeline to re-execute us.
            self.UpdateTimeIndex += 1
            request.Set(vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING(), 1)
            c = inp.NewInstance()
            c.ShallowCopy(inp.VTKObject)
            c = dsa.WrapDataObject(c)
            self.Cache = c
        else:
            # Stop execution
            request.Remove(vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING())
            self.Cache = None
        return 1

s = VelocitySource()

f = ParticleAdvection()
f.SetInputConnection(s.GetOutputPort())
f.Update()
