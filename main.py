# script/CollectTheSun/main.py

import logging
import os
import sys
import re

import datetime
import random
import sqlite3
import math  # 添加此行以引入math模块

# 添加项目根目录到sys.path
sys.path.append(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

from app.config import owner_id
from app.api import *
from app.switch import load_switch, save_switch


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
                time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_join BOOLEAN NOT NULL DEFAULT FALSE,
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


# 读取上次sun或rain操作时间
def load_user_last_operation_time(group_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT time FROM collect_the_sun WHERE group_id = ? AND user_id = ?",
        (group_id, user_id),
    )
    result = cursor.fetchone()
    conn.close()
    if result:
        return datetime.datetime.strptime(result[0], "%Y-%m-%d %H:%M:%S")
    return datetime.datetime(1970, 1, 1, 0, 0, 0)


# 读取奇遇状态
def load_user_join_event(group_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT is_join FROM collect_the_sun WHERE group_id = ? AND user_id = ?",
        (group_id, user_id),
    )
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else False


# 读取用户所有群的阳光,求和
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


# 判断是否在冷却
def is_in_cd(group_id, user_id):
    time = datetime.datetime.now().replace(microsecond=0)
    current_time = load_user_last_operation_time(group_id, user_id)
    if current_time is None or (time - current_time).seconds > 60:
        return False
    return True


# 读取用户所有群的雨水,求和
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


# 读取本群所有阳光,求和
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


# 读取本群所有雨水,求和
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


# 读取全服所有阳光,求和
def load_all_sun():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT sun_count FROM collect_the_sun",
    )
    result = cursor.fetchall()
    conn.close()
    return sum(result[0] for result in result)


# 读取全服所有雨水,求和
def load_all_rain():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT rain_count FROM collect_the_sun",
    )
    result = cursor.fetchall()
    conn.close()
    return sum(result[0] for result in result)


# 更新CD（操作时间）
def update_cd(group_id, user_id):
    time = datetime.datetime.now().replace(microsecond=0)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM collect_the_sun WHERE group_id = ? AND user_id = ?",
        (group_id, user_id),
    )
    if cursor.fetchone() is None:
        cursor.execute(
            "INSERT INTO collect_the_sun (group_id, user_id, time) VALUES (?, ?, ?)",
            (group_id, user_id, time),
        )
    else:
        cursor.execute(
            "SELECT 1 FROM collect_the_sun WHERE group_id = ? AND user_id = ?",
            (group_id, user_id),
        )
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO collect_the_sun (group_id, user_id, time) VALUES (?, ?, ?)",
                (group_id, user_id, time),
            )
        else:
            cursor.execute(
                "UPDATE collect_the_sun SET time = ? WHERE group_id = ? AND user_id = ?",
                (time, group_id, user_id),
            )
    logging.info(f"更新用户{user_id}在群{group_id}的CD:{time}")
    conn.commit()
    conn.close()


# 更新用户在某群的阳光
def update_sun(group_id, user_id, sun_count):
    current_sun_count = load_user_sun(group_id, user_id)  # 获取当前阳光数量
    total_sun_count = max(0, current_sun_count + sun_count)  # 确保阳光数量不为负数
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT 1 FROM collect_the_sun WHERE group_id = ? AND user_id = ?",
        (group_id, user_id),
    )
    if cursor.fetchone() is None:
        cursor.execute(
            "SELECT 1 FROM collect_the_sun WHERE group_id = ? AND user_id = ?",
            (group_id, user_id),
        )
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO collect_the_sun (group_id, user_id, sun_count) VALUES (?, ?, ?)",
                (group_id, user_id, total_sun_count),
            )
        else:
            cursor.execute(
                "UPDATE collect_the_sun SET sun_count = ? WHERE group_id = ? AND user_id = ?",
                (total_sun_count, group_id, user_id),
            )
    logging.info(f"更新用户{user_id}在群{group_id}的阳光:{total_sun_count}")
    conn.commit()
    conn.close()
    return True


