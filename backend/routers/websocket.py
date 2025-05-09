from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, select
from database import get_db
from models import LeaveRecord, Employee, EmployeeSupervisor
from utils import verify_access_token
from typing import Optional
import re
import json
import holidays
import os

from dotenv import load_dotenv
from datetime import datetime, timedelta
import logging

load_dotenv()

router = APIRouter()

openapikey = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=openapikey)

history = [
    {"role": "system",
     "content": """你是一個請假助理，負責從用戶輸入中提取請假資訊，包括：
- 假別（leave_type）
- 起始日期時間（start_datetime）
- 結束日期時間（end_datetime）

請遵守以下規則：
1. 將用戶輸入中的相對時間（如「明天下午」）轉換為具體的日期時間（格式為：YYYY-MM-DD HH:mm）。
2. 如果資訊不完整（例如未提及假別、起始或結束時間），請向用戶詢問缺少的項目。
3. 如果資訊齊全，請只輸出一個標準 JSON 格式字串，鍵為 `leave_type`, `start_datetime`, `end_datetime`，**不要加上任何其它文字、說明、或程式碼標記（例如```json）**。
4. 請不要自行假設或決定任何用戶未提及的資訊。

現在開始處理用戶的輸入。
"""
     }
]

user_history = {}

user_confirm = {}

logger = logging.getLogger("uvicorn")


def generate_time_prompt():
    today = datetime.today()
    weekday = today.weekday()  # 0 = Monday, 4 = Friday

    # 计算相对时间
    date_mappings = {
        "今天": today.strftime("%Y-%m-%d"),
        "明天": (today + timedelta(days=1)).strftime("%Y-%m-%d"),
        "後天": (today + timedelta(days=2)).strftime("%Y-%m-%d"),
        "這周五": (today + timedelta(days=(4 - weekday) if weekday <= 4 else (4 - weekday + 7))).strftime("%Y-%m-%d")
    }

    # 生成提示文本
    prompt = f"今天是 {date_mappings['今天']}，星期{['一', '二', '三', '四', '五', '六', '日'][weekday]}。\n"
    prompt += "請基於當前時間解析以下自然語言的日期：\n"
    for key, value in date_mappings.items():
        prompt += f"- \"{key}\" = {value}\n"
    prompt += "如果遇到類似的時間表達方式, 請進行同樣的轉換,並在後續回答中使用解析後的日期"

    return prompt


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
                logger.info("=>下屬請假查詢")
                reqlist = get_pending_leave_requests(emp_id, db)
                if len(reqlist) > 0:
                    await websocket.send_text("下屬請假申請:")
                    response = await generate_subleave_summary(reqlist)
                    await websocket.send_text(response)
            else:
                print("normal query")
                if "查詢" in user_input and "請假" in user_input:
                    logger.info("=>查詢請假")
                    # 查询已请假记录
                    leave_records = query_leave_records(emp_id, db)
                    if not leave_records:
                        await websocket.send_text("您目前尚未有任何請假記錄。")
                    else:
                        # 使用 GPT 生成自然语言回复
                        response = await generate_leave_summary(leave_records)
                        await websocket.send_text(response)
                elif "確認" in user_input and "請假" in user_input:
                    logger.info("=>確認請假")
                    if emp_id in user_confirm and len(user_confirm[emp_id]) > 0:
                        save_leave_record(user_confirm[emp_id], emp_id, db)
                        msg = generate_confirmation_message(user_confirm[emp_id])
                        await websocket.send_text(f"已提出請假申請\n {msg}")
                        user_confirm[emp_id] = {}
                        user_history[emp_id] = []  # clear old  record
                    else:
                        await websocket.send_text("您目前尚無要確認的請假")
                elif "同意" in user_input and "請假" in user_input:
                    logger.info("=>同意請假")
                    reqlist = get_pending_leave_requests(emp_id, db)
                    if len(reqlist) > 0:
                        msg = approve_all_leave_requests(emp_id, db)
                        await websocket.send_text(msg)
                elif "取消" in user_input and "請假" in user_input:
                    logger.info("=>取消請假")
                    leave_records = query_leave_records(emp_id, db)
                    if not leave_records:
                        await websocket.send_text("您目前尚未有任何請假記錄。")
                    else:
                        # 使用 GPT 生成自然语言回复
                        response = await generate_leave_summary(leave_records)
                        await websocket.send_text("要取消那一筆?" + response)
                else:
                    logger.info("=>處理請假")
                    # 处理请假申请或其他逻辑
                    response = await process_leave_request(user_input, emp_id, db)
                    print(f"get response {response}")
                    await websocket.send_text(str(response))

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


