import glob
from ncatbot.plugin import BasePlugin
from ncatbot.core import MessageChain, At
from ncatbot.core import Image as BotImage
from ncatbot.core.event import BaseMessageEvent
from ncatbot.utils import get_log
import os
import sqlite3
import json
import random
from PIL import Image
import __main__

LOG = get_log("AiChan")
class AiChan(BasePlugin):
    name = "AiChan"
    version = "1.0.0"
    author = "SweelLong"
    description = "Ai酱推荐歌曲"

    def get_diff_str(self, difficulty: int) -> str:
        if difficulty == 0:
            return "PAST"
        elif difficulty == 1:
            return "PRESENT"
        elif difficulty == 2:
            return "FUTURE"
        elif difficulty == 3:
            return "BEYOND"
        elif difficulty == 4:
            return "ETERNAL"

    def get_diff_constant(self, difficulty: int) -> str:
        if difficulty == 0:
            return "rating_pst"
        elif difficulty == 1:
            return "rating_prs"
        elif difficulty == 2:
            return "rating_ftr"
        elif difficulty == 3:
            return "rating_byn"
        elif difficulty == 4:
            return "rating_etr"

    @__main__.arcaea_group.command("aichan", ["ai酱", "推荐"])
    async def aichan(self, msg: BaseMessageEvent):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        aichan_text = json.load(open(os.path.join(config["path"]["src"], "AiChan.json"), "r", encoding="utf-8"))
        random_text = random.choice(aichan_text['ai_chan'])
        with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""SELECT * 
                           FROM best_score 
                           NATURAL JOIN (SELECT user_id, email FROM user)
                           WHERE email=?
                           ORDER BY random() LIMIT 1""", (str(msg.sender.user_id) + '@qq.com', ))
            info = c.fetchone()
            if info is None:
                return await msg.reply("Ai酱找不到你的分数信息，无法为你推荐呢~")
            c.execute("SELECT * FROM chart WHERE song_id=?", (info['song_id'],))
            const_info = c.fetchone() 
            if const_info is None:
                const_info = {"name": info["song_id"], "rating_pst": 0, "rating_prs": 0, "rating_ftr": 0, "rating_byn": 0, "rating_etr": 0}
        random_text = random_text.replace("“songName”", const_info['name'])
        random_text = random_text.replace("difficulty", self.get_diff_str(info['difficulty']))
        random_text = random_text.replace("constant，", str(round(const_info[self.get_diff_constant(info['difficulty'])] / 10, 1)))
        random_text = random_text.replace("score", str(info['score']))
        song_id = info['song_id']
        song_jacket_path = os.path.join(config["path"]["src"], "random.jpg")
        if os.path.exists(os.path.join(config["path"]["illustrations"], f"dl_{song_id}")):
            jacket_path = glob.glob(os.path.join(config["path"]["illustrations"], f"dl_{song_id}", "*.[jJ][pP][gG]"))
            if jacket_path:
                song_jacket_path = jacket_path[0]
        elif os.path.exists(os.path.join(config["path"]["illustrations"], song_id)):
            jacket_path = glob.glob(os.path.join(config["path"]["illustrations"], song_id, "*.[jJ][pP][gG]"))
            if jacket_path:
                song_jacket_path = jacket_path[0]
        try:
            with Image.open(song_jacket_path) as jacket_img, Image.open(os.path.join(config["path"]["src"], "ai-chan.png")) as ai_chan_img:
                ai_chan_img = ai_chan_img.convert("RGBA")
                jacket_width, jacket_height = jacket_img.size
                max_width = int(jacket_width * 0.25)
                max_height = int(jacket_height * 0.25)
                ai_width, ai_height = ai_chan_img.size
                scale = min(max_width / ai_width, max_height / ai_height)
                new_ai_width = int(ai_width * scale)
                new_ai_height = int(ai_height * scale)
                ai_chan_img = ai_chan_img.resize((new_ai_width, new_ai_height))
                margin = 10
                x = jacket_width - new_ai_width - margin
                y = jacket_height - new_ai_height - margin
                if jacket_img.mode != "RGBA":
                    jacket_img = jacket_img.convert("RGBA")
                result_img = jacket_img.copy()
                result_img.paste(ai_chan_img, (x, y), ai_chan_img)
                OUTPUT_PATH = os.path.join(config["path"]["saves"], "AiChan.png")
                result_img.convert("RGB").save(OUTPUT_PATH, quality=95)
                message = MessageChain([
                    At(msg.sender.user_id),
                    BotImage(OUTPUT_PATH),
                    random_text
                ])
                if hasattr(msg, "group_id"):
                    return await self.api.post_group_msg(msg.group_id, rtf=message)
                else:
                    return await self.api.post_private_msg(msg.sender.user_id, rtf=message)
        except Exception as e:
            LOG.error(f"处理图片时出错: {str(e)}")
            return await msg.reply("出错了，请稍后再试~")
        
    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")