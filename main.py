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


# 更新用户在某群的阳光
def update_sun(group_id, user_id, sun_count):

    current_time = load_user_last_operation_time(
        group_id, user_id
    )  # 获取上次sun或rain操作时间
    time = datetime.datetime.now().replace(microsecond=0)
    if current_time is None or (time - current_time).seconds > 30:
        current_sun_count = load_user_sun(group_id, user_id)  # 获取当前阳光数量
        current_rain_count = load_user_rain(group_id, user_id)  # 获取当前雨水数量
        is_join = load_user_join_event(group_id, user_id)
        total_sun_count = current_sun_count + sun_count
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO collect_the_sun (group_id, user_id, sun_count, rain_count, time, is_join) VALUES (?, ?, ?, ?, ?, ?)",
            (
                group_id,
                user_id,
                total_sun_count,
                current_rain_count,
                time,
                is_join,
            ),  # 保持雨水数量不变
        )
        conn.commit()
        conn.close()
        return True
    else:
        logging.info(
            f"用户{user_id}在{group_id}的阳光操作时间小于30秒,无法操作，还剩{30 - (time - current_time).seconds}秒"
        )
        return False


# 更新用户在某群的雨水
def update_rain(group_id, user_id, rain_count):
    current_time = load_user_last_operation_time(
        group_id, user_id
    )  # 获取上次sun或rain操作时间
    time = datetime.datetime.now().replace(microsecond=0)
    current_rain_count = load_user_rain(group_id, user_id)  # 获取当前雨水数量
    current_sun_count = load_user_sun(group_id, user_id)  # 获取当前阳光数量
    if current_time is None or (time - current_time).seconds > 30:
        is_join = load_user_join_event(group_id, user_id)
        total_rain_count = current_rain_count + rain_count
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO collect_the_sun (group_id, user_id, sun_count, rain_count, time, is_join) VALUES (?, ?, ?, ?, ?, ?)",
            (
                group_id,
                user_id,
                current_sun_count,
                total_rain_count,
                time,
                is_join,
            ),  # 保持阳光数量不变
        )
        conn.commit()
        conn.close()
        return True
    else:
        logging.info(
            f"用户{user_id}在{group_id}的雨水操作时间小于30秒,无法操作，还剩{30 - (time - current_time).seconds}秒"
        )
        return False


# 加入奇遇
def join_event(group_id, user_id):
    current_rain_count = load_user_rain(group_id, user_id)  # 获取当前雨水数量
    current_sun_count = load_user_sun(group_id, user_id)  # 获取当前阳光数量

    # 获取上次sun或rain操作时间
    current_time = load_user_last_operation_time(group_id, user_id)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO collect_the_sun (group_id, user_id, sun_count, rain_count, time, is_join) VALUES (?, ?, ?, ?, ?, ?)",
        (group_id, user_id, current_sun_count, current_rain_count, current_time, True),
    )
    conn.commit()
    conn.close()
    return True


# 退出奇遇
def quit_event(group_id, user_id):
    current_rain_count = load_user_rain(group_id, user_id)  # 获取当前雨水数量
    current_sun_count = load_user_sun(group_id, user_id)  # 获取当前阳光数量

    # 获取上次sun或rain操作时间
    current_time = load_user_last_operation_time(group_id, user_id)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT OR REPLACE INTO collect_the_sun (group_id, user_id, sun_count, rain_count, time, is_join) VALUES (?, ?, ?, ?, ?, ?)",
        (group_id, user_id, current_sun_count, current_rain_count, current_time, False),
    )
    conn.commit()
    conn.close()
    return True


