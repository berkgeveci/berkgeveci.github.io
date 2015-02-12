/*=========================================================================

  Program:   Visualization Toolkit
  Module:    vtkCellSet.h

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/
// .NAME vtkCellSet - Uses an Exodus II element block as a
//  vtkMappedUnstructuredGrid's implementation.
//
// .SECTION Description
// This class allows raw data arrays returned by the Exodus II library to be
// used directly in VTK without repacking the data into the vtkUnstructuredGrid
// memory layout. Use the vtkCPExodusIIInSituReader to read an Exodus II file's
// data into this structure.

#ifndef vtkCellSet_h
#define vtkCellSet_h

#include "vtkObject.h"

#include "vtkMappedUnstructuredGrid.h" // For mapped unstructured grid wrapper

#include <string> // For std::string

class vtkGenericCell;
class vtkDataSet;
class vtkIdTypeArray;

class vtkCellSetImpl : public vtkObject
{
public:
  static vtkCellSetImpl *New();
  virtual void PrintSelf(ostream &os, vtkIndent indent);
  vtkTypeMacro(vtkCellSetImpl, vtkObject)

  void SetDataSet(vtkDataSet*);
  void SetCellIds(vtkIdTypeArray*);

  // API for vtkMappedUnstructuredGrid's implementation.
  vtkIdType GetNumberOfCells();
  int GetCellType(vtkIdType cellId);
  void GetCellPoints(vtkIdType cellId, vtkIdList *ptIds);
  void GetPointCells(vtkIdType ptId, vtkIdList *cellIds);
  int GetMaxCellSize();
  void GetIdsOfCellsOfType(int type, vtkIdTypeArray *array);
  int IsHomogeneous();

  // This container is read only -- these methods do nothing but print a
  // warning.
  void Allocate(vtkIdType numCells, int extSize = 1000);
  vtkIdType InsertNextCell(int type, vtkIdList *ptIds);
  vtkIdType InsertNextCell(int type, vtkIdType npts, vtkIdType *ptIds);
  vtkIdType InsertNextCell(int type, vtkIdType npts, vtkIdType *ptIds,
                           vtkIdType nfaces, vtkIdType *faces);
  void ReplaceCell(vtkIdType cellId, int npts, vtkIdType *pts);

protected:
  vtkCellSetImpl();
  ~vtkCellSetImpl();

private:
  vtkCellSetImpl(const vtkCellSetImpl &); // Not implemented.
  void operator=(const vtkCellSetImpl &);   // Not implemented.

  vtkDataSet* DataSet;
  vtkIdTypeArray* CellIds;
};

vtkMakeMappedUnstructuredGrid(vtkCellSet,
                              vtkCellSetImpl)

#endif //vtkCellSet_h
