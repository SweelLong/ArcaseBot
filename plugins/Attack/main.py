import random
import json
import sqlite3
from ncatbot.plugin import BasePlugin
from ncatbot.core.event import BaseMessageEvent
from ncatbot.core.event.message_segment import MessageArray
from ncatbot.core.api.api_group import GroupMemberList, GroupMemberInfo
from ncatbot.utils import get_log
import __main__

LOG = get_log("Attack")
class Attack(BasePlugin):
    name = "Attack"
    author = "SweelLong"
    description = "攻击命令"
    version = "1.0.0"

    @__main__.arcaea_group.command("attack", ["攻击", "袭击"])
    async def Attack(self, msg: BaseMessageEvent, target_user: str):
        if not hasattr(msg, "group_id"):
            return await msg.reply("请在群聊中使用此命令。")
        qq_id = target_user
        if qq_id.strip().startswith('At(qq="') and qq_id.strip().endswith('")'):
            qq_id = qq_id.strip()[7:-2]
        shuts: GroupMemberList = await self.api.get_group_shut_list(msg.group_id)
        for shut in shuts.members:
            shut: GroupMemberInfo
            if shut.user_id == int(qq_id):
                return await msg.reply("对方已被禁言，无法命中！")
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        with sqlite3.connect(config["database"]["server"]) as conn:
            c = conn.cursor()
            c.execute("SELECT 1 FROM user WHERE email=?", (str(qq_id) + "@qq.com",))
            if not c.fetchone():
                return await msg.reply("对方为注册账号，无法命中！")
        rate = random.randint(1, 100)
        text = MessageArray().add_at(msg.sender.user_id).add_text("试图攻击").add_at(qq_id)
        if rate <= 60:
            second = random.randint(30, 5 * 60)
            await self.api.set_group_ban(msg.group_id, msg.sender.user_id, second)
            await self.api.post_group_msg(msg.group_id, rtf=text.add_text(f"\n失败，被禁言{second}秒。"))
        else:
            second = random.randint(30, 5 * 60)
            compensation = random.randint(50, 100)
            await self.api.set_group_ban(msg.group_id, qq_id, second)
            await self.api.post_group_msg(msg.group_id, rtf=text.add_text(f"\n成功，禁言{second}秒。\n受害者获得{compensation}个记忆源点补偿！"))
            c.execute("UPDATE user SET ticket=ticket+? WHERE email=?", (compensation, str(qq_id) + "@qq.com"))
            conn.commit()

    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")