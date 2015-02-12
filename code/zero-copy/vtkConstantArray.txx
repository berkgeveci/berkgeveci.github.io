/*=========================================================================

  Program:   Visualization Toolkit
  Module:    vtkConstantArray.txx

  Copyright (c) Ken Martin, Will Schroeder, Bill Lorensen
  All rights reserved.
  See Copyright.txt or http://www.kitware.com/Copyright.htm for details.

     This software is distributed WITHOUT ANY WARRANTY; without even
     the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
     PURPOSE.  See the above copyright notice for more information.

=========================================================================*/

#include "vtkConstantArray.h"

#include "vtkIdList.h"
#include "vtkObjectFactory.h"
#include "vtkVariant.h"
#include "vtkVariantCast.h"

//------------------------------------------------------------------------------
// Can't use vtkStandardNewMacro on a templated class.
template <class Scalar> vtkConstantArray<Scalar> *
vtkConstantArray<Scalar>::New()
{
  VTK_STANDARD_NEW_BODY(vtkConstantArray<Scalar>)
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::PrintSelf(ostream &os, vtkIndent indent)
{
  this->vtkConstantArray<Scalar>::Superclass::PrintSelf(
        os, indent);

  os << indent << "TempDoubleArray: " << this->TempDoubleArray << "\n";
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::InitializeArray(Scalar value, vtkIdType size, int numComps)
{
  this->MaxId = size - 1;
  this->Size = size;
  this->NumberOfComponents = numComps;
  this->Value = value;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::Initialize()
{
  delete [] this->TempDoubleArray;
  this->TempDoubleArray = NULL;

  this->MaxId = -1;
  this->Size = 0;
  this->NumberOfComponents = 1;
  this->Value = 0;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
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
template <class Scalar> void vtkConstantArray<Scalar>
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
template <class Scalar> void vtkConstantArray<Scalar>
::Squeeze()
{
  // noop
}

//------------------------------------------------------------------------------
template <class Scalar> vtkArrayIterator*
vtkConstantArray<Scalar>::NewIterator()
{
  vtkErrorMacro(<<"Not implemented.");
  return NULL;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkConstantArray<Scalar>
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
template <class Scalar> void vtkConstantArray<Scalar>
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
template <class Scalar> vtkVariant vtkConstantArray<Scalar>
::GetVariantValue(vtkIdType idx)
{
  return vtkVariant(this->GetValueReference(idx));
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::ClearLookup()
{
  // no-op, no fast lookup implemented.
}

//------------------------------------------------------------------------------
template <class Scalar> double* vtkConstantArray<Scalar>
::GetTuple(vtkIdType i)
{
  this->GetTuple(i, this->TempDoubleArray);
  return this->TempDoubleArray;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::GetTuple(vtkIdType i, double *tuple)
{
  /*
  for (size_t comp = 0; comp < this->Arrays.size(); ++comp)
    {
    tuple[comp] = static_cast<double>(this->Arrays[comp][i]);
    }
  */
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkConstantArray<Scalar>
::LookupTypedValue(Scalar value)
{
//  return this->Lookup(value, 0);
  return 0;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
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
template <class Scalar> Scalar vtkConstantArray<Scalar>
::GetValue(vtkIdType idx)
{
  return this->GetValueReference(idx);
}

//------------------------------------------------------------------------------
template <class Scalar> Scalar& vtkConstantArray<Scalar>
::GetValueReference(vtkIdType idx)
{
  return this->Value;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::GetTupleValue(vtkIdType tupleId, Scalar *tuple)
{
  /*
  for (size_t comp = 0; comp < this->Arrays.size(); ++comp)
    {
    tuple[comp] = this->Arrays[comp][tupleId];
    }
  */
}

//------------------------------------------------------------------------------
template <class Scalar> int vtkConstantArray<Scalar>
::Allocate(vtkIdType, vtkIdType)
{
  vtkErrorMacro("Read only container.")
  return 0;
}

//------------------------------------------------------------------------------
template <class Scalar> int vtkConstantArray<Scalar>
::Resize(vtkIdType)
{
  vtkErrorMacro("Read only container.")
  return 0;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::SetNumberOfTuples(vtkIdType)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::SetTuple(vtkIdType, vtkIdType, vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::SetTuple(vtkIdType, const float *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::SetTuple(vtkIdType, const double *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::InsertTuple(vtkIdType, vtkIdType, vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::InsertTuple(vtkIdType, const float *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::InsertTuple(vtkIdType, const double *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::InsertTuples(vtkIdList *, vtkIdList *, vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::InsertTuples(vtkIdType, vtkIdType, vtkIdType, vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkConstantArray<Scalar>
::InsertNextTuple(vtkIdType, vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return -1;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkConstantArray<Scalar>
::InsertNextTuple(const float *)
{

  vtkErrorMacro("Read only container.")
  return -1;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkConstantArray<Scalar>
::InsertNextTuple(const double *)
{
  vtkErrorMacro("Read only container.")
  return -1;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::DeepCopy(vtkAbstractArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::DeepCopy(vtkDataArray *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::InterpolateTuple(vtkIdType, vtkIdList *, vtkAbstractArray *, double *)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::InterpolateTuple(vtkIdType, vtkIdType, vtkAbstractArray*, vtkIdType,
                   vtkAbstractArray*, double)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::SetVariantValue(vtkIdType, vtkVariant)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::RemoveTuple(vtkIdType)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::RemoveFirstTuple()
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::RemoveLastTuple()
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::SetTupleValue(vtkIdType, const Scalar*)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::InsertTupleValue(vtkIdType, const Scalar*)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkConstantArray<Scalar>
::InsertNextTupleValue(const Scalar *)
{
  vtkErrorMacro("Read only container.")
  return -1;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::SetValue(vtkIdType, Scalar)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkIdType vtkConstantArray<Scalar>
::InsertNextValue(Scalar)
{
  vtkErrorMacro("Read only container.")
  return -1;
}

//------------------------------------------------------------------------------
template <class Scalar> void vtkConstantArray<Scalar>
::InsertValue(vtkIdType, Scalar)
{
  vtkErrorMacro("Read only container.")
  return;
}

//------------------------------------------------------------------------------
template <class Scalar> vtkConstantArray<Scalar>
::vtkConstantArray()
  : TempDoubleArray(NULL), Value(0)
{
}

//------------------------------------------------------------------------------
template <class Scalar> vtkConstantArray<Scalar>
::~vtkConstantArray()
{
  delete [] this->TempDoubleArray;
}
