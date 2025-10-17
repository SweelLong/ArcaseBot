import time
import random
import sqlite3
import json
from ncatbot.plugin import BasePlugin
from ncatbot.core.event import BaseMessageEvent
from ncatbot.utils import get_log
import __main__

LOG = get_log("Snatch")
class Snatch(BasePlugin):
    name = "Snatch"
    author = "SweelLong"
    description = "记忆源点争夺"
    version = "1.0.0"

    @__main__.arcaea_group.command("snatch", ["争夺", "抢夺"])
    async def snatch(self, msg: BaseMessageEvent):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            suoyuki_email = str(config["main"]["qq_id"]) + "@qq.com"
            c.execute("SELECT user_id FROM user WHERE email=?", (suoyuki_email,))
            datainfo = c.fetchone()
            if not datainfo:
                c.execute("SELECT MAX(user_id) FROM user")
                try:
                    next_user_id = c.fetchone()[0] + 1
                except:
                    next_user_id = 2000001
                c.execute("INSERT INTO user (user_id, email, join_date, name, user_code, ticket) VALUES (?, ?, ?, 'Suo Yuki', '000000000', 100)", (next_user_id, suoyuki_email, int(time.time() * 1000)))
                conn.commit()
                suoyuki_user_id = next_user_id
            else:
                suoyuki_user_id = datainfo[0]
            user_id = msg.sender.user_id
            c.execute("SELECT * FROM user WHERE email=?", (f"{user_id}@qq.com",))
            whose_info = c.fetchone()
            if not whose_info:
                return await msg.reply("注册账号才能开启记忆源点争夺战哦！")
            elif whose_info['ticket'] <= 100:
                return await msg.reply("诶诶，你才这点记忆源点，想...想干嘛？我才不让你抢走我的东西呢！")
            # 执行抽奖逻辑
            TYPE = [2, 6, 32, 20, 40]
            SNATCH_POOL = [j for i in range(len(TYPE)) for j in [TYPE[i]] * TYPE[i]]
            grab_ticket = random.choice(SNATCH_POOL)
            # 2%概率：用户记忆源点翻倍
            if grab_ticket == 2:
                n = random.randint(2, 3)
                # 获取当前用户的记忆源点数量
                c.execute("SELECT ticket FROM user WHERE email=?", (f"{user_id}@qq.com",))
                current_ticket = c.fetchone()[0]
                # 更新为翻倍后的值
                new_ticket = current_ticket * n
                c.execute("UPDATE user SET ticket=? WHERE email=?", (new_ticket, f"{user_id}@qq.com",))
                conn.commit()
                return await msg.reply(f"我把你所有的记忆源点翻{n}倍，可以把手撒开吗...")
            # 6%概率：从suoyuki处获得记忆源点
            elif grab_ticket == 6:
                c.execute("SELECT ticket FROM user WHERE user_id=?", (suoyuki_user_id,))
                suoyuki_ticket = c.fetchone()[0]
                if suoyuki_ticket <= 0:
                    return await msg.reply("干什么！我可连一个记忆源点都没有...")
                rate = random.uniform(0.5, 1.0)
                n = int(random.randint(int(suoyuki_ticket * 0.25), int(suoyuki_ticket * 0.35)) * rate)
                c.execute("UPDATE user SET ticket = ticket + ? WHERE email=?", (n, f"{user_id}@qq.com",))
                c.execute("UPDATE user SET ticket = ticket - ? WHERE user_id=?", (n, suoyuki_user_id,))
                conn.commit()
                return await msg.reply(f"我分你一点{n}个记忆源点，就当作可怜你吧...")
            # 32%概率：被suoyuki夺走记忆源点（8-40区间）
            elif grab_ticket == 32:
                c.execute("SELECT ticket FROM user WHERE email=?", (f"{user_id}@qq.com",))
                user_ticket = c.fetchone()
                if user_ticket is None or user_ticket[0] <= 0:
                    return await msg.reply("什么？你居然一个记忆源点都没有！没事，我会给你打欠条的！")
                # 计算可夺取的数量
                max_value = user_ticket[0] // 2
                ticket = random.randint(50, max_value) if max_value >= 50 else 50
                # 更新数据库
                c.execute("UPDATE user SET ticket = ticket + ? WHERE user_id=?", (ticket, suoyuki_user_id,))
                c.execute("UPDATE user SET ticket = ticket - ? WHERE email=?", (ticket, f"{user_id}@qq.com",))
                conn.commit()
                # 获取更新后的suoyuki的记忆源点数量
                c.execute("SELECT ticket FROM user WHERE user_id=?", (suoyuki_user_id,))
                suoyuki_ticket = c.fetchone()[0]
                # 获取更新后的玩家的记忆源点数量
                c.execute("SELECT ticket FROM user WHERE email=?", (f"{user_id}@qq.com",))
                user_rest_ticket = c.fetchone()[0]
                return await msg.reply(f"嘻嘻，你有{ticket}个记忆源点而现在却都是我的啦，而你只剩下{user_rest_ticket}个咯！\n哎呀，我还剩下{suoyuki_ticket}个记忆源点呢~")
            # 60%概率：20 + 40
            elif grab_ticket == 20:
                c.execute("SELECT ticket FROM user WHERE user_id=?", (suoyuki_user_id,))
                suoyuki_ticket = c.fetchone()[0]
                if suoyuki_ticket <= 0:
                    return await msg.reply("干什么！我可连一个记忆源点都没有...")
                n = random.randint(0, 100)
                # 更新用户的记忆源点
                c.execute("UPDATE user SET ticket = ticket + ? WHERE email=?", (n, f"{user_id}@qq.com",))
                # 更新suoyuki的记忆源点
                c.execute("UPDATE user SET ticket = ticket - ? WHERE user_id=?", (n, suoyuki_user_id,))
                conn.commit()
                return await msg.reply(f"好啦好啦，我赏你{n}个记忆源点，下次我可不会再让你了！")
            # 40%概率：100
            elif grab_ticket == 40:
                c.execute("SELECT ticket FROM user WHERE email=?", (f"{user_id}@qq.com",))
                user_ticket = c.fetchone()
                if user_ticket is None or user_ticket[0] <= 0:
                    return await msg.reply("什么？你居然一个记忆源点都没有！没事，我会给你打欠条的！")
                # 计算可夺取的数量
                ticket = random.randint(0, 100)
                # 更新数据库
                c.execute("UPDATE user SET ticket = ticket + ? WHERE user_id=?", (ticket, suoyuki_user_id,))
                c.execute("UPDATE user SET ticket = ticket - ? WHERE email=?", (ticket, f"{user_id}@qq.com",))
                conn.commit()
                # 获取更新后的suoyuki的记忆源点数量
                c.execute("SELECT ticket FROM user WHERE user_id=?", (suoyuki_user_id,))
                suoyuki_ticket = c.fetchone()[0]
                # 获取更新后的玩家的记忆源点数量
                c.execute("SELECT ticket FROM user WHERE email=?", (f"{user_id}@qq.com",))
                user_rest_ticket = c.fetchone()[0]
                return await msg.reply(f"哎，这次拿的不多，不过你知道我的厉害就好，哈哈！{ticket}个记忆源点我就收下了。嗯，没事...我数过，你还有{user_rest_ticket}个的！\n我还有{suoyuki_ticket}个记忆源点呢~")

    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")