# 更新用户在某群的雨水
def update_rain(group_id, user_id, rain_count):
    current_rain_count = load_user_rain(group_id, user_id)  # 获取当前雨水数量
    total_rain_count = max(0, current_rain_count + rain_count)  # 确保雨水数量不为负数
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE collect_the_sun SET rain_count = ? WHERE group_id = ? AND user_id = ?",
        (
            total_rain_count,
            group_id,
            user_id,
        ),
    )
    conn.commit()
    conn.close()
    return True


# 加入奇遇
def join_event(group_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE collect_the_sun SET is_join = ? WHERE group_id = ? AND user_id = ?",
        (True, group_id, user_id),
    )
    conn.commit()
    conn.close()
    return True


# 退出奇遇
def quit_event(group_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE collect_the_sun SET is_join = ? WHERE group_id = ? AND user_id = ?",
        (False, group_id, user_id),
    )
    conn.commit()
    conn.close()
    return True


# 菜单
async def sun_menu(websocket, group_id, message_id):
    content = f"""[CQ:reply,id={message_id}]

收集阳光指令列表:
收集阳光:收集阳光 或 sun
收集雨水:收集雨水 或 rain
查看信息:查看信息 或 suninfo
加入奇遇:加入奇遇 或 sunjoin
退出奇遇:退出奇遇 或 sunquit
阳光榜:阳光榜 或 sunrank
雨水榜:雨水榜 或 rainrank
偷阳光:偷阳光 或 stealsun@
偷雨水:偷雨水 或 stealrain@
送阳光:送阳光 或 givesun@赠送量
送雨水:送雨水 或 giverain@赠送量
想加新玩法或建议或bug反馈
联系QQhttps://qm.qq.com/q/dJjlDIFJfM"""
    await send_group_msg(websocket, group_id, content)


# 随机收集阳光
async def collect_sun(websocket, group_id, user_id, message_id):
    # 检测日期
    if datetime.datetime.now() > datetime.datetime(2024, 9, 14):
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]军训已结束,不用再收集阳光了",
        )
        return

    current_sun_count = load_user_sun(group_id, user_id)
    chance = random.random()

    # 根据当前阳光数量使用不同的计算函数
    if chance < 0.15:  # 15% 概率大量收集
        sun_count = int(
            500 / (1 + math.log1p(current_sun_count)) * random.uniform(0.3, 0.5)
        ) + random.randint(1000, 5000)
        message = f"运气爆棚！大量收集了{sun_count}颗阳光"
    else:  # 85% 概率正常收集
        sun_count = int(
            200 / (1 + math.log1p(current_sun_count)) * random.uniform(0.1, 0.2)
        ) + random.randint(500, 2000)
        message = f"收集了{sun_count}颗阳光"
    if update_sun(group_id, user_id, sun_count):
        update_cd(group_id, user_id)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]{message},祝24级新生军训愉快(冷却60秒)！\n"
            f"——————————\n"
            f'发送"suninfo"查看信息,发送"sunrank"查看阳光排行榜,发送"sunmenu"查看所有命令',
        )


# 随机收集雨水
async def collect_rain(websocket, group_id, user_id, message_id):
    # 检测日期
    if datetime.datetime.now() > datetime.datetime(2024, 9, 14):
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]军训已结束,不用再呼风唤雨了",
        )
        return

    current_rain_count = load_user_rain(group_id, user_id)
    chance = random.random()

    # 根据当前雨水数量使用不同的计算函数
    if chance < 0.15:  # 15% 概率大量收集
        rain_count = int(
            500 / (1 + math.log1p(current_rain_count)) * random.uniform(0.3, 0.5)
        ) + random.randint(1000, 5000)
        message = f"运气爆棚！大量收集了{rain_count}滴雨水"
    else:  # 85% 概率正常收集
        rain_count = int(
            200 / (1 + math.log1p(current_rain_count)) * random.uniform(0.1, 0.2)
        ) + random.randint(500, 2000)
        message = f"收集了{rain_count}滴雨水"

    if update_rain(group_id, user_id, rain_count):
        update_cd(group_id, user_id)
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]{message},祝24级新生军训愉快(冷却60秒)！\n"
            f"——————————\n"
            f'发送"suninfo"查看信息,发送"sunrank"查看阳光排行榜,发送"sunmenu"查看所有命令',
        )


