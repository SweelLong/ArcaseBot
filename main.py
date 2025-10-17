# ========= 导入模块 ==========
import json
import os
import time
import random
import sqlite3
import datetime
import pandas
import requests
import __main__
from ncatbot.utils import get_log
from ncatbot.plugin_system import command_registry
from ncatbot.core import BotClient, GroupMessage, PrivateMessage

# ========== 创建对象 ==========
bot = BotClient()
_log = get_log()
config = {}
arcaea_group = command_registry.group("a", description="Arcaea核心功能命令分组")

# ========== 辅助函数 ==========
async def get_qq_group_folder_id(group_id, folder_name, retry=0):
    root_result = await bot.api.get_group_root_files(group_id)
    for file in root_result["folders"]:
        if file.get("folder_name") == folder_name:
            return file["folder_id"]
    if retry:
        return None
    await bot.api.create_group_file_folder(group_id, folder_name)
    return get_qq_group_folder_id(group_id, folder_name)

# ========== 功能函数 ==========
async def punch_in(msg: GroupMessage):
    today = str(datetime.date.today())
    today_currency = random.randint(*config["main"]["currency_range"])
    with sqlite3.connect(config["database"]["bot"], timeout=30) as conn:
        cursor = conn.cursor()
        # 清理3天之前的记录
        time_delta = str(datetime.date.today() - datetime.timedelta(1))
        cursor.execute("DELETE FROM punch_in WHERE today<=?", (time_delta, ))
        conn.commit()
        # 检查今日签到记录是否存在
        cursor.execute("SELECT 1 FROM punch_in WHERE qq_id=? AND today=?", (msg.user_id, today))
        result = cursor.fetchone()
        if result is None:
            with sqlite3.connect(config["database"]["server"], timeout=30) as conn2:
                cursor2 = conn2.cursor()
                # 获取用户ID
                cursor2.execute("SELECT user_id FROM user WHERE email=?", (str(msg.user_id) + "@qq.com",))
                user_id = cursor2.fetchone()
                if user_id is None:
                    return await msg.reply("请先注册账号！")
                user_id = user_id[0]
                present_id = "每日签到" + str(msg.user_id)
                description = f"QQ号码{msg.user_id}的每日签到"
                expire_time = int((time.time() + 86400) * 1000)
                # 检查present表记录是否存在
                cursor2.execute("SELECT 1 FROM present WHERE present_id=? AND description=?", (present_id, description))
                if cursor2.fetchone():
                    cursor2.execute("UPDATE present SET expire_ts=? WHERE present_id=? AND description=?", (expire_time, present_id, description))
                else:
                    cursor2.execute("INSERT INTO present (present_id, description, expire_ts) VALUES (?,?,?)", (present_id, description, expire_time))
                conn2.commit()
                # 检查present_item表记录是否存在
                cursor2.execute("SELECT 1 FROM present_item WHERE present_id=? AND item_id=? AND type=?", (present_id, "memory", "memory"))
                if cursor2.fetchone():
                    cursor2.execute("UPDATE present_item SET amount=? WHERE present_id=? AND item_id=? AND type=?", (today_currency, present_id, "memory", "memory"))
                else:
                    cursor2.execute("INSERT INTO present_item (present_id, item_id, type, amount) VALUES (?,?,?,?)", (present_id, "memory", "memory", today_currency))
                conn2.commit()
                # 检查user_present表记录是否存在
                cursor2.execute("SELECT 1 FROM user_present WHERE user_id=? AND present_id=?", (user_id, present_id))
                if cursor2.fetchone():
                    cursor2.execute("DELETE FROM user_present WHERE user_id=? AND present_id=?", (user_id, present_id))
                    conn2.commit()
                cursor2.execute("INSERT INTO user_present (user_id, present_id) VALUES (?,?)", (user_id, present_id))
                conn2.commit()
                # 插入打卡记录
                cursor.execute("INSERT INTO punch_in (qq_id, today) VALUES (?,?)", (msg.user_id, today))
                conn.commit()
                return await msg.reply(f"今日签到成功，获得{today_currency}个记忆源点！")
        else:
            return await msg.reply("你今天已经签到过了！")

async def get_arcaea_china_version_url(msg: GroupMessage):
    response = requests.get("https://webapi.lowiro.com/webapi/serve/static/bin/arcaea/apk")
    if response.status_code == 200:
        data = response.json()
        return await msg.reply(f"爬取成功：{data['success']}\n获取到{data['value']['version']}最新下载链接：{data['value']['url']}\n若无法下载请检查网络连接！")
    else:
        return await msg.reply("无法获取Arcaea的最新下载链接！")

