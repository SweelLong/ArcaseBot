import hashlib
import json
from random import randint
import sqlite3
import time
from ncatbot.plugin import BasePlugin
from ncatbot.core.message import BaseMessage
from ncatbot.core.event import BaseMessageEvent
from ncatbot.utils import get_log
import __main__

LOG = get_log("Register")
class Register(BasePlugin):
    name = "Register"
    version = "1.0.0"
    author = "SweelLong"
    description = "注册游戏账号"
    
    async def special_call(self, msg: BaseMessage, text):
        if hasattr(msg, "group_id"):
            await self.api.post_group_msg(msg.group_id, text)
        else:
            await self.api.post_private_msg(msg.sender.user_id, text)

    @__main__.arcaea_group.command("rename", ["改名", "重命名"])
    async def rename(self, msg: BaseMessageEvent, username:str):
        if not username.isascii():
            return await msg.reply("用户名包含了特殊字符！")
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        email = str(msg.sender.user_id) + "@qq.com"
        rename_cost = config["register"]["rename_cost"]
        with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("select 1 name from user where name=?", (username,))
            if c.fetchone() is not None:
                return await msg.reply(f"用户名 {username} 已被占用惹！")
            c.execute("select ticket, name from user where email=?", (email,))
            ticket, old_name = c.fetchone()
            if ticket <= rename_cost:
                return await msg.reply(f"您的余额不足，需要 {rename_cost} 个记忆源点才能重命名！")
            c.execute("update user set name=?, ticket=ticket-? where email=?", (username, rename_cost, email))
            conn.commit()
            return await msg.reply(f"用户名修改成功！\n{old_name} -> {username}")

    @__main__.arcaea_group.command("register", ["注册", "create"])
    async def register(self, msg: BaseMessageEvent, username:str, password:str):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        try:
            await self.api.delete_msg(msg.message_id)
        except Exception as e:
            await msg.reply("我无法撤回您的消息owo")
        if not hasattr(msg, "group_id"):
            return await self.special_call(msg, "请在群聊中使用注册命令！")
        if int(msg.group_id) not in config["register"]["allowed_groups"]:
            return await self.special_call(msg, "只允许在Arcase群内使用注册命令！")
        mmr_num = config["register"]["new_user_memory"]
        try:
            if not username or not password:
                return await self.special_call(msg, "请输入您的用户名和密码！")
            email = str(msg.sender.user_id) + "@qq.com"
            with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("select 1 from user where email=?", (email,))
                if c.fetchone() is not None:
                    return await self.special_call(msg, "您已经注册过了！不能重复注册哦~")
                if not username.isascii():
                    return await self.special_call(msg, "用户名包含了特殊字符！")
                c.execute("select 1 from user where name=?", (username,))
                if c.fetchone() is not None:
                    return await self.special_call(msg, f"啊哦，用户名 {username} 已被注册惹！")
                hash_pwd = hashlib.sha256(password.encode("utf8")).hexdigest()
                now = int(time.time() * 1000)
                random_times = 0
                while random_times <= 1000:
                    random_times += 1
                    user_code = ''.join([str(randint(0, 9)) for _ in range(9)])
                    c.execute("select 1 from user where user_code=?", (user_code,))
                    if c.fetchone() is None:
                        break
                if random_times > 1000:
                    return await self.special_call(msg, "注册名额已满，请稍后再试吧！")
                c.execute("select max(user_id) from user")
                x = c.fetchone()
                if x[0] is not None:
                    user_id = x[0] + 1
                else:
                    user_id = 2000001
                c.execute('''insert or ignore into user(user_id, name, password, join_date, user_code, rating_ptt,
                character_id, is_skill_sealed, is_char_uncapped, is_char_uncapped_override, is_hide_rating, favorite_character, max_stamina_notification_enabled, current_map, ticket, prog_boost, email)
                values(:user_id, :name, :password, :join_date, :user_code, 0, 0, 0, 0, 0, 0, -1, 0, '', :memories, 0, :email)
                ''', {'user_code': user_code, 'user_id': user_id, 'join_date': now, 'name': username, 'password': hash_pwd, 'memories': mmr_num, 'email': email})
                c.execute('''insert or ignore into user_char values(?,?,?,?,?,?,0)''',
                               (user_id, 0, 1, 0, 0, 0))
                c.execute('''insert or ignore into user_char values(?,?,?,?,?,?,0)''',
                               (user_id, 1, 1, 0, 0, 0))
                c.execute(
                    '''select character_id, max_level, is_uncapped from character''')
                x = c.fetchall()
                if x:
                    for i in x:
                        exp = 25000 if i[1] == 30 else 10000
                        c.execute("insert or replace into user_char_full values(?,?,?,?,?,?,0)", (user_id, i[0], i[1], exp, i[2], 0))
                conn.commit()
                return await self.special_call(msg, f"注册成功！请查看个人信息~\n好友码：{user_code}\n- 用户名：{username}\n- 密码：{'*' * len(password)}\n- 邮箱：{email}")
        except Exception as e:
            LOG.error(f"注册失败: {e}")
            return await msg.reply("注册失败，请稍后再试！")

    @__main__.arcaea_group.command("forgot", ["忘记", "找回"])
    async def forgot(self, msg: BaseMessageEvent, new_password: str):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        try:
            await self.api.delete_msg(msg.message_id)
        except Exception as e:
            await msg.reply("我无法撤回您的消息owo")
        if not new_password:
            return await self.special_call(msg, "请输入新密码~")
        if len(new_password) < 6:
            return await self.special_call(msg, "啊哦，密码长度不能少于6位哦！")
        email = str(msg.sender.user_id) + "@qq.com"
        with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("select 1 from user where email=?", (email,))
            if c.fetchone() is None:
                return await self.special_call(msg, "请先注册账号！")
            hash_pwd = hashlib.sha256(new_password.encode("utf8")).hexdigest()
            c.execute("update user set password=? where email=?", (hash_pwd, email))
            conn.commit()
            return await self.special_call(msg, "您的密码修改成功！")

    @__main__.arcaea_group.command("bind", ["绑定"])
    async def bind(self, msg: BaseMessageEvent, username:str, password:str):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        try:
            await self.api.delete_msg(msg.message_id)
        except:
            await msg.reply("我无法撤回您的消息owo")
        if not username or not password:
            return await self.special_call(msg, "请输入您的用户名和密码~")
        email = str(msg.sender.user_id) + "@qq.com"
        with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("select 1 from user where email=?", (email,))
            if c.fetchone() is not None:
                return await self.special_call(msg, "名单上写您已经绑定过账号了ovo，如错误注册新账号请联系管理员！")
            c.execute("select * from user where name=?", (username,))
            account_info = c.fetchone()
            if account_info is None:
                return await self.special_call(msg, "啊哦，名单上好像找不到需要绑定的账号呢~")
            if account_info["email"].endswith("@qq.com"):
                qq = int(account_info["email"][:-7])
                members = await self.api.get_group_member_list(msg.group_id)
                for member in members.members:
                    if member.user_id == qq:
                        return await self.special_call(msg, "请不要绑定其他人的账号！")
            hash_pwd = hashlib.sha256(password.encode("utf8")).hexdigest()
            if account_info["password"] != hash_pwd:
                return await self.special_call(msg, "啊哦，密码错误，绑定Failed,哔哔--")
            c.execute("update user set email=? where name=?", (email, username))
            conn.commit()
            return await self.special_call(msg, "哔哔--，账号绑定Successed,哔哔--")

    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")