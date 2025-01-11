from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import and_
from schemas import LeaveResponse

from database import get_db
from models import LeaveRecord, LeaveEntitlement
from typing import List
from datetime import datetime



router = APIRouter()

@router.post("/leave")
def request_leave(emp_id: str, leave_type: str, start_datetime: str, end_datetime: str, db: Session = Depends(get_db)):
    entitlement = db.query(LeaveEntitlement).filter_by(emp_id=emp_id, leave_type=leave_type).first()
    if not entitlement or entitlement.entitlement_days <= 0:
        raise HTTPException(status_code=400, detail="Insufficient leave balance")
    leave = LeaveRecord(emp_id=emp_id, leave_type=leave_type, start_datetime=start_datetime, end_datetime=end_datetime)
    db.add(leave)
    db.commit()
    return {"message": "Leave requested"}



# 查询特定员工在特定时间区间内的请假数据
@router.get("/leave-records/{emp_id}/time-range", response_model=List[LeaveResponse])
def get_leave_records_by_employee_and_time(
    emp_id: str,
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db)
):
    """
    查询特定员工在特定时间区间内的请假数据。
    """
    records = db.query(LeaveRecord).filter(
        and_(
            LeaveRecord.emp_id == emp_id,
            LeaveRecord.start_datetime >= start_date,
            LeaveRecord.end_datetime <= end_date
        )
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail="No leave records found for the specified employee and time range")
    return records

# 查询所有员工在特定时间区间内的请假数据
@router.get("/leave-records/time-range", response_model=List[LeaveResponse])
def get_leave_records_by_time(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db)
):
    """
    查询所有员工在特定时间区间内的请假数据。
    """
    records = db.query(LeaveRecord).filter(
        and_(
            LeaveRecord.start_datetime >= start_date,
            LeaveRecord.end_datetime <= end_date
        )
    ).all()

    if not records:
        raise HTTPException(status_code=404, detail="No leave records found for the specified time range")
    return records