async def get_chart_constant_excel(msg: GroupMessage):
    try:
        SONG_LIST_PATH = config["path"]["songlist"]
        if not os.path.exists(SONG_LIST_PATH):
            return await msg.reply(f"错误：歌曲列表文件不存在 - {SONG_LIST_PATH}")
        with open(SONG_LIST_PATH, "r", encoding="utf-8") as f:
            songs = [{
                "id": s.get("id"),
                "set": s.get("set", ""),
                "title_en": s.get("title_localized", {}).get("en", ""),
                "difficulties": s.get("difficulties", [])
            } for s in json.load(f).get("songs", [])]
        with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
            cursor = conn.cursor()
            result = []
            SP_SPNGS = [
                "tempestissimo", "infinitestrife", "worldender", "pentiment", 
                "arcanaeden", "testify", "lovelessdress", "last", 
                "lasteternity", "callimakarma", "designant", "astralquant"
            ]
            for song in songs:
                cursor.execute("""
                    SELECT rating_pst, rating_prs, rating_ftr, rating_byn, rating_etr 
                    FROM chart WHERE song_id = ?
                """, (song["id"],))
                data = cursor.fetchone() or [None] * 5
                diff_info = {}
                for diff in song["difficulties"]:
                    r = diff.get("rating", 0) 
                    diff_info.setdefault(diff["ratingClass"], r if r > 0 else 0)
                def get_rating(i, data_val):
                    if i not in diff_info:
                        return 0
                    elif diff_info[i] != 0:
                        if data_val is None or data_val == "":
                            return 0
                        elif (int(data_val) != 0 or song["id"] in SP_SPNGS):
                            return data_val
                        else:
                            return "待填写"
                    else:
                        if data_val is not None and int(data_val) != 0:
                            return f"该格应为0而不该有定数：{data_val}"
                        else:
                            return 0
                result.append({
                    "歌曲ID": song["id"],
                    "歌曲名称": song["title_en"],
                    "曲包ID": song["set"],
                    "PAST": get_rating(0, data[0]),
                    "PRESENT": get_rating(1, data[1]),
                    "FUTURE": get_rating(2, data[2]),
                    "BEYOND": get_rating(3, data[3]),
                    "ETERNAL": get_rating(4, data[4]),
                })
        filename = "Arcase数据库定数表.xlsx"
        file_path = os.path.abspath(os.path.join(config["path"]["saves"], filename))
        pandas.DataFrame(result).to_excel(file_path, index=False, engine='openpyxl')
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            if hasattr(msg, "group_id"):
                folder_id = await get_qq_group_folder_id(msg.group_id, "定数表")
                await bot.api.upload_group_file(msg.group_id, file_path, name=f"Arcase数据库定数表_{datetime.date.today()}.xlsx", folder=folder_id)
            else:
                await msg.reply("不允许私聊发送定数表！")
        else:
            return await msg.reply("定数表生成失败！")
    except Exception as e:
        return await msg.reply(f"定数表生成失败: {str(e)}")

async def call_copilot_api(messages):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config['copilot_api']['key']}"
    }
    data = {
        "model": "gpt-4",
        "messages": messages
    }
    try:
        response = requests.post(
            f"{config['copilot_api']['url']}/chat/completions",
            headers=headers,
            data=json.dumps(data),
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        return True, str(result["choices"][0]["message"]["content"])
    except:
        return False, "Suo Yuki现在不想和你说话哦~"
    
# ========= 特殊命令 ==========
async def special_command(msg: GroupMessage):
    if "签到" in msg.raw_message:
        await punch_in(msg)
    if msg.raw_message.lower().startswith("arcaea"):
        await get_arcaea_china_version_url(msg)
    if "定数表" in msg.raw_message:
        await get_chart_constant_excel(msg)

# ========== 回调函数 ==========
last_msg = ("", 0)
@bot.group_event()
async def on_group_message(msg: GroupMessage):
    _log.info(msg)
    await special_command(msg)
    global last_msg
    if msg.raw_message == last_msg[0] and msg.user_id != last_msg[1]:
        await bot.api.post_group_msg(msg.group_id, msg.raw_message)
    last_msg = (msg.raw_message, msg.user_id)
    if msg.raw_message.lower().startswith("suo") or msg.raw_message.lower().startswith("yuki"):
        chats = [{
            "role": "system", 
            "content": "你叫做周防有希(Suo Yuki)，设定是(高冷一点尽量不要轻易透露)：" + "".join(config["poke"]["default"])
        },
        {
            "role": "user", 
            "content": f"对方的QQ名称是{msg.sender.nickname}，QQ号码是{msg.sender.user_id}"
        }]
        with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, name, join_date, user_code, rating_ptt, email FROM user WHERE email=?", (str(msg.sender.user_id) + "@qq.com",))
            info = "对方的游戏信息每次回复都可以透露：(游戏ID，游戏名，加入时间的毫秒级时间戳，回复的时候请转换为日期时间再告诉他，好友码，潜力值(ptt)*100(回复的时候需要除100保留两位小数告诉他)，邮箱)："
            info += str(dict(cursor.fetchone())) or ""
            chats.extend([{
                "role": "user", 
                "content": info
            },
            {
                "role": "user", 
                "content": "你需要回复以下内容：" + msg.raw_message
            }])
        status, response = await call_copilot_api(chats)
        if status:
            await msg.reply(response)
        else:
            await msg.reply(response)

@bot.private_event()
async def on_private_message(msg: PrivateMessage):
    _log.info(msg)
    await special_command(msg)

# ========== 启动实例 ==========
if __name__ == "__main__":
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    bot.run(bt_uin=config["main"]["qq_id"])