from vtk.numpy_interface import dataset_adapter as dsa
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import vtk
import numpy as np

class StreamExtents(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkImageData',
            nOutputPorts=0)

        self.Contour = vtk.vtkContourFilter()
        self.Contour.SetValue(0, 180)
        self.UpdateIndex = 0
        self.NumberOfBlocks = 20

        self.Mapper = vtk.vtkPolyDataMapper()
        self.Mapper.SetScalarRange(0, 20)

        actor = vtk.vtkActor()
        actor.SetMapper(self.Mapper)

        ren = vtk.vtkRenderer()
        ren.AddActor(actor)

        self.RenWin = vtk.vtkRenderWindow()
        self.RenWin.AddRenderer(ren)
        self.RenWin.Render()
        ren.GetActiveCamera().SetPosition(0, 0, 400)
        self.RenWin.SetSize(600, 600)
        # This allows us to stream into the view. OpenGL
        # takes care of compositing using the z-buffer
        # when Erase is set to off.
        self.RenWin.EraseOff()
        self.RenWin.DoubleBufferOff()

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        # Ask for the next extent.
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_NUMBER_OF_PIECES(),
            self.NumberOfBlocks)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_PIECE_NUMBER(),
            self.UpdateIndex)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        inp = dsa.WrapDataObject(vtk.vtkDataSet.GetData(info))

        self.Contour.SetInputData(inp.VTKObject)
        self.Contour.Update()
        contour = dsa.WrapDataObject(self.Contour.GetOutput())
        rtdata = contour.PointData['RTData']
        color = np.empty_like(rtdata)
        color[:] = self.UpdateIndex
        contour.PointData.append(color, "color")
        contour.PointData.SetActiveScalars("color")

        self.Mapper.SetInputData(contour.VTKObject)
        self.RenWin.Render()

        w2i = vtk.vtkWindowToImageFilter()
        w2i.SetInput(self.RenWin)

        w = vtk.vtkPNGWriter()
        w.SetInputConnection(w2i.GetOutputPort())
        w.SetFileName("composite_step%02d.png" % self.UpdateIndex)
        w.Write()

        if self.UpdateIndex < self.NumberOfBlocks - 1:
            # If we are not done, ask the pipeline to re-execute us.
            self.UpdateIndex += 1
            request.Set(vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING(), 1)
        else:
            # Stop execution
            request.Remove(vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING())
            # Reset for next potential execution.
            self.UpdateIndex = 0

            w2i = vtk.vtkWindowToImageFilter()
            w2i.SetInput(self.RenWin)

            w = vtk.vtkPNGWriter()
            w.SetInputConnection(w2i.GetOutputPort())
            w.SetFileName("composite1.png")
            w.Write()

        return 1

w = vtk.vtkRTAnalyticSource()
w.SetWholeExtent(-100, 100, -100, 100, -100, 100)

s = StreamExtents()
s.SetInputConnection(w.GetOutputPort())

s.Update()