def check_leave_exists(db: Session, emp_id: str, leave_date: datetime):
    """
    检查员工是否在指定日期已有请假记录
    """
    # 获取该日期的 00:00:00 和 23:59:59
    day_start = datetime(leave_date.year, leave_date.month, leave_date.day, 0, 0, 0)
    day_end = datetime(leave_date.year, leave_date.month, leave_date.day, 23, 59, 59)

    # 查询是否已有当天的请假记录
    existing_leave = db.query(LeaveRecord).filter(
        LeaveRecord.emp_id == emp_id,
        LeaveRecord.status.in_(["requested", "approved"]),  # 只检查已申请或已批准的
        or_(
            and_(LeaveRecord.start_datetime >= day_start, LeaveRecord.start_datetime <= day_end),
            and_(LeaveRecord.end_datetime >= day_start, LeaveRecord.end_datetime <= day_end),
            and_(LeaveRecord.start_datetime <= day_start, LeaveRecord.end_datetime >= day_end)  # 覆盖整天的情况
        )
    ).first()

    return existing_leave is not None  # 返回 True 表示已有请假记录，False 表示没有


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
    print(f"get {extracted_data}")
    missing_fields = check_missing_fields(extracted_data)
    print(f"miss fields :{missing_fields}")
    logger.info(f"請假欄位處理:{extracted_data}")

    logger.info(f"缺少欄位:{missing_fields}")

    if missing_fields:
        return extracted_data  # f"缺少以下資訊：{', '.join(missing_fields)}，請補充。"
    else:
        print("start to check error")
        error_msg = check_error(extracted_data, emp_id, db)
        print(f"error message {error_msg}")

        if len(error_msg) == 0:
            confirmation_message = generate_confirmation_message(extracted_data)
            user_confirm[emp_id] = extracted_data
            # save_leave_record(extracted_data, emp_id, db)  # 保存记录
            return f"請假資訊確認：\n{confirmation_message}, 如果資訊正確, 請回覆確認請假,提出請假申請"
        else:
            try:
                return json.loads(error_msg)["error"]
            except Exception:
                return error_msg


# 提取请假信息（保持不变）
async def extract_leave_info(user_input: str, his):
    his.append({"role": "user", "content": user_input})
    time_prompt = generate_time_prompt()
    his.append({"role": "system", "content": time_prompt})
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

    logger.info(f"助理回復:{extracted_info}")
    print(extracted_info)
    return parse_extracted_info(extracted_info)


# 检查缺失字段（保持不变）
def check_missing_fields(data: dict):
    try:
        required_fields = ["leave_type", "start_datetime", "end_datetime"]
        return [field for field in required_fields if field not in data or not data[field]]
    except Exception:
        return f"資訊不足"


def check_error(data: dict, emp_id: str, db: Session):
    try:

        logger.info(f"檢查錯誤:{data}")

        print(f"start to check {data}")

        data["start_datetime"] = data["start_datetime"].replace("/", "-")
        data["end_datetime"] = data["end_datetime"].replace("/", "-")

        st_dt = datetime.strptime(data["start_datetime"], "%Y-%m-%d %H:%M")
        ed_dt = datetime.strptime(data["end_datetime"], "%Y-%m-%d %H:%M")

        print(f"get datetime")
        if st_dt > ed_dt:
            return f"請假開始時間必須早於結束時間"

        if check_leave_exists(db, emp_id, st_dt):
            return f"{data['start_datetime']}已請假,請先取消或檢查請假日期"
        if check_leave_exists(db, emp_id, ed_dt):
            return f"{data['end_datetime']}已請假,請先取消或檢查請假日期"

        print(f"check weekday and holiday")

        current_date = st_dt

        tw_holidays = holidays.Taiwan()

        while current_date <= ed_dt:
            if current_date.weekday() in [5, 6]:  # 週六 = 5, 週日 = 6
                return {"error": f"請假區間內包含週末 ({current_date})，請確認"}
            if current_date in tw_holidays:
                return {"error": f"請假區間內包含國定假日 ({current_date}: {tw_holidays[current_date]})，請確認"}
            current_date = current_date + timedelta(days=1)


    except ValueError:
        return f"日期格式錯誤，請使用 YYYY-MM-DD HH:MM 格式"
    except Exception:
        return f"輸入有錯,請重新輸入"
    return ""


def parse_extracted_info(extracted_info: str) -> dict:
    """
    将 GPT 的输出解析为 Python 字典。
    假设返回格式为 JSON。
    """
    extracted_info = extracted_info.replace("```json", "").replace("```", "")
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

    data["start_datetime"] = data["start_datetime"].replace("/", "-")
    data["end_datetime"] = data["end_datetime"].replace("/", "-")

    # 解析时间
    start_datetime = datetime.strptime(data["start_datetime"], "%Y-%m-%d %H:%M")
    end_datetime = datetime.strptime(data["end_datetime"], "%Y-%m-%d %H:%M")

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
        current_date = current_date + timedelta(days=1)
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