# 获取本群有效阳光前三的用户
def get_top_three_sun(group_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, (sun_count - rain_count) as effective_sun FROM collect_the_sun WHERE group_id = ? ORDER BY effective_sun DESC LIMIT 3",
        (group_id,),
    )
    result = cursor.fetchall()
    conn.close()
    return result


# 获取全服有效阳光前三的用户
def get_top_three_sun_all():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, (sun_count - rain_count) as effective_sun FROM collect_the_sun ORDER BY effective_sun DESC LIMIT 3",
    )
    result = cursor.fetchall()
    conn.close()
    return result


# 获取总阳光最多的前三个群
def get_top_three_group_sun():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT group_id, SUM(sun_count - rain_count) as effective_sun FROM collect_the_sun GROUP BY group_id ORDER BY effective_sun DESC LIMIT 3",
    )
    result = cursor.fetchall()
    conn.close()
    return result


# 获取本群雨水最多的前三个用户
def get_top_three_rain(group_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, rain_count FROM collect_the_sun WHERE group_id = ? ORDER BY rain_count DESC LIMIT 3",
        (group_id,),
    )
    result = cursor.fetchall()
    conn.close()
    return result


# 获取全服雨水最多的前三个用户
def get_top_three_rain_all():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT user_id, rain_count FROM collect_the_sun ORDER BY rain_count DESC LIMIT 3",
    )
    result = cursor.fetchall()
    conn.close()
    return result


# 获取总雨水最多的前三个群
def get_top_three_group_rain():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT group_id, SUM(rain_count) as total_rain FROM collect_the_sun GROUP BY group_id ORDER BY total_rain DESC LIMIT 3",
    )
    result = cursor.fetchall()
    conn.close()
    return result


# 查看信息
async def check_info(websocket, group_id, user_id, message_id):
    content = (
        f"[CQ:reply,id={message_id}]"
        f"[你在本群]\n"
        f"阳光:{load_user_sun(group_id, user_id)},雨水:{load_user_rain(group_id, user_id)},有效阳光:{load_user_sun(group_id, user_id) - load_user_rain(group_id, user_id)}\n"
        f"[你在全服]\n"
        f"阳光:{load_user_all_sun(user_id)},雨水:{load_user_all_rain(user_id)},有效阳光:{load_user_all_sun(user_id) - load_user_all_rain(user_id)}\n"
        f"[全服数据]\n"
        f"阳光:{load_all_sun()},雨水:{load_all_rain()},有效阳光:{load_all_sun() - load_all_rain()}"
    )
    await send_group_msg(websocket, group_id, content)


# 查看某用户信息
async def check_user_info(
    websocket,
    group_id,
    target_user_id,
    message_id,
):
    content = (
        f"[CQ:reply,id={message_id}]"
        f"[{target_user_id}在本群]\n"
        f"阳光:{load_user_sun(group_id, target_user_id)},雨水:{load_user_rain(group_id, target_user_id)},有效阳光:{load_user_sun(group_id, target_user_id) - load_user_rain(group_id, target_user_id)}\n"
        f"[{target_user_id}在全服]\n"
        f"阳光:{load_user_all_sun(target_user_id)},雨水:{load_user_all_rain(target_user_id)},有效阳光:{load_user_all_sun(target_user_id) - load_user_all_rain(target_user_id)}"
    )
    await send_group_msg(websocket, group_id, content)


# 阳光排行榜
async def sun_rank(websocket, group_id, message_id):
    logging.debug(f"群号:{group_id}")
    top_three_sun = get_top_three_sun(group_id)
    top_three_sun_all = get_top_three_sun_all()
    top_three_group_sun = get_top_three_group_sun()
    content = f"[CQ:reply,id={message_id}]"
    content += f"本群有效阳光前三的用户:\n"
    for rank, (user_id, sun_count) in enumerate(top_three_sun, 1):
        content += f"{rank}. <{user_id}>: {sun_count}阳光\n"
    logging.debug(f"群号:{group_id}")
    content += f"\n全服有效阳光前三的用户:\n"
    for rank, (user_id, sun_count) in enumerate(top_three_sun_all, 1):
        content += f"{rank}. <{user_id}>: {sun_count}阳光\n"
    logging.debug(f"群号:{group_id}")
    content += f"\n全服有效阳光前三的群:\n"
    for rank, (group_id_in_db, sun_count) in enumerate(top_three_group_sun, 1):
        content += f"{rank}. <{group_id_in_db}>: {sun_count}阳光\n"
    logging.debug(f"群号:{group_id}")
    await send_group_msg(websocket, group_id, content)


