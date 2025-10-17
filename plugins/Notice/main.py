import random
import json
import __main__
from ncatbot.plugin import BasePlugin
from ncatbot.utils import get_log
from ncatbot.core.event import NoticeEvent
from ncatbot.plugin_system.event import NcatBotEvent

LOG = get_log("Notice")
class Notice(BasePlugin):
    name = "Notice"
    author = "SweelLong"
    description = "消息事件的处理"
    version = "1.0.0"

    async def handle_notice_event(self, msg: NcatBotEvent):
        event: NoticeEvent = msg.data
        if hasattr(event, "sub_type") and event.sub_type == "poke":
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            if config["main"]["qq_id"] == event.target_id:
                if hasattr(event, "group_id"):
                    return await self.api.post_group_msg(event.group_id, random.choice(config["poke"]["default"]))
                else:
                    return await self.api.post_private_msg(event.user_id, random.choice(config["poke"]["default"]))
        if hasattr(event, "notice_type") and event.notice_type == "group_increase":
            welcome_msg = "欢迎新群员！输入/a help查看Suo Yuki的帮助菜单哦~"
            if hasattr(event, "group_id"):
                return await self.api.post_group_msg(event.group_id, welcome_msg)
            else:
                return await self.api.post_private_msg(event.user_id, welcome_msg)
        # TODO: 自动上传不必要的文件到回收站，但似乎需要packetBackend dlc才可以使用！
        #if hasattr(event, "notice_type") and event.notice_type == "group_upload":
        #    folder_id = await __main__.get_qq_group_folder_id(event.group_id, "回收站")
        #    root_result = await self.api.get_group_root_files(event.group_id)
        #    for file in root_result["files"]:
        #        await self.api.move_group_file(event.group_id, file.get("file_id"), "", "回收站")

    async def on_load(self):
        self.event_bus.subscribe(
            event_type="ncatbot.notice_event",
            handler=self.handle_notice_event
        )
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")