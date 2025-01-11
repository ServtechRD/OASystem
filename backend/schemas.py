from pydantic import BaseModel, EmailStr,Field
from datetime import datetime, time




from pydantic import BaseModel
from typing import Optional,List



class ChangePasswordRequest(BaseModel):
    emp_id: str = Field(..., example="E001")
    old_password: str = Field(..., example="current_password")
    new_password: str = Field(..., example="new_password")



# 员工基础模型
class EmployeeBase(BaseModel):
    emp_id: str
    name: str
    position: Optional[str]
    specialty: Optional[str]
    description: Optional[str]
    phone: Optional[str]
    email: str
    login_account: Optional[str]
    work_start_time: Optional[str] = Field("09:00", example="09:00")
    work_end_time: Optional[str] = Field("18:30", example="18:30")
    annual_leave_days: Optional[int] = Field(0, example=12)
    sick_leave_days: Optional[int] = Field(0, example=14)



# 创建员工模型
class EmployeeCreate(EmployeeBase):
    login_password: str

# 更新员工模型
class EmployeeUpdate(BaseModel):
    name: Optional[str]
    position: Optional[str]
    specialty: Optional[str]
    description: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    login_account: Optional[str]


    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None
    annual_leave_days: Optional[int] = None
    sick_leave_days: Optional[int] = None



# 员工响应模型
class EmployeeResponse(EmployeeBase):
    id: int

    class Config:
        orm_mode = True

# 主管关系模型
class EmployeeSupervisorBase(BaseModel):
    emp_id: str
    supervisor_id: str

# 创建主管关系
class EmployeeSupervisorCreate(EmployeeSupervisorBase):
    pass

# 主管关系响应
class EmployeeSupervisorResponse(EmployeeSupervisorBase):
    id: int

    class Config:
        orm_mode = True




# 假数基础模型
class LeaveEntitlementBase(BaseModel):
    emp_id: str
    leave_type: str
    entitlement_days: int = 0

# 创建假数模型
class LeaveEntitlementCreate(LeaveEntitlementBase):
    pass

# 更新假数模型
class LeaveEntitlementUpdate(BaseModel):
    leave_type: Optional[str]
    entitlement_days: Optional[int]

# 假数响应模型
class LeaveEntitlementResponse(LeaveEntitlementBase):
    id: int

    class Config:
        orm_mode = True



# 请假记录模型
class LeaveRequest(BaseModel):
    emp_id: str
    leave_type: str
    start_datetime: datetime
    end_datetime: datetime
    note: str = None

class LeaveResponse(BaseModel):
    id: int
    emp_id: str
    leave_type: str
    start_datetime: datetime
    end_datetime: datetime
    status: str
    note: str = None

    class Config:
        orm_mode = True

# 上下班时间模型
class WorkScheduleBase(BaseModel):
    emp_id: str
    start_time: time
    end_time: time

class WorkScheduleCreate(WorkScheduleBase):
    pass

class WorkScheduleResponse(WorkScheduleBase):
    id: int

    class Config:
        orm_mode = True