# 雨水排行榜
async def rain_rank(websocket, group_id, message_id):
    top_three_rain = get_top_three_rain(group_id)
    top_three_rain_all = get_top_three_rain_all()
    top_three_group_rain = get_top_three_group_rain()
    content = f"[CQ:reply,id={message_id}]"
    content += f"本群雨水前三的用户:\n"
    for rank, (user_id, rain_count) in enumerate(top_three_rain, 1):
        content += f"{rank}. <{user_id}>: {rain_count}雨水\n"
    content += f"\n全服雨水前三的用户:\n"
    for rank, (user_id, rain_count) in enumerate(top_three_rain_all, 1):
        content += f"{rank}. <{user_id}>: {rain_count}雨水\n"
    content += f"\n全服雨水最多的群:\n"
    for rank, (group_id_in_db, rain_count) in enumerate(top_three_group_rain, 1):
        content += f"{rank}. <{group_id_in_db}>: {rain_count}雨水\n"
    await send_group_msg(websocket, group_id, content)


# 每句话随机添加阳光
async def random_add(websocket, group_id, user_id, message_id):
    events = [
        "你在格物楼捡到了",
        "你在吱吱楼找到了",
        "你在文渊楼发现了",
        "你在操场上遇到了",
        "你在军训操场找到了",
        "你在综合楼里发现了",
        "你在宿舍楼捡到了",
        "你在图书馆里找到了",
        "你在体育馆里发现了",
        "你在食堂里找到了",
        "你在符文大陆找到了",
        "你在王者峡谷找到了",
        "你在蛋仔岛找到了",
        "你在平安京找到了",
        "你在提瓦特大陆找到了",
        "你在黑神话悟空找到了",
        "你在做俯卧撑时找到了",
        "你在罚站时找到了",
        "你在整理床铺时找到了",
        "你在瓦罗兰特找到了",
        "你在木叶村找到了",
        "你在西联找到了",
        "你在文史楼找到了",
        "你在绘素楼找到了",
        "你在背论语的时候找到了",
        "你在背单词的时候找到了",
        "你在背公式的时候找到了",
        "你在写代码找到了",
        "你在暴打W1ndys的时候找到了",
    ]

    # 检测是否在奇遇事件中
    if load_user_join_event(group_id, user_id):
        if random.random() < 0.05:
            sun_count = random.randint(500, 1000)
            event = random.choice(events)
            if random.random() < 0.5:  # 百分之五十的概率收集阳光
                if update_sun(group_id, user_id, sun_count):
                    await send_group_msg(
                        websocket,
                        group_id,
                        f"[CQ:reply,id={message_id}]{event}{sun_count}颗阳光,祝24级新生军训愉快(冷却60秒)！",
                    )
                    # logging.info(f"触发奇遇事件,{user_id}在{group_id}添加{sun_count}颗阳光")

            else:  # 百分之五十的概率收集雨水
                if update_rain(group_id, user_id, sun_count):
                    await send_group_msg(
                        websocket,
                        group_id,
                        f"[CQ:reply,id={message_id}]{event}{sun_count}滴雨水,祝24级新生军训愉快(冷却60秒)！",
                    )
                    # logging.info(f"触发奇遇事件,{user_id}在{group_id}添加{sun_count}滴雨水")


