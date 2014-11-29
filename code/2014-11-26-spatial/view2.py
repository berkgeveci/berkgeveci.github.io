from vtk.numpy_interface import dataset_adapter as dsa
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
import vtk
import numpy as np

w = vtk.vtkRTAnalyticSource()
w.SetWholeExtent(-100, 100, -100, 100, -100, 100)

def execute(obj, event):
    print w.GetOutput().GetExtent()
w.AddObserver(vtk.vtkCommand.EndEvent, execute)

c = vtk.vtkContourFilter()
c.SetInputConnection(w.GetOutputPort())
c.SetValue(0, 180)

ps = vtk.vtkPieceScalars()
ps.SetInputConnection(c.GetOutputPort())

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputConnection(ps.GetOutputPort())
mapper.SetNumberOfSubPieces(20)
mapper.SetScalarRange(0, 20)

actor = vtk.vtkActor()
actor.SetMapper(mapper)

ren = vtk.vtkRenderer()
ren.AddActor(actor)

renWin = vtk.vtkRenderWindow()
renWin.AddRenderer(ren)
renWin.SetSize(600, 600)
ren.GetActiveCamera().SetPosition(0, 0, 400)
renWin.Render()

import time
time.sleep(5)