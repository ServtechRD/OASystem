from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from models import Employee
from schemas import EmployeeCreate, EmployeeUpdate, EmployeeResponse,LeaveEntitlementCreate,LeaveEntitlementUpdate,LeaveEntitlementUpdate,ChangePasswordRequest
from database import get_db
from typing import List
from utils import hash_password,verify_password;



router = APIRouter()

# 创建员工
@router.post("/employees", response_model=EmployeeResponse)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    db_employee = Employee(**employee.dict())
    db.add(db_employee)
    db.commit()
    db.refresh(db_employee)
    return db_employee

# 查询所有员工
@router.get("/employees", response_model=List[EmployeeResponse])
def get_employees(db: Session = Depends(get_db)):
    return db.query(Employee).all()

# 查询特定员工
@router.get("/employees/{emp_id}", response_model=EmployeeResponse)
def get_employee(emp_id: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee

# 更新员工
@router.put("/employees/{emp_id}", response_model=EmployeeResponse)
def update_employee(emp_id: str, updated_employee: EmployeeUpdate, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    for key, value in updated_employee.dict(exclude_unset=True).items():
        setattr(employee, key, value)
    db.commit()
    db.refresh(employee)
    return employee



# 修改密码
@router.put("/employees/change-password")
def change_password(request: ChangePasswordRequest, db: Session = Depends(get_db)):
    # 查找员工
    employee = db.query(Employee).filter(Employee.id == request.emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # 验证旧密码
    if not verify_password(request.old_password, employee.login_password):
        raise HTTPException(status_code=400, detail="Old password is incorrect")

    # 更新密码
    employee.login_password = hash_password(request.new_password)
    db.commit()
    return {"detail": "Password updated successfully"}


# 删除员工
@router.delete("/employees/{emp_id}")
def delete_employee(emp_id: str, db: Session = Depends(get_db)):
    employee = db.query(Employee).filter(Employee.id == emp_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(employee)
    db.commit()
    return {"detail": "Employee deleted"}
