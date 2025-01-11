from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import LeaveEntitlement, Employee
from schemas import LeaveEntitlementCreate, LeaveEntitlementUpdate, LeaveEntitlementResponse
from database import get_db
from typing import List

router = APIRouter()

# 创建员工假数
@router.post("/leave-entitlements", response_model=LeaveEntitlementResponse)
def create_leave_entitlement(entitlement: LeaveEntitlementCreate, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.emp_id == entitlement.emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    db_entitlement = LeaveEntitlement(**entitlement.dict())
    db.add(db_entitlement)
    db.commit()
    db.refresh(db_entitlement)
    return db_entitlement

# 查询所有员工的假数
@router.get("/leave-entitlements", response_model=List[LeaveEntitlementResponse])
def get_all_leave_entitlements(db: Session = Depends(get_db)):
    return db.query(LeaveEntitlement).all()

# 查询特定员工的假数
@router.get("/leave-entitlements/{emp_id}", response_model=List[LeaveEntitlementResponse])
def get_leave_entitlements_by_employee(emp_id: str, db: Session = Depends(get_db)):
    entitlements = db.query(LeaveEntitlement).filter(LeaveEntitlement.emp_id == emp_id).all()
    if not entitlements:
        raise HTTPException(status_code=404, detail="Leave entitlements not found")
    return entitlements

# 更新员工假数
@router.put("/leave-entitlements/{id}", response_model=LeaveEntitlementResponse)
def update_leave_entitlement(id: int, entitlement: LeaveEntitlementUpdate, db: Session = Depends(get_db)):
    db_entitlement = db.query(LeaveEntitlement).filter(LeaveEntitlement.id == id).first()
    if not db_entitlement:
        raise HTTPException(status_code=404, detail="Leave entitlement not found")
    for key, value in entitlement.dict(exclude_unset=True).items():
        setattr(db_entitlement, key, value)
    db.commit()
    db.refresh(db_entitlement)
    return db_entitlement

# 删除员工假数
@router.delete("/leave-entitlements/{id}")
def delete_leave_entitlement(id: int, db: Session = Depends(get_db)):
    db_entitlement = db.query(LeaveEntitlement).filter(LeaveEntitlement.id == id).first()
    if not db_entitlement:
        raise HTTPException(status_code=404, detail="Leave entitlement not found")
    db.delete(db_entitlement)
    db.commit()
    return {"detail": "Leave entitlement deleted"}
