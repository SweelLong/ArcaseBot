from ncatbot.plugin import BasePlugin
from ncatbot.core.message import BaseMessage
from ncatbot.utils import get_log
import sqlite3
import json
import time
import __main__

LOG = get_log("Fragment")
class Fragment(BasePlugin):
    name = "Fragment"
    version = "1.0.0"
    author = "SweelLong"
    description = "残片兑换"

    @__main__.arcaea_group.command("fragment", ["残片"])
    async def handle_Fragment(self, msg: BaseMessage, num: int):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
            email = str(msg.sender.user_id) + "@qq.com"
            with sqlite3.connect(config["database"]["server"]) as conn:
                conn.row_factory = sqlite3.Row
                c = conn.cursor()
                c.execute("SELECT ticket, user_id FROM user WHERE email=?", (email,))
                ticket = c.fetchone()
                if ticket is None:
                    return await msg.reply("请先注册账号！")
                if ticket[0] < num:
                    return await msg.reply(f"余额不足！\n({num}/{ticket[0]})")
                user_id = ticket[1]
                present_id = '残片兑换' + str(user_id)
                c.execute(f"SELECT 1 FROM user_present WHERE user_id=? AND present_id=?", (user_id, present_id))
                if c.fetchone() is not None:
                    return await msg.reply("请先领取已经兑换的残片！")
                try:
                    c.execute("INSERT INTO present(present_id, expire_ts, description) VALUES (?, ?, ?)", (present_id, (int((time.time() + 86400) * 1000)), '残片兑换：请尽快领取兑换的残片！'))
                    c.execute("INSERT INTO present_item(present_id, item_id, type, amount) VALUES (?, 'fragment', 'fragment', ?)", (present_id, num))
                except:
                    c.execute("UPDATE present SET expire_ts=? WHERE present_id=?", ((int((time.time() + 86400) * 1000)), present_id))
                    c.execute("UPDATE present_item SET amount=? WHERE present_id=?", (num, present_id))
                c.execute("INSERT INTO user_present(user_id, present_id) VALUES (?, ?)", (user_id, present_id))
                c.execute("UPDATE user SET ticket=ticket-? WHERE email=?", (num, email))
                conn.commit()
                return await msg.reply(f"兑换成功！残片将以礼物形式发放请及时查收~\n({num} 记忆源点 -> {num} 残片)")
                    
    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")