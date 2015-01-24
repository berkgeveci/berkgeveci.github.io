import vtk, h5py
from vtk.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtk.numpy_interface import dataset_adapter as dsa

class HDF5Reader(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=0,
            nOutputPorts=1, outputType='vtkMultiBlockDataSet')

        self.__FileName = ""

    def RequestInformation(self, request, inInfo, outInfo):
        import re
        p = re.compile('piece([0-9]*)')

        md = vtk.vtkMultiBlockDataSet()
        f = h5py.File(self.__FileName, 'r')
        for grp_name in f:
            idx = int(p.match(grp_name).groups()[0])
            md.SetBlock(idx, None)
            bmd = md.GetMetaData(idx)
            idx += 1
            grp = f[grp_name]
            bds = grp.attrs['bounds']
            bmd.Set(vtk.vtkDataObject.BOUNDING_BOX(), bds, 6)

        f.close()

        outInfo.GetInformationObject(0).Set(
            vtk.vtkCompositeDataPipeline.COMPOSITE_DATA_META_DATA(),
            md)

        return 1

    def RequestData(self, request, inInfo, outInfo):
        output = dsa.WrapDataObject(vtk.vtkMultiBlockDataSet.GetData(outInfo))

        import re
        p = re.compile('piece([0-9]*)')

        f = h5py.File(self.__FileName, 'r')

        if outInfo.GetInformationObject(0).Has(
            vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES()):
            uci = outInfo.GetInformationObject(0).Get(
                vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES())
            if uci is None:
                pieces = []
            else:
                pieces = ["piece%d" % num for num in uci]
        else:
            pieces = f
        idx = 0
        nblocks = len(pieces)
        output.SetNumberOfBlocks(nblocks)
        idx = 0
        for grp_name in pieces:
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
        f.close()

        return 1

    def SetFileName(self, fname):
        if fname != self.__FileName:
            self.Modified()
            self.__FileName = fname

    def GetFileName(self):
        return self.__FileName

class PlaneCutter(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkMultiBlockDataSet',
            nOutputPorts=1, outputType='vtkMultiBlockDataSet')

        self.__Origin = (0, 0, 0)
        self.__Normal = (1, 0, 0)
        self.__BlockMap = {}

    def CheckBounds(self, bounds):
        pts = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
         (1, 1, 0), (1, 0, 1), (0, 1, 1), (1, 1, 1)]
        import numpy
        org = numpy.array(self.__Origin, dtype = numpy.float64)
        nrm = numpy.array(self.__Normal, dtype = numpy.float64)
        point = numpy.zeros((3,), dtype = numpy.float64)
        sign = None
        all_same = True
        for pt in pts:
            point[0] = bounds[pt[0]]
            point[1] = bounds[pt[1] + 2]
            point[2] = bounds[pt[2] + 4]
            sn = numpy.sign(numpy.dot(point - org, nrm))
            if sign is None:
                sign = sn
            if sign != sn:
                all_same = False
                break
        return not all_same

    def RequestInformation(self, request, inInfo, outInfo):
        inInfo0 = inInfo[0].GetInformationObject(0)
        metaData = inInfo0.Get(
            vtk.vtkCompositeDataPipeline.COMPOSITE_DATA_META_DATA())
        nblocks = metaData.GetNumberOfBlocks()
        idx = 0
        for i in range(nblocks):
            bmd = metaData.GetMetaData(i)
            if self.CheckBounds(bmd.Get(vtk.vtkDataObject.BOUNDING_BOX())):
                self.__BlockMap[idx] = i
                idx += 1

        md = vtk.vtkMultiBlockDataSet()
        for i in self.__BlockMap.keys():
            ii = self.__BlockMap[i]
            imd = metaData.GetMetaData(ii)
            bds = imd.Get(vtk.vtkDataObject.BOUNDING_BOX())
            md.SetBlock(i, None)
            bmd = md.GetMetaData(i)
            bmd.Set(vtk.vtkDataObject.BOUNDING_BOX(), bds, 6)

        outInfo.GetInformationObject(0).Set(
            vtk.vtkCompositeDataPipeline.COMPOSITE_DATA_META_DATA(),
            md)

        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        inInfo0 = inInfo[0].GetInformationObject(0)

        if outInfo.GetInformationObject(0).Has(
            vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES()):
            uci = outInfo.GetInformationObject(0).Get(
                vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES())
            if uci is None:
                uci = []
        else:
            uci = self.__BlockMap.keys()

        requestBlocks = []
        for i in uci:
            requestBlocks.append(self.__BlockMap[i])

        nblocks = len(requestBlocks)
        if nblocks == 0:
            # Special case because the Python generated code
            # does not like None instead of a NULL pointer in
            # this case.
            inInfo0.Set(
                vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES(),
                [0],
                0)
        else:
            inInfo0.Set(
                vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES(),
                requestBlocks, len(requestBlocks))

        print "Requesting: ", requestBlocks
        return 1

    def RequestData(self, request, inInfo, outInfo):
        inInfo0 = inInfo[0].GetInformationObject(0)
        inpMB = vtk.vtkMultiBlockDataSet.GetData(inInfo0)
        output = vtk.vtkMultiBlockDataSet.GetData(outInfo)

        c = vtk.vtkCutter()

        p = vtk.vtkPlane()
        p.SetNormal(self.__Normal)
        p.SetOrigin(self.__Origin)
        c.SetCutFunction(p)

        idx = 0
        itr = inpMB.NewIterator()
        while not itr.IsDoneWithTraversal():
            inp = itr.GetCurrentDataObject()
            c.SetInputData(inp)
            c.Update()
            opt = c.GetOutput().NewInstance()
            opt.ShallowCopy(c.GetOutput())
            output.SetBlock(idx, opt)
            idx += 1
            itr.GoToNextItem()

        itr.UnRegister(None)

        return 1

    def SetOrigin(self, origin):
        if origin != self.__Origin:
            self.Modified()
            self.__Origin = origin

    def GetOrigin(self):
        return self.__Origin

    def SetNormal(self, normal):
        if normal != self.__Normal:
            self.Modified()
            self.__Normal = normal

    def GetNormal(self):
        return self.__Normal