# 抢夺阳光
async def steal_sun(websocket, group_id, user_id, target_user_id, message_id):
    target_resource = load_user_sun(group_id, target_user_id)
    if not target_resource:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]目标用户不存在或没有资源",
        )
        return

    # 抢夺阳光的用户
    steal_sun_user = load_user_sun(group_id, user_id)
    # 抢夺的阳光数量
    steal_amount = int(target_resource * random.uniform(0.1, 0.3))
    # 损失的阳光数量
    lose_amount = int(steal_sun_user * random.uniform(0.1, 0.3))

    if random.random() < 0.5:  # 50% 成功率
        if update_sun(group_id, user_id, steal_amount) and update_sun(
            group_id, target_user_id, -lose_amount
        ):
            update_cd(group_id, user_id)
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]成功抢夺了{steal_amount}颗阳光(冷却60秒)",
            )
    else:
        if update_sun(group_id, user_id, -lose_amount):
            update_cd(group_id, user_id)
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]抢夺失败,损失了{lose_amount}颗阳光(冷却60秒)",
            )


# 抢夺雨水
async def steal_rain(websocket, group_id, user_id, target_user_id, message_id):

    target_resource = load_user_rain(group_id, target_user_id)
    if not target_resource:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]目标用户不存在或没有资源",
        )
        return

    # 抢夺雨水的用户
    steal_rain_user = load_user_rain(group_id, user_id)
    # 抢夺的雨水数量
    steal_amount = int(target_resource * random.uniform(0.1, 0.3))
    # 损失的雨水数量
    lose_amount = int(steal_rain_user * random.uniform(0.1, 0.3))

    if random.random() < 0.5:  # 50% 成功率
        if update_rain(group_id, user_id, steal_amount) and update_rain(
            group_id, target_user_id, -lose_amount
        ):
            update_cd(group_id, user_id)
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]成功抢夺了{steal_amount}滴雨水(冷却60秒)",
            )
    else:
        if update_rain(group_id, user_id, -lose_amount):
            update_cd(group_id, user_id)
            await send_group_msg(
                websocket,
                group_id,
                f"[CQ:reply,id={message_id}]抢夺失败,损失了{lose_amount}滴雨水(冷却60秒)",
            )


# 赠送阳光
async def give_sun(websocket, group_id, user_id, target_user_id, amount, message_id):
    user_sun = load_user_sun(group_id, user_id)
    if not user_sun or user_sun < amount:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]你没有足够的阳光,无法赠送",
        )
        return

    if update_sun(group_id, target_user_id, amount) and update_sun(
        group_id, user_id, -amount
    ):
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]成功赠送给[CQ:at,qq={target_user_id}][{amount}]颗阳光",
        )
    else:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]赠送失败,目标用户不存在或你的阳光不足",
        )


# 赠送雨水
async def give_rain(websocket, group_id, user_id, target_user_id, amount, message_id):
    user_rain = load_user_rain(group_id, user_id)
    if not user_rain or user_rain < amount:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]你没有足够的雨水,无法赠送",
        )
        return

    if update_rain(group_id, target_user_id, amount) and update_rain(
        group_id, user_id, -amount
    ):
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]成功赠送给[CQ:at,qq={target_user_id}][{amount}]滴雨水",
        )
    else:
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]赠送失败,目标用户不存在或你的雨水不足",
        )


