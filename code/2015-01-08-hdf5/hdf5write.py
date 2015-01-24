import vtk
import h5py
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtk.numpy_interface import dataset_adapter as dsa

class HDF5Writer(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkUnstructuredGrid',
            nOutputPorts=0)

        self.__FileName = ""
        self.__NumberOfPieces = 1
        self.__CurrentPiece = 0

    def RequestData(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        inp = dsa.WrapDataObject(vtk.vtkDataSet.GetData(info))

        if self.__CurrentPiece == 0:
              self.__File = h5py.File(self.__FileName, 'w')

        grp = self.__File.create_group("piece%d" % self.__CurrentPiece)
        grp.attrs['bounds'] = inp.GetBounds()

        grp.create_dataset("cells", data=inp.Cells)
        grp.create_dataset("cell_types", data=inp.CellTypes)
        grp.create_dataset("cell_locations", data=inp.CellLocations)

        grp.create_dataset("points", data=inp.Points)

        pdata = grp.create_group("point_data")
        for name in inp.PointData.keys():
            pdata.create_dataset(name, data=inp.PointData[name])

        if self.__CurrentPiece < self.__NumberOfPieces - 1:
            # If we are not done, ask the pipeline to re-execute us.
            self.__CurrentPiece += 1
            request.Set(
                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING(),
                1)
        else:
            # Stop execution
            request.Remove(
                vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING())
            self.__File.close()
            del self.__File
        return 1

    def RequestInformation(self, request, inInfo, outInfo):
        # Reset values.
        self.__CurrentPiece = 0
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_NUMBER_OF_PIECES(),
            self.__NumberOfPieces)
        info.Set(vtk.vtkStreamingDemandDrivenPipeline.UPDATE_PIECE_NUMBER(),
            self.__CurrentPiece)
        return 1

    def SetFileName(self, fname):
        if fname != self.__FileName:
            self.Modified()
            self.__FileName = fname

    def GetFileName(self):
        return self.__FileName

    def SetNumberOfPieces(self, npieces):
        if npieces != self.__NumberOfPieces:
            self.Modified()
            self.__NumberOfPieces = npieces

    def GetNumberOfPieces(self):
        return self.__NumberOfPieces

s = vtk.vtkRTAnalyticSource()

c = vtk.vtkClipDataSet()
c.SetInputConnection(s.GetOutputPort())
c.SetValue(157)

w = HDF5Writer()
w.SetInputConnection(c.GetOutputPort())
w.SetFileName("test.h5")
w.SetNumberOfPieces(5)

w.Update()
