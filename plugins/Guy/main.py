from PIL import Image
import os
import random
import json
from typing import Optional
from ncatbot.plugin import BasePlugin
from ncatbot.core import Image as BotImage
from ncatbot.core.event import BaseMessageEvent
from ncatbot.utils import get_log
import __main__

LOG = get_log("Guy")
class Guy(BasePlugin):
    name = "Guy"
    version = "1.0.0"
    author = "SweelLong"
    description = "杠钙"

    @__main__.arcaea_group.command("guy", ["钙哥", "杠钙"])
    async def handle_guy_command(self, msg: BaseMessageEvent):
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            save_path = os.path.join(config["path"]["src"], "guy")
            tmp_file = config["path"]["saves"]
            valid_extensions = ('.jpg', '.gif')
            pic_files = [f for f in os.listdir(save_path) 
                    if f.lower().endswith(valid_extensions) 
                    and os.path.isfile(os.path.join(save_path, f))]
            if not pic_files:
                return await msg.reply("找不到钙哥表情包惹~")
            selected_pic = random.choice(pic_files)
            pic_path = os.path.join(save_path, selected_pic)
            max_size = 200
            resized_path: Optional[str] = None
            with Image.open(pic_path) as img:
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new(img.mode[:-1], img.size, (255, 255, 255))
                    background.paste(img, img.split()[-1])
                    img = background
                elif img.mode == 'P':
                    img = img.convert('RGB')
                width, height = img.size
                if max(width, height) > max_size:
                    ratio = max_size / max(width, height)
                    new_size = (int(width * ratio), int(height * ratio))
                    img = img.resize(new_size, Image.Resampling.LANCZOS)
                    ext = os.path.splitext(selected_pic)[1]
                    resized_path = os.path.join(tmp_file, f"Guy{ext}")
                    img.save(resized_path)
                else:
                    resized_path = pic_path
            if resized_path and os.path.exists(resized_path):
                if hasattr(msg, "group_id"):
                    await self.api.post_group_msg(msg.group_id, BotImage(resized_path))
                else:
                    await self.api.post_private_msg(msg.sender.user_id, BotImage(resized_path))
            else:
                await msg.reply("图片处理失败~")
        except Exception as e:
            await msg.reply(f"发送钙哥表情包失败：{str(e)}")

    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")