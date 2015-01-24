import vtk, h5py
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtk.numpy_interface import dataset_adapter as dsa

class HDF5Reader(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=0,
            nOutputPorts=1, outputType='vtkMultiBlockDataSet')

        self.__FileName = ""

    def RequestData(self, request, inInfo, outInfo):
        output = dsa.WrapDataObject(vtk.vtkMultiBlockDataSet.GetData(outInfo))
        f = h5py.File(self.__FileName, 'r')
        idx = 0
        for grp_name in f:
            ug = vtk.vtkUnstructuredGrid()
            output.SetBlock(idx, ug)
            idx += 1
            ug = dsa.WrapDataObject(ug)
            grp = f[grp_name]
            cells = grp['cells'][:]
            locations = grp['cell_locations'][:]
            types = grp['cell_types'][:]
            ug.SetCells(types, locations, cells)
            pts = grp['points'][:]
            ug.Points = pts
            pt_arrays = grp['point_data']
            for pt_array in pt_arrays:
                array = pt_arrays[pt_array][:]
                ug.PointData.append(array, pt_array)

        return 1

    def SetFileName(self, fname):
        if fname != self.__FileName:
            self.Modified()
            self.__FileName = fname

    def GetFileName(self):
        return self.__FileName

r = HDF5Reader()
r.SetFileName("test.h5")
r.Update()

w = vtk.vtkXMLMultiBlockDataWriter()
w.SetInputConnection(r.GetOutputPort())
w.SetFileName("foo.vtm")
w.Write()
