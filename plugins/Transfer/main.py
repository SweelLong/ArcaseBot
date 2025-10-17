import sqlite3
import json
from ncatbot.plugin import BasePlugin
from ncatbot.core.event import BaseMessageEvent
from ncatbot.utils import get_log
import __main__

LOG = get_log("Transfer")
class Transfer(BasePlugin):
    name = "Transfer"
    version = "1.0.0"
    author = "SweelLong"
    description = "转账插件"

    @__main__.arcaea_group.command("transfer", ["转账"])
    async def transfer(self, msg: BaseMessageEvent, target_user: str, amount: int):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("SELECT user_id, ticket FROM user WHERE email=?", (str(msg.sender.user_id) + "@qq.com",))
            origin_user = c.fetchone()
            if origin_user is None:
                return await msg.reply("你还没有注册，请先注册！")
            if origin_user[1] < amount:
                return await msg.reply("余额不足！")
            qq_id = target_user
            if qq_id.strip().startswith('At(qq="') and qq_id.strip().endswith('")'):
                qq_id = qq_id.strip()[7:-2]
            c.execute("SELECT user_id, name FROM user WHERE email=?", (qq_id + "@qq.com",))
            target_user_info = c.fetchone()
            if target_user_info is None:
                return await msg.reply("找不到收款方！")
            else:
                c.execute("UPDATE user SET ticket=ticket+? WHERE user_id=?", (amount, target_user_info[0]))
                c.execute("UPDATE user SET ticket=ticket-? WHERE user_id=?", (amount, origin_user[0]))
                conn.commit()
                await msg.reply(f"转账成功，{amount}个记忆源点已转给{target_user_info[1]}！")

    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")
