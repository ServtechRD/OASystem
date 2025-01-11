from fastapi import APIRouter, Depends, HTTPException,Form
from sqlalchemy.orm import Session
from database import get_db
from models import Employee
from utils import verify_password

router = APIRouter()

@router.post("/login")
def login(email: str=Form(...), password: str=Form(...), db: Session = Depends(get_db)):
    user = db.query(Employee).filter(Employee.email == email).first()
    if not user or not verify_password(password, user.login_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")
    return {"message": "Login successful", "emp_id": user.emp_id,"emp_name":user.name,"annual":user.annual_leave_days,"sick":user.sick_leave_days}
