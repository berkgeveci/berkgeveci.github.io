from particle import *

class AnimateParticles(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkUnstructuredGrid',
            nOutputPorts=1, outputType='vtkUnstructuredGrid')

        self.Threshold = vtk.vtkThreshold()

    def RequestInformation(self, request, inInfo, outInfo):
        # We need to report that we are a time source to downstream.
        # We will use the TIME_VALUES from upstream for this.
        info = inInfo[0].GetInformationObject(0)
        self.TimeValues = info.Get(TIME_VALUES)
        outInfo.GetInformationObject(0).Set(
            vtk.vtkStreamingDemandDrivenPipeline.TIME_STEPS(),
            self.TimeValues,
            len(self.TimeValues))
        tr = [self.TimeValues[0], self.TimeValues[-1]]
        outInfo.GetInformationObject(0).Set(
            vtk.vtkStreamingDemandDrivenPipeline.TIME_RANGE(), tr, 2)

        return 1


    def RequestData(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        inp = dsa.WrapDataObject(
            vtk.vtkUnstructuredGrid.GetData(info))

        oinfo = outInfo.GetInformationObject(0)
        if oinfo.Has(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP()):
            ut = oinfo.Get(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP())
        else:
            ut = self.TimeValues[0]
        # Simply extract the particles where the Time Values array
        # matches the requested time value.
        tvs = inp.PointData['Time Values']
        newpts = dsa.numpyTovtkDataArray(inp.Points[np.where(tvs == ut)])
        pts = vtk.vtkPoints()
        pts.SetData(newpts)

        output = vtk.vtkUnstructuredGrid.GetData(outInfo)
        output.SetPoints(pts)

        return 1

s = VelocitySource()

pa = ParticleAdvection()
pa.SetInputConnection(s.GetOutputPort())

anim = AnimateParticles()
anim.SetInputConnection(pa.GetOutputPort())
anim.Update()

renWin = vtk.vtkRenderWindow()
ren = vtk.vtkRenderer()
renWin.AddRenderer(ren)
s = vtk.vtkSphereSource()
s.SetRadius(0.03)
glyph = vtk.vtkGlyph3D()
glyph.SetInputConnection(anim.GetOutputPort())
glyph.SetSourceConnection(s.GetOutputPort())
glyph.SetScaleModeToDataScalingOff()
m = vtk.vtkPolyDataMapper()
m.SetInputConnection(glyph.GetOutputPort())
a = vtk.vtkActor()
a.SetMapper(m)
ren.AddActor(a)
renWin.SetSize(500, 500)
to_image = vtk.vtkWindowToImageFilter()
to_image.SetInput(renWin)
to_png = vtk.vtkPNGWriter()
to_png.SetInputConnection(to_image.GetOutputPort())
idx = 0
for time in t:
    glyph.GetOutputInformation(0).Set(
        vtk.vtkStreamingDemandDrivenPipeline.UPDATE_TIME_STEP(),
        time)
    glyph.Update()
    renWin.Render()

    to_image.Modified()
    to_png.SetFileName("particles%03d.png" % idx)
    idx += 1
    to_png.Write()