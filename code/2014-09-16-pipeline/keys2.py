from vtk.util import keys
from vtk.vtkCommonCore import vtkInformation

print keys.IntegerKey
k = keys.MakeKey(keys.IntegerKey, "foo", "bar")
print k.GetName()

k2 = keys.MakeKey(keys.IntegerVectorKey, "test", "me", 3)
print k2

info = vtkInformation()
k2.Set(info, (1,2,3), 3)
print info