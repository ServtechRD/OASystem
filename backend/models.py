from sqlalchemy import Column, Integer, String, Enum, ForeignKey, Date, DateTime, Time, Text, DECIMAL
from sqlalchemy.orm import relationship

from database import Base

class Employee(Base):
    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(20), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    position = Column(String(50))
    specialty = Column(String(100))
    description = Column(Text)
    phone = Column(String(15))
    email = Column(String(50), unique=True, nullable=False)
    login_account = Column(String(50), default=None)
    login_password = Column(String(100), nullable=False)

    # 新增字段
    work_start_time = Column(String(5), default="09:30")  # 上班时间
    work_end_time = Column(String(5), default="18:30")    # 下班时间
    annual_leave_days = Column(Integer, default=0)        # 每年特休天数
    sick_leave_days = Column(Integer, default=0)          # 每年病假天数    





class EmployeeSupervisor(Base):
    __tablename__ = "employee_supervisors"
    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(20), ForeignKey("employees.emp_id"), nullable=False)
    supervisor_id = Column(String(20), ForeignKey("employees.emp_id"), nullable=False)

class LeaveRecord(Base):
    __tablename__ = "leave_records"
    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(20), ForeignKey("employees.emp_id"), nullable=False)
    #leave_type = Column(Enum("annual", "sick", "personal", "marriage", "other"), nullable=False)
    leave_type = Column(String(50),nullable=False)
    start_datetime = Column(DateTime, nullable=False)
    end_datetime = Column(DateTime, nullable=False)
    status = Column(Enum("draft","requested", "approved", "cancelled","deleted"), default="draft")
    note = Column(Text)
    total_hours = Column(DECIMAL(5, 2), default=0)  # 实际请假小时数（新增字段）

class WorkSchedule(Base):
    __tablename__ = "work_schedules"
    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(20), ForeignKey("employees.emp_id"), nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

class LeaveEntitlement(Base):
    __tablename__ = "leave_entitlements"
    id = Column(Integer, primary_key=True, index=True)
    emp_id = Column(String(20), ForeignKey("employees.emp_id"), nullable=False)
    #leave_type = Column(Enum("annual", "sick", "personal", "marriage", "other"), nullable=False)
    leave_type = Column(String(50) , nullable = False)
    entitlement_days = Column(Integer, default=0)



class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(Integer, primary_key=True, autoincrement=True)
    holiday_date = Column(Date, nullable=False, unique=True)  # 假日日期
    description = Column(String(255), nullable=False)  # 假日描述
