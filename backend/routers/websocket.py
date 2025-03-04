from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from database import get_db
from models import LeaveRecord, Employee, EmployeeSupervisor
from utils import verify_access_token
from typing import Optional
from datetime import datetime
import re
import json
import holidays
import os

from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

router = APIRouter()

openapikey = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openapikey)

history = [
    {"role": "system",
     "content": "你是一個請假助理，負責提取用戶輸入中的請假信息（假別、起始日期時間和結束日期時間）,不可以代替用戶決定任何信息, 如果用反沒有提到, 就要問用戶,如果已有足夠的訊息,則輸出一個一個json格式, key 為 leave_type,start_datetime,end_datetime,如果用戶的輸入有缺少資訊,詢問用戶。"}
]

user_history = {}

user_confirm = {}


async def get_emp_id_from_token(websocket: WebSocket) -> Optional[str]:
    """从 WebSocket 请求头中提取并验证 JWT Token，获取 emp_id。"""
    try:
        token = websocket.headers.get("Authorization")
        if not token or not token.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
        token = token.split(" ")[1]
        payload = verify_access_token(token)
        if not payload or "emp_id" not in payload:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return payload["emp_id"]
    except Exception as e:
        print(f"Token verification failed: {e}")
        return None


def extract_emp_id(input_text: str) -> str:
    """
    使用正则表达式从输入字符串中提取 emp_id。
    """
    match = re.search(r"@@(.*?)@@", input_text)
    if match:
        return match.group(1)  # 提取匹配到的 emp_id
    return None


@router.websocket("/leave")
async def leave_websocket(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()

    # 验证并获取用户的 emp_id
    # emp_id = await get_emp_id_from_token(websocket)
    # if not emp_id:
    #     await websocket.close(code=1008)  # 关闭 WebSocket，提示用户认证失败
    #     return

    user_data = {}
    emp_id = None
    try:

        while True:
            user_input = await websocket.receive_text()
            emp_id = extract_emp_id(user_input)
            print(f"recv :{user_input}")

            reqlist = []
            if "***" in user_input:
                print("is ****")
                reqlist = get_pending_leave_requests(emp_id, db)
                if len(reqlist) > 0:
                    await websocket.send_text("下屬請假申請:")
                    response = await generate_subleave_summary(reqlist)
                    await websocket.send_text(response)
            else:
                print("normal query")
                if "查詢" in user_input and "請假" in user_input:
                    # 查询已请假记录
                    leave_records = query_leave_records(emp_id, db)
                    if not leave_records:
                        await websocket.send_text("您目前尚未有任何請假記錄。")
                    else:
                        # 使用 GPT 生成自然语言回复
                        response = await generate_leave_summary(leave_records)
                        await websocket.send_text(response)
                elif "確認" in user_input and "請假" in user_input:
                    if emp_id in user_confirm and len(user_confirm[emp_id]) > 0:
                        save_leave_record(user_confirm[emp_id], emp_id, db)
                        msg = generate_confirmation_message(user_confirm[emp_id])
                        await websocket.send_text(f"已提出請假申請\n {msg}")
                        user_confirm[emp_id] = {}
                    else:
                        await websocket.send_text("您目前尚無要確認的請假")
                elif "同意" in user_input and "請假" in user_input:
                    reqlist = get_pending_leave_requests(emp_id, db)
                    if len(reqlist) > 0:
                        msg = approve_all_leave_requests(emp_id, db)
                        await websocket.send_text(msg)
                else:
                    # 处理请假申请或其他逻辑
                    response = await process_leave_request(user_input, emp_id, db)
                    await websocket.send_text(response)

            # Process natural language with GPT
            # response = await process_with_gpt(data, user_data)
            # await websocket.send_text(response)
    except WebSocketDisconnect:
        if emp_id is not None:
            user_history[emp_id] = []  # clear old  record
        print("WebSocket disconnected")


async def process_with_gpt(input_text: str, user_data: dict) -> str:
    # openai.api_key = "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"
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "你是一個智能助手，請只使用繁體中文回答所有問題，不要使用其他語言."},
            {"role": "user", "content": input_text}
        ]
    )
    return response.choices[0].message.content.strip()


