import vtk
from vtk.util import keys

info = vtk.vtkInformation()
print info

key = vtk.vtkSelectionNode.SOURCE()

#key.Set(info, vtk.vtkObject())
info.Set(key, vtk.vtkObject())
print info

key = keys.MakeKey(keys.ObjectBaseKey, "a new key", "some class")
print "key:\n", key

info = vtk.vtkInformation()
print "info:\n", info

key.Set(info, vtk.vtkObject())
print "info after set:\n", info

key = keys.MakeKey(keys.IntegerKey, "another key", "some class")

key.Set(info, 12)
print info

key = keys.MakeKey(keys.IntegerKey, "another key", "some class")

iv = vtk.vtkInformationVector()

i1 = vtk.vtkInformation()
i1.Set(key, 10)
iv.Append(i1)

i2 = vtk.vtkInformation()
i2.Set(key, 20)
iv.Append(i2)

print iv

for i in range(2):
    print iv.GetInformationObject(i)

info = vtk.vtkInformation()
info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_PIECE_NUMBER(), 1)

print vtk.vtkStreamingDemandDrivenPipeline.UPDATE_PIECE_NUMBER()
print info