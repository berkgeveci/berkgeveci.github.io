from vtk.numpy_interface import dataset_adapter as dsa
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import vtk
import numpy as np

class StreamExtents(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkImageData',
            nOutputPorts=1, outputType='vtkMultiBlockDataSet')

        self.Contour = vtk.vtkContourFilter()
        self.Contour.SetValue(0, 180)
        self.UpdateIndex = 0
        self.NumberOfBlocks = 20
        self.ExtentTranslator = vtk.vtkExtentTranslator()
        self.ExtentTranslator.SetNumberOfPieces(self.NumberOfBlocks)

    def RequestInformation(self, request, inInfo, outInfo):
        # We need to report that we are a time source to downstream.
        # We will use the TIME_VALUES from upstream for this.
        info = inInfo[0].GetInformationObject(0)
        wholeExtent = info.Get(
            vtk.vtkStreamingDemandDrivenPipeline.WHOLE_EXTENT())
        self.ExtentTranslator.SetWholeExtent(wholeExtent)

        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        # Ask for the next extent.
        self.ExtentTranslator.SetPiece(self.UpdateIndex)
        self.ExtentTranslator.PieceToExtent()
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_EXTENT(),
            self.ExtentTranslator.GetExtent(), 6)
        print self.ExtentTranslator.GetExtent()
        return 1

    def RequestData(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        inp = dsa.WrapDataObject(vtk.vtkDataSet.GetData(info))
        output = vtk.vtkMultiBlockDataSet.GetData(outInfo)

        if output.GetNumberOfBlocks() == 0:
            output.SetNumberOfBlocks(self.NumberOfBlocks)

        self.Contour.SetInputData(inp.VTKObject)
        self.Contour.Update()
        print self.UpdateIndex, self.Contour.GetOutput().GetNumberOfCells()
        contour = dsa.WrapDataObject(self.Contour.GetOutput())
        rtdata = contour.PointData['RTData']
        color = np.empty_like(rtdata)
        color[:] = self.UpdateIndex
        contour.PointData.append(color, "color")
        contour.PointData.SetActiveScalars("color")
        if contour.GetNumberOfCells() > 0:
            block = vtk.vtkPolyData()
            block.ShallowCopy(contour.VTKObject)
            output.SetBlock(self.UpdateIndex, block)

        if self.UpdateIndex < self.NumberOfBlocks - 1:
            # If we are not done, ask the pipeline to re-execute us.
            self.UpdateIndex += 1
            request.Set(
                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING(),
                1)
        else:
            # Stop execution
            request.Remove(
                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING())
            # Reset for next potential execution.
            self.UpdateIndex = 0
        return 1

w = vtk.vtkRTAnalyticSource()
w.SetWholeExtent(-100, 100, -100, 100, -100, 100)

s = StreamExtents()
s.SetInputConnection(w.GetOutputPort())

m = vtk.vtkCompositePolyDataMapper()
m.SetInputConnection(s.GetOutputPort())
m.SetScalarRange(0, 20)

a = vtk.vtkActor()
a.SetMapper(m)

ren = vtk.vtkRenderer()
ren.AddActor(a)

renWin = vtk.vtkRenderWindow()
renWin.SetSize(800, 800)
renWin.AddRenderer(ren)

renWin.Render()

import time
time.sleep(10)