def approve_all_leave_requests(supervisor_id: str, db: Session):
    """
    批量批准该主管的所有待审批请假请求 (status="requested" -> "approved")
    """
    # 找出该主管管理的所有员工
    subordinates_query = select(EmployeeSupervisor.emp_id).filter(EmployeeSupervisor.supervisor_id == supervisor_id)

    # 直接批量更新数据库
    updated_rows = (
        db.query(LeaveRecord)
        .filter(and_(LeaveRecord.emp_id.in_(subordinates_query), LeaveRecord.status == "requested"))
        .update({"status": "approved"}, synchronize_session=False)
    )

    db.commit()

    return f"已核淮請假記錄"


def get_pending_leave_requests(supervisor_id: str, db: Session):
    """
    查询所有属于 supervisor_id 主管的员工，并且 status="requested" 的请假记录
    """
    # 找出该主管管理的所有员工
    subordinates_query = select(EmployeeSupervisor.emp_id).filter(EmployeeSupervisor.supervisor_id == supervisor_id)

    # 查询请假记录
    leave_requests = (
        db.query(LeaveRecord)
        .filter(and_(LeaveRecord.emp_id.in_(subordinates_query), LeaveRecord.status == "requested"))
        .all()
    )

    return leave_requests


# 查询数据库中的请假记录
def query_leave_records(emp_id: str, db: Session):
    return db.query(LeaveRecord).filter(LeaveRecord.emp_id == emp_id).all()


async def generate_subleave_summary(leave_records):
    leave_summary = [
        f"{record.emp_id} 請{record.leave_type}假，從 {record.start_datetime} 到 {record.end_datetime} 狀態 {record.status}"
        for record in leave_records
    ]
    records_text = "\n".join(leave_summary)

    records_text + "是否同意?"

    return records_text
    # 使用 GPT 将数据转换为自然语言
    '''
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system",
             "content": "你是一個請假記錄助手，負責根據用戶的下屬請假記錄生成表格摘要，詢問是否允許，並以自然語言返回。"},
            {"role": "assistant", "content": f"以下是用戶的的下屬請假記錄：\n{records_text}"},
        ]
    )

    return response.choices[0].message.content
    '''


# 使用 GPT 生成请假记录摘要
async def generate_leave_summary(leave_records):
    leave_summary = [
        f"{record.leave_type}假，從 {record.start_datetime} 到 {record.end_datetime} 狀態 {record.status}"
        for record in leave_records
    ]
    records_text = "\n".join(leave_summary)

    # 使用 GPT 将数据转换为自然语言
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "你是一個請假記錄助手，負責根據用戶的請假記錄生成表格摘要，並以自然語言返回。"},
            {"role": "assistant", "content": f"以下是用戶的請假記錄：\n{records_text}"},
        ]
    )

    return response.choices[0].message.content


# 处理请假申请
async def process_leave_request(user_input: str, emp_id: str, db: Session):
    his = []
    if emp_id in user_history:
        his = user_history[emp_id]
    else:
        user_history[emp_id] = his

    if len(his) == 0:
        his.append(history[0])

    extracted_data = await extract_leave_info(user_input, his)
    missing_fields = check_missing_fields(extracted_data)

    if missing_fields:
        return extracted_data  # f"缺少以下資訊：{', '.join(missing_fields)}，請補充。"
    else:
        error_msg = check_error(extracted_data)

        if len(error_msg) == 0:
            confirmation_message = generate_confirmation_message(extracted_data)
            user_confirm[emp_id] = extracted_data
            # save_leave_record(extracted_data, emp_id, db)  # 保存记录
            return f"請假資訊確認：\n{confirmation_message}, 如果資訊正確, 請回覆確認請假,提出請假申請"
        else:
            return error_msg


# 提取请假信息（保持不变）
async def extract_leave_info(user_input: str, his):
    his.append({"role": "user", "content": user_input})
    print(his)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=his
        # [
        #     {"role": "system", "content": "你是一個請假助理，負責提取用戶輸入中的請假信息（假別、起始日期時間和結束日期時間）,如果已有足夠的訊息,則輸出一個json格式, key 為 leave_type,start_datetime,end_datetime,如果用戶的輸入有缺少資訊,詢問用戶。"},
        #     {"role": "user", "content": user_input}
        # ]
    )
    extracted_info = response.choices[0].message.content

    his.append({"role": "assistant", "content": extracted_info})

    print(extracted_info)
    return parse_extracted_info(extracted_info)


