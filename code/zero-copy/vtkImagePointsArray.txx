/*=========================================================================

  Program:   Visualization Toolkit
  Module:    vtkImagePointsArray.txx

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/

#include "vtkImagePointsArray.h"

#include "vtkIdList.h"
#include "vtkObjectFactory.h"
#include "vtkVariant.h"
#include "vtkVariantCast.h"
#include "vtkImageData.h"

//------------------------------------------------------------------------------
// Can't use vtkStandardNewMacro on a templated class.
template <class Scalar> vtkImagePointsArray<Scalar> *
vtkImagePointsArray<Scalar>::New()
{
  VTK_STANDARD_NEW_BODY(vtkImagePointsArray<Scalar>)
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::PrintSelf(ostream &os, vtkIndent indent)
{
  this->vtkImagePointsArray<Scalar>::Superclass::PrintSelf(
        os, indent);

  os << indent << "TempDoubleArray: " << this->TempDoubleArray << "\n";
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::InitializeArray(vtkImageData* points)
{
  this->MaxId = points->GetNumberOfPoints()*3 - 1;
  this->Size = this->MaxId + 1;
  this->NumberOfComponents = 3;
  this->Points = points;
  points->Register(this);
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::Initialize()
{
  if (this->Points)
    {
    this->Points->Delete();
    this->Points = 0;
    }

  this->MaxId = -1;
  this->Size = 0;
  this->NumberOfComponents = 3;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::GetTuples(vtkIdList *ptIds, vtkAbstractArray *output)
{
  vtkDataArray *da = vtkDataArray::FastDownCast(output);
  if (!da)
    {
    vtkWarningMacro(<<"Input is not a vtkDataArray");
    return;
    }

  if (da->GetNumberOfComponents() != this->GetNumberOfComponents())
    {
    vtkWarningMacro(<<"Incorrect number of components in input array.");
    return;
    }

  const vtkIdType numPoints = ptIds->GetNumberOfIds();
  for (vtkIdType i = 0; i < numPoints; ++i)
    {
    da->SetTuple(i, this->GetTuple(ptIds->GetId(i)));
    }
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::GetTuples(vtkIdType p1, vtkIdType p2, vtkAbstractArray *output)
{
  vtkDataArray *da = vtkDataArray::FastDownCast(output);
  if (!da)
    {
    vtkErrorMacro(<<"Input is not a vtkDataArray");
    return;
    }

  if (da->GetNumberOfComponents() != this->GetNumberOfComponents())
    {
    vtkErrorMacro(<<"Incorrect number of components in input array.");
    return;
    }

  for (vtkIdType daTupleId = 0; p1 <= p2; ++p1)
    {
    da->SetTuple(daTupleId++, this->GetTuple(p1));
    }
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::Squeeze()
{
  // noop
}

//------------------------------------------------------------------------------
template <class Scalar> vtkArrayIterator*
vtkImagePointsArray<Scalar>::NewIterator()
{
  vtkErrorMacro(<<"Not implemented.");
  return NULL;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkImagePointsArray<Scalar>
::LookupValue(vtkVariant value)
{
  bool valid = true;
  Scalar val = vtkVariantCast<Scalar>(value, &valid);
  if (valid)
    {
    // return this->Lookup(val, 0);
    }
  return -1;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::LookupValue(vtkVariant value, vtkIdList *ids)
{
  /*
  bool valid = true;
  Scalar val = vtkVariantCast<Scalar>(value, &valid);
  ids->Reset();
  if (valid)
    {
    vtkIdType index = 0;
    while ((index = this->Lookup(val, index)) >= 0)
      {
      ids->InsertNextId(index);
      ++index;
      }
    }
  */
}

