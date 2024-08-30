# script/CollectTheSun/main.py

import logging
import os
import sys

import datetime
import random
import sqlite3

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

DB_PATH = os.path.join(DATA_DIR, "collect_the_sun.db")


# 查看功能开关状态
def load_function_status(group_id):
    return load_switch(group_id, "function_status")


# 保存功能开关状态
def save_function_status(group_id, status):
    save_switch(group_id, "function_status", status)


# 初始化数据库
def init_database():
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS collect_the_sun (
                group_id TEXT NOT NULL,
                user_id TEXT NOT NULL,
                sun_count INTEGER NOT NULL DEFAULT 0,
                rain_count INTEGER NOT NULL DEFAULT 0,
                UNIQUE(user_id, group_id)
            )
        """
        )
        conn.commit()
        conn.close()
        logging.info(f"初始化CollectTheSun数据库成功")


# 读取用户在某群收集的阳光
def load_user_sun(group_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sun_count FROM collect_the_sun WHERE group_id = ? AND user_id = ?",
        (group_id, user_id),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


# 读取用户在某群收集的雨水
def load_user_rain(group_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT rain_count FROM collect_the_sun WHERE group_id = ? AND user_id = ?",
        (group_id, user_id),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0


# 读取用户所有群的阳光，求和
def load_user_all_sun(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sun_count FROM collect_the_sun WHERE user_id = ?",
        (user_id,),
    )
    result = cursor.fetchall()
    conn.close()
    return sum(result[0] for result in result)


# 读取用户所有群的雨水，求和
def load_user_all_rain(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT rain_count FROM collect_the_sun WHERE user_id = ?",
        (user_id,),
    )
    result = cursor.fetchall()
    conn.close()
    return sum(result[0] for result in result)


# 读取本群所有阳光，求和
def load_group_all_sun(group_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sun_count FROM collect_the_sun WHERE group_id = ?",
        (group_id,),
    )
    result = cursor.fetchall()
    conn.close()
    return sum(result[0] for result in result)


# 读取本群所有雨水，求和
def load_group_all_rain(group_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT rain_count FROM collect_the_sun WHERE group_id = ?",
        (group_id,),
    )
    result = cursor.fetchall()
    conn.close()
    return sum(result[0] for result in result)


# 读取全服所有阳光，求和
def load_all_sun():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sun_count FROM collect_the_sun",
    )
    result = cursor.fetchall()
    conn.close()
    return sum(result[0] for result in result)


# 读取全服所有雨水，求和
def load_all_rain():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT rain_count FROM collect_the_sun",
    )
    result = cursor.fetchall()
    conn.close()
    return sum(result[0] for result in result)


# 更新用户在某群的阳光
def update_sun(group_id, user_id, sun_count):
    current_sun_count = load_user_sun(group_id, user_id)
    current_rain_count = load_user_rain(group_id, user_id)  # 获取当前雨水数量
    total_sun_count = current_sun_count + sun_count
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO collect_the_sun (group_id, user_id, sun_count, rain_count) VALUES (?, ?, ?, ?)",
        (group_id, user_id, total_sun_count, current_rain_count),  # 保持雨水数量不变
    )
    conn.commit()
    conn.close()


# 更新用户在某群的雨水
def update_rain(group_id, user_id, rain_count):
    current_rain_count = load_user_rain(group_id, user_id)
    current_sun_count = load_user_sun(group_id, user_id)  # 获取当前阳光数量
    total_rain_count = current_rain_count + rain_count
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO collect_the_sun (group_id, user_id, sun_count, rain_count) VALUES (?, ?, ?, ?)",
        (group_id, user_id, current_sun_count, total_rain_count),  # 保持阳光数量不变
    )
    conn.commit()
    conn.close()


# 菜单
async def sun_menu(websocket, group_id, message_id):
    content = f"""[CQ:reply,id={message_id}]收集阳光指令列表：
收集阳光：收集阳光 或 sun
呼风唤雨：呼风唤雨 或 rain
查看信息：查看信息 或 info
阳光排行榜：阳光排行榜 或 rank"""
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

    sun_count = random.randint(1, 50)
    update_sun(group_id, user_id, sun_count)
    await send_group_msg(
        websocket,
        group_id,
        f"[CQ:reply,id={message_id}]本次收集了{sun_count}个阳光，祝24级新生军训愉快！\n"
        f"——————————\n"
        f"发送“info”查看信息，发送“rank”查看阳光排行榜，发送“sunmenu”查看所有命令",
    )


# 呼风唤雨，随机减少阳光
async def call_rain(websocket, group_id, user_id, message_id):

    # 检测日期
    if datetime.datetime.now() > datetime.datetime(2024, 9, 14):
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]军训已结束，不用再呼风唤雨了",
        )
        return

    rain_count = random.randint(1, 50)
    update_rain(group_id, user_id, rain_count)
    await send_group_msg(
        websocket,
        group_id,
        f"[CQ:reply,id={message_id}]本次呼风唤雨了{rain_count}个雨水，祝24级新生军训愉快！\n"
        f"——————————\n"
        f"发送“suninfo”查看信息，发送“sunrank”查看阳光排行榜，发送“sunmenu”查看所有命令",
    )


# 查看信息
async def check_info(websocket, group_id, user_id, message_id):
    content = (
        f"[CQ:reply,id={message_id}]"
        f"你在本群收集阳光：{load_user_sun(group_id, user_id)}个，收集雨水：{load_user_rain(group_id, user_id)}个\n"
        f"你共收集阳光：{load_user_all_sun(user_id)}个，收集雨水：{load_user_all_rain(user_id)}个\n"
        f"本群总收集阳光：{load_group_all_sun(group_id)}个，收集雨水：{load_group_all_rain(group_id)}个\n"
        f"全服总收集阳光：{load_all_sun()}个，收集雨水：{load_all_rain()}个"
    )
    await send_group_msg(websocket, group_id, content)


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

        # 检测日期，军训已结束，不用再收集阳光了
        if datetime.datetime.now() > datetime.datetime(2024, 9, 14):
            return

        # 菜单
        if raw_message == "sunmenu":
            await sun_menu(websocket, group_id, message_id)
            return

        if raw_message == "收集阳光" or raw_message == "sun":
            await collect_sun(websocket, group_id, user_id, message_id)
            return

        if raw_message == "呼风唤雨" or raw_message == "rain":
            await call_rain(websocket, group_id, user_id, message_id)
            return

        if raw_message == "查看信息" or raw_message == "suninfo":
            await check_info(websocket, group_id, user_id, message_id)
            return

        if raw_message == "阳光排行榜" or raw_message == "sunrank":
            await sun_rank(websocket, group_id, user_id, message_id)
            return

    except Exception as e:
        logging.error(f"处理CollectTheSun群消息失败: {e}")
        return
