from ncatbot.plugin import BasePlugin
from ncatbot.core.event import BaseMessageEvent
from ncatbot.utils import get_log
import sqlite3
import json
import __main__

LOG = get_log("Alias")
class Alias(BasePlugin):
    name = "Alias"
    version = "1.0.0"
    author = "SweelLong"
    description = "单曲别名管理插件，支持添加、删除和查询歌曲别名"

    @__main__.arcaea_group.command("alias", ["别名"])
    async def alias_link(self, msg: BaseMessageEvent):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        qq = msg.sender.user_id
        email = str(qq) + "@qq.com"
        with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT 1 FROM user WHERE email =?", (email,))
            if not c.fetchone():
                return await msg.reply("请先注册或绑定游戏账号！")
            else:
                return await msg.reply(f"查询及编辑别名请前往：https://arcase.swiro.top/alias/{qq}")
        
    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")