//------------------------------------------------------------------------------
template <class Scalar> vtkVariant vtkImagePointsArray<Scalar>
::GetVariantValue(vtkIdType idx)
{
  return vtkVariant(this->GetValueReference(idx));
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::ClearLookup()
{
  // no-op, no fast lookup implemented.
}

//------------------------------------------------------------------------------
template <class Scalar> double* vtkImagePointsArray<Scalar>
::GetTuple(vtkIdType i)
{
  this->GetTuple(i, this->TempDoubleArray);
  return this->TempDoubleArray;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::GetTuple(vtkIdType i, double *tuple)
{
  this->Points->GetPoint(i, tuple);
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkImagePointsArray<Scalar>
::LookupTypedValue(Scalar value)
{
//  return this->Lookup(value, 0);
  return 0;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::LookupTypedValue(Scalar value, vtkIdList *ids)
{
  /*
  ids->Reset();
  vtkIdType index = 0;
  while ((index = this->Lookup(value, index)) >= 0)
    {
    ids->InsertNextId(index);
    ++index;
    }
  */
}

//------------------------------------------------------------------------------
template <class Scalar> Scalar vtkImagePointsArray<Scalar>
::GetValue(vtkIdType idx)
{
  return this->GetValueReference(idx);
}

//------------------------------------------------------------------------------
template <class Scalar> Scalar& vtkImagePointsArray<Scalar>
::GetValueReference(vtkIdType idx)
{
  assert(this->Points);

  const vtkIdType tuple = idx / 3;
  const vtkIdType comp = idx % 3;

  return this->Points->GetPoint(tuple)[comp];
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::GetTupleValue(vtkIdType tupleId, Scalar *tuple)
{
  this->Points->GetPoint(tupleId, tuple);
}

//------------------------------------------------------------------------------
template <class Scalar> int vtkImagePointsArray<Scalar>
::Allocate(vtkIdType, vtkIdType)
{
  vtkErrorMacro("Read only container.")
  return 0;
}

//------------------------------------------------------------------------------
template <class Scalar> int vtkImagePointsArray<Scalar>
::Resize(vtkIdType)
{
  vtkErrorMacro("Read only container.")
  return 0;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::SetNumberOfTuples(vtkIdType)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::SetTuple(vtkIdType, vtkIdType, vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::SetTuple(vtkIdType, const float *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::SetTuple(vtkIdType, const double *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::InsertTuple(vtkIdType, vtkIdType, vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::InsertTuple(vtkIdType, const float *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::InsertTuple(vtkIdType, const double *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::InsertTuples(vtkIdList *, vtkIdList *, vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::InsertTuples(vtkIdType, vtkIdType, vtkIdType, vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkImagePointsArray<Scalar>
::InsertNextTuple(vtkIdType, vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return -1;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkImagePointsArray<Scalar>
::InsertNextTuple(const float *)
{

  vtkErrorMacro("Read only container.")
  return -1;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkImagePointsArray<Scalar>
::InsertNextTuple(const double *)
{
  vtkErrorMacro("Read only container.")
  return -1;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::DeepCopy(vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::DeepCopy(vtkDataArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::InterpolateTuple(vtkIdType, vtkIdList *, vtkAbstractArray *, double *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::InterpolateTuple(vtkIdType, vtkIdType, vtkAbstractArray*, vtkIdType,
                   vtkAbstractArray*, double)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::SetVariantValue(vtkIdType, vtkVariant)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::RemoveTuple(vtkIdType)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::RemoveFirstTuple()
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::RemoveLastTuple()
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::SetTupleValue(vtkIdType, const Scalar*)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::InsertTupleValue(vtkIdType, const Scalar*)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkImagePointsArray<Scalar>
::InsertNextTupleValue(const Scalar *)
{
  vtkErrorMacro("Read only container.")
  return -1;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::SetValue(vtkIdType, Scalar)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkImagePointsArray<Scalar>
::InsertNextValue(Scalar)
{
  vtkErrorMacro("Read only container.")
  return -1;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkImagePointsArray<Scalar>
::InsertValue(vtkIdType, Scalar)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkImagePointsArray<Scalar>
::vtkImagePointsArray()
  : Points(0)
{
}

//------------------------------------------------------------------------------
template <class Scalar> vtkImagePointsArray<Scalar>
::~vtkImagePointsArray()
{
  if (this->Points)
    {
    this->Points->Delete();
    this->Points = 0;
    }
}