# 菜单
async def sun_menu(websocket, group_id, message_id):
    content = f"""[CQ:reply,id={message_id}]来为 24 级新生收集阳光吧！每次收集阳光或雨水,都会随机增加 0-50 阳光或雨水。阳光减去雨水为有效阳光。本玩法为限时娱乐玩法,适度娱乐,切勿当真。数据全服互通,你的数据将会基于所有群聊的数据结算,切勿频繁刷分喔,否则会被关进小黑屋,玩法将于 9 月 14 日 0 点军训结束准时关服。排行榜也是全服实时结算,偷偷告诉你,这是 W1ndys 第一次写全服互通的玩法,快来看看他有没有写出愚蠢的 bug。
特殊玩法:奇遇事件,加入奇遇后群里的每一条消息都有 1% 的概率触发奇遇事件并收集 0-20 阳光或雨水（作者脑子已经炸了）。


收集阳光指令列表:
收集阳光:收集阳光 或 sun
收集雨水:收集雨水 或 rain
查看信息:查看信息 或 suninfo
加入奇遇:加入奇遇 或 sunjoin
退出奇遇:退出奇遇 或 sunquit
阳光排行榜:阳光排行榜 或 sunrank
想加新玩法或建议或bug反馈
联系https://blog.w1ndys.top/html/QQ.html"""
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

    sun_count = random.randint(1, 500)
    if update_sun(group_id, user_id, sun_count):
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]本次收集了{sun_count}颗阳光,祝24级新生军训愉快！\n"
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

    rain_count = random.randint(1, 500)
    if update_rain(group_id, user_id, rain_count):
        await send_group_msg(
            websocket,
            group_id,
            f"[CQ:reply,id={message_id}]本次收集了{rain_count}滴雨水,祝24级新生军训愉快！\n"
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


# 查看信息
async def check_info(websocket, group_id, user_id, message_id):
    content = (
        f"[CQ:reply,id={message_id}]"
        f"[你在本群]\n"
        f"阳光:{load_user_sun(group_id, user_id)},雨水:{load_user_rain(group_id, user_id)},有效阳光:{load_user_sun(group_id, user_id) - load_user_rain(group_id, user_id)}\n"
        f"[你在全服]\n"
        f"阳光:{load_user_all_sun(user_id)},雨水:{load_user_all_rain(user_id)},有效阳光:{load_user_all_sun(user_id) - load_user_all_rain(user_id)}\n"
        f"[全服数据]\n"
        f"阳光:{load_all_sun()},雨水:{load_all_rain()},有效阳光:{load_all_sun() - load_all_rain()}\n"
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
        "你在暴打W1ndys的时候找到了",
        "你在暴打W1ndys的时候找到了",
        "你在暴打W1ndys的时候找到了",
        "你在暴打W1ndys的时候找到了",
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
                        f"[CQ:reply,id={message_id}]{event}{sun_count}颗阳光,祝24级新生军训愉快！",
                    )
                    # logging.info(f"触发奇遇事件,{user_id}在{group_id}添加{sun_count}颗阳光")

            else:  # 百分之五十的概率收集雨水
                if update_rain(group_id, user_id, sun_count):
                    await send_group_msg(
                        websocket,
                        group_id,
                        f"[CQ:reply,id={message_id}]{event}{sun_count}滴雨水,祝24级新生军训愉快！",
                    )
                    # logging.info(f"触发奇遇事件,{user_id}在{group_id}添加{sun_count}滴雨水")


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

        if raw_message == "收集阳光" or raw_message == "sun":
            await collect_sun(websocket, group_id, user_id, message_id)
            return

        if raw_message == "收集雨水" or raw_message == "rain":
            await collect_rain(websocket, group_id, user_id, message_id)
            return

        if raw_message == "查看信息" or raw_message == "suninfo":
            await check_info(websocket, group_id, user_id, message_id)
            return

        if raw_message == "加入奇遇" or raw_message == "sunjoin":
            if join_event(group_id, user_id):
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]你已成功加入奇遇,你在本群的每句话都有 1% 的概率触发奇遇事件！",
                )
            return

        if raw_message == "退出奇遇" or raw_message == "sunquit":
            if quit_event(group_id, user_id):
                await send_group_msg(
                    websocket,
                    group_id,
                    f"[CQ:reply,id={message_id}]你已成功退出奇遇",
                )
            return

        if raw_message == "阳光排行榜" or raw_message == "sunrank":
            await sun_rank(websocket, group_id, message_id)
            return

        # 如果不是上述命令,进入奇遇事件
        await random_add(websocket, group_id, user_id, message_id)
        return

    except Exception as e:
        logging.error(f"处理CollectTheSun群消息失败: {e}")
        return
