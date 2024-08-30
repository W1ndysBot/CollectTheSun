# script/CollectTheSun/main.py

import logging
import os
import sys
import asyncio
import datetime


# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import owner_id
from app.api import *
from app.switch import load_switch, save_switch

# 数据存储路径，实际开发时，请将CollectTheSun替换为具体的数据存放路径
DATA_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "CollectTheSun",
)


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "function_status")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "function_status", status)


# 初始化数据库
def init_database():
    pass


# 菜单
async def sun_menu(websocket, group_id, user_id, message_id):
    content = f"""[CQ:reply,id={message_id}]收集阳光指令列表：
收集阳光：收集阳光 或 collectsun
查看阳光：查看阳光 或 checksun
阳光排行榜：阳光排行榜 或 sunrank
"""
    await send_group_msg(websocket, group_id, content)


# 随机收集阳光
async def collect_sun(websocket, group_id, user_id, message_id):

    # 检测日期
    if datetime.datetime.now() > datetime.datetime(2024, 9, 14):
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]军训已结束，不用再收集阳光了",
        )
        return


# 查看阳光
async def check_sun(websocket, group_id, user_id, message_id):
    pass


# 阳光排行榜
async def sun_rank(websocket, group_id, user_id, message_id):
    pass


# 群消息处理函数
async def handle_CollectTheSun_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        role = str(msg.get("sender", {}).get("role"))
        message_id = str(msg.get("message_id"))

        # 初始化数据库
        init_database()

        # 检测日期
        if datetime.datetime.now() > datetime.datetime(2024, 9, 14):

            logging.info(f"军训已结束，不用再收集阳光了")
            return

        # 菜单
        if raw_message == "sunmenu":
            await sun_menu(websocket, group_id, user_id, message_id)

        if raw_message == "收集阳光" or raw_message == "collectsun":
            await collect_sun(websocket, group_id, user_id, message_id)

        if raw_message == "查看阳光" or raw_message == "checksun":
            await check_sun(websocket, group_id, user_id, message_id)

        if raw_message == "阳光排行榜" or raw_message == "sunrank":
            await sun_rank(websocket, group_id, user_id, message_id)

    except Exception as e:
        logging.error(f"处理CollectTheSun群消息失败: {e}")
        return