# 检查缺失字段（保持不变）
def check_missing_fields(data: dict):
    required_fields = ["leave_type", "start_datetime", "end_datetime"]
    return [field for field in required_fields if field not in data or not data[field]]


def check_error(data: dict):
    try:
        st_dt = datetime.strptime(data["start_datetime"], "%Y-%m-%dT%H:%M:%S")
        ed_dt = datetime.strptime(data["end_datetime"], "%Y-%m-%dT%H:%M:%S")

        if st_dt > ed_dt:
            return f"請假開始時間必須早於結束時間"

        current_date = st_dt

        tw_holidays = holidays.Taiwan()

        while current_date <= ed_dt:
            if current_date.weekday() in [5, 6]:  # 週六 = 5, 週日 = 6
                return {"error": f"請假區間內包含週末 ({current_date})，請確認"}
            if current_date in tw_holidays:
                return {"error": f"請假區間內包含國定假日 ({current_date}: {tw_holidays[current_date]})，請確認"}
            current_date += datetime.timedelta(days=1)


    except ValueError:
        return f"日期格式錯誤，請使用 YYYY-MM-DDTHH:MM:SS 格式"
    return ""


def parse_extracted_info(extracted_info: str) -> dict:
    """
    将 GPT 的输出解析为 Python 字典。
    假设返回格式为 JSON。
    """
    try:
        return json.loads(extracted_info)
    except json.JSONDecodeError as e:
        print(f"解析失敗: {e}")
        return extracted_info


# 生成确认消息（保持不变）
def generate_confirmation_message(data: dict):
    return (f"假別：{data['leave_type']}\n"
            f"起始時間：{data['start_datetime']}\n"
            f"結束時間：{data['end_datetime']}")


# 保存记录到数据库
def save_leave_record(data: dict, emp_id: str, db: Session):
    # 获取员工信息
    employee = db.query(Employee).filter(Employee.emp_id == emp_id).first()
    # 解析时间
    start_datetime = datetime.strptime(data["start_datetime"], "%Y-%m-%dT%H:%M:%S")
    end_datetime = datetime.strptime(data["end_datetime"], "%Y-%m-%dT%H:%M:%S")

    # 获取员工的上下班时间
    work_start_time = datetime.strptime(employee.work_start_time, "%H:%M").time()
    work_end_time = datetime.strptime(employee.work_end_time, "%H:%M").time()

    leave_records = []  # 存储拆分后的请假记录

    current_date = start_datetime.date()  # 当前处理日期
    day_start = start_datetime
    while True:
        # 计算当天的工作开始、结束时间
        day_end = datetime.combine(current_date, work_end_time)

        # 如果 start_datetime 在 work_end_time 之后，跳到下一天
        if start_datetime > day_end:
            current_date += timedelta(days=1)
            continue

        # 计算当天的请假时间
        leave_start = start_datetime
        leave_end = min(day_end, end_datetime)  # 取较早者

        # 创建请假记录
        leave_records.append(LeaveRecord(
            emp_id=emp_id,
            leave_type=data["leave_type"],
            start_datetime=leave_start,
            end_datetime=leave_end,
            status="requested",
            note=data.get("note", ""),
        ))

        # 结束条件
        if leave_end == end_datetime:
            break

        # 进入下一天
        current_date += timedelta(days=1)
        start_datetime = datetime.combine(current_date, work_start_time)  # 设定新的一天的开始时间

    # 批量插入数据库
    db.add_all(leave_records)
    db.commit()

    print("請假記錄拆分成功")

    '''
    record = LeaveRecord(
        emp_id=emp_id,
        leave_type=data["leave_type"],
        start_datetime=data["start_datetime"],
        end_datetime=data["end_datetime"],
        status="requested",
        note=data.get("note", ""),
    )
    db.add(record)
    db.commit()
    '''