# 群消息处理函数
async def handle_CollectTheSun_group_message(websocket, msg):
    # 确保数据目录存在
    os.makedirs(DATA_DIR, exist_ok=True)

    try:
        user_id = str(msg.get("user_id"))
        group_id = str(msg.get("group_id"))
        raw_message = str(msg.get("raw_message"))
        message_id = str(msg.get("message_id"))

        # 初始化数据库
        init_database()

        # 检测日期,军训已结束,不用再收集阳光了
        if datetime.datetime.now() > datetime.datetime(2024, 9, 14):
            return

        # 菜单
        if raw_message == "sunmenu":
            await sun_menu(websocket, group_id, message_id)
            return

        if (
            raw_message == "收集阳光"
            or raw_message == "sun"
            or raw_message == "啦啦啦种太阳"
            or raw_message == "种太阳"
        ):
            if not is_in_cd(group_id, user_id):
                await collect_sun(websocket, group_id, user_id, message_id)
                return
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]你当前处于冷却状态,冷却时间:{60 - (datetime.datetime.now() - load_user_last_operation_time(group_id, user_id)).seconds}秒",
                )
                return

        # 收集雨水
        if raw_message == "收集雨水" or raw_message == "rain":
            if not is_in_cd(group_id, user_id):
                await collect_rain(websocket, group_id, user_id, message_id)
                return
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]你当前处于冷却状态,冷却时间:{60 - (datetime.datetime.now() - load_user_last_operation_time(group_id, user_id)).seconds}秒",
                )
                return

        # 查看信息
        if raw_message.startswith("查看信息") or raw_message.startswith("suninfo"):
            match = re.search(r"\[CQ:at,qq=(\d+)\]", raw_message)
            if match:
                target_user_id = match.group(1)
                await check_user_info(
                    websocket,
                    group_id,
                    target_user_id,
                    message_id,
                )
            else:
                await check_info(websocket, group_id, user_id, message_id)
            return

        # 加入奇遇
        if raw_message == "加入奇遇" or raw_message == "sunjoin":
            if join_event(group_id, user_id):
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]你已成功加入奇遇,你在本群的每句话都有 1% 的概率触发奇遇事件！",
                )
            return

        # 退出奇遇
        if raw_message == "退出奇遇" or raw_message == "sunquit":
            if quit_event(group_id, user_id):
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]你已成功退出奇遇",
                )
            return

        # 阳光排行榜
        if raw_message == "阳光榜" or raw_message == "sunrank":
            await sun_rank(websocket, group_id, message_id)
            return

        # 雨水排行榜
        if raw_message == "雨水榜" or raw_message == "rainrank":
            await rain_rank(websocket, group_id, message_id)
            return

        # 抢夺阳光
        if raw_message.startswith("偷阳光") or raw_message.startswith("stealsun"):
            if not is_in_cd(group_id, user_id):
                steal_sun_match = re.search(r"\[CQ:at,qq=(\d+)\]", raw_message)
                if steal_sun_match:
                    target_user_id = steal_sun_match.group(1)
                    await steal_sun(
                        websocket, group_id, user_id, target_user_id, message_id
                    )
                    return
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]你当前处于冷却状态,冷却时间:{60 - (datetime.datetime.now() - load_user_last_operation_time(group_id, user_id)).seconds}秒",
                )
                return

        # 抢夺雨水
        if raw_message.startswith("偷雨水") or raw_message.startswith("stealrain"):
            steal_rain_match = re.search(r"\[CQ:at,qq=(\d+)\]", raw_message)
            if not is_in_cd(group_id, user_id):
                if steal_rain_match:
                    target_user_id = steal_rain_match.group(1)
                    await steal_rain(
                        websocket, group_id, user_id, target_user_id, message_id
                    )
                    return
            else:
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]你当前处于冷却状态,冷却时间:{60 - (datetime.datetime.now() - load_user_last_operation_time(group_id, user_id)).seconds}秒",
                )
                return

        # 赠送阳光
        if raw_message.startswith("送阳光") or raw_message.startswith("givesun"):
            raw_message = raw_message.replace(" ", "")
            give_sun_match = re.search(r"\[CQ:at,qq=(\d+)\]([0-9]+)", raw_message)
            if give_sun_match:
                target_user_id = give_sun_match.group(1)
                amount = int(give_sun_match.group(2))
                await give_sun(
                    websocket, group_id, user_id, target_user_id, amount, message_id
                )
                return

        # 送雨水
        if raw_message.startswith("送雨水") or raw_message.startswith("giverain"):
            raw_message = raw_message.replace(" ", "")
            give_rain_match = re.search(r"\[CQ:at,qq=(\d+)\]([0-9]+)", raw_message)
            if give_rain_match:
                target_user_id = give_rain_match.group(1)
                amount = int(give_rain_match.group(2))
                await give_rain(
                    websocket, group_id, user_id, target_user_id, amount, message_id
                )
                return

        # 如果不是上述命令,进入奇遇事件
        await random_add(websocket, group_id, user_id, message_id)
        return

    except Exception as e:
        logging.error(f"处理CollectTheSun群消息失败: {e}")
        return
