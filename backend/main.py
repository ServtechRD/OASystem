from fastapi import FastAPI


from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import auth, leave, websocket, employee , leave_entitlements


# 创建数据库表
Base.metadata.create_all(bind=engine)

# 创建 FastAPI 应用
app = FastAPI(
    title="OA System",
    description="A system to manage employee leaves and work schedules",
    version="1.0.0"
)


# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 根据需要配置来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 注册路由
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(leave.router, prefix="/leave", tags=["Leave Management"])
app.include_router(websocket.router, prefix="/ws", tags=["WebSocket"])
app.include_router(employee.router, prefix="/base", tags=["Employee"])
app.include_router(leave_entitlements.router, prefix="/base", tags=["Leave-Entitlements"])