class StreamBlocks(VTKPythonAlgorithmBase):
    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
            nInputPorts=1, inputType='vtkMultiBlockDataSet',
            nOutputPorts=1, outputType='vtkMultiBlockDataSet')

        self.UpdateIndex = 0
        self.__FileName = ""

    def RequestInformation(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        blocks = info.Get(vtk.vtkCompositeDataPipeline.COMPOSITE_DATA_META_DATA())
        self.NumberOfBlocks = blocks.GetNumberOfBlocks()
        return 1

    def RequestUpdateExtent(self, request, inInfo, outInfo):
        info = inInfo[0].GetInformationObject(0)
        info.Set(
            vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES(),
            [self.UpdateIndex],
            1)
        return 1

    def RequestData(self, request, inInfo, outInfo):
        if self.UpdateIndex == 0:
              self.__File = h5py.File(self.__FileName, 'w')

        info = inInfo[0].GetInformationObject(0)
        inpMB = vtk.vtkMultiBlockDataSet.GetData(info)
        if inpMB.GetBlock(0) is not None:
            inp = dsa.WrapDataObject(inpMB.GetBlock(0))

            if inp.GetNumberOfCells() > 0:
                grp = self.__File.create_group("piece%d" % self.UpdateIndex)
                grp.attrs['bounds'] = inp.GetBounds()

                grp.create_dataset("cells", data=inp.Cells)
                grp.create_dataset("cell_types", data=inp.CellTypes)
                grp.create_dataset("cell_locations", data=inp.CellLocations)

                grp.create_dataset("points", data=inp.Points)

                pdata = grp.create_group("point_data")
                for name in inp.PointData.keys():
                    pdata.create_dataset(name, data=inp.PointData[name])

        if self.UpdateIndex < self.NumberOfBlocks - 1:
            # If we are not done, ask the pipeline to re-execute us.
            self.UpdateIndex += 1
            request.Set(vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING(), 1)
        else:
            # Stop execution
            request.Remove(vtk.vtkStreamingDemandDrivenPipeline.CONTINUE_EXECUTING())
            # Reset for next potential execution.
            self.UpdateIndex = 0

            self.__File.close()
            del self.__File
        return 1

    def SetFileName(self, fname):
        if fname != self.__FileName:
            self.Modified()
            self.__FileName = fname

    def GetFileName(self):
        return self.__FileName

r = HDF5Reader()
r.SetFileName("test.h5")

c = PlaneCutter()
c.SetInputConnection(r.GetOutputPort())
c.SetOrigin((1, 0, 0))

f = StreamBlocks()
#f.SetInputConnection(c.GetOutputPort())
f.SetInputConnection(r.GetOutputPort())
f.SetFileName("test2.h5")

#f.Update()
c.Update()
print c.GetOutputDataObject(0)

# r.UpdateInformation()
# indices = [0, 2]
# r.GetOutputInformation(0).Set(
#     vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES(),
#     indices,
#     len(indices))
# # r.GetOutputInformation(0).Set(
# #     vtk.vtkCompositeDataPipeline.UPDATE_COMPOSITE_INDICES(),
# #     [0],
# #     0)

# r.Update()
# #print r.GetOutputDataObject(0)

