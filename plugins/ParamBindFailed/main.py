from ncatbot.plugin import BasePlugin
from ncatbot.utils import get_log
import __main__

LOG = get_log("ParamBindFailed")
class ParamBindFailed(BasePlugin):
    name = "ParamBindFailed"
    version = "1.0.0"
    author = "SweelLong"
    description = "命令参数绑定失败时返回错误信息"

    async def on_load(self):
        self.event_bus.subscribe(
            event_type="ncatbot.param_bind_failed",
            handler=self.handle_param_error
        )
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")

    async def handle_param_error(self, event):
        if event.data['cmd'] == "attack":
            return await event.data["event"].reply("袭击命令格式错误！请使用：/袭击 <(@)QQ号>")
        elif event.data['cmd'] == "chart":
            return await event.data["event"].reply("谱面命令格式错误！请使用：/谱面 <歌曲ID/别名> <难度(0-4)>")
        elif event.data['cmd'] == "fragment":
            return await event.data["event"].reply("残片命令格式错误！请使用：/残片 <数量>")
        elif event.data['cmd'] == "rating":
            return await event.data["event"].reply("定数命令格式错误！请使用：/定数 <定数/起始定数> <(可选)结束定数>")
        elif event.data['cmd'] == "register":
            return await event.data["event"].reply("注册命令格式错误！请使用：/注册 <用户名> <密码>")
        elif event.data['cmd'] == "rename":
            return await event.data["event"].reply("改名命令格式错误！请使用：/改名 <新昵称>")
        elif event.data['cmd'] == "forgot":
            return await event.data["event"].reply("忘记命令格式错误！请使用：/忘记 <新密码>")
        elif event.data['cmd'] == "bind":
            return await event.data["event"].reply("绑定命令格式错误！请使用：/绑定 <用户名> <密码>")
        elif event.data['cmd'] == "transfer":
            return await event.data["event"].reply("转账命令格式错误！请使用：/转账 <(@)QQ号> <数量>")
        elif event.data['cmd'] == "rank":
            return await event.data["event"].reply("排行命令格式错误！请使用：/排行 <#/ptt>")
        else:
            return await event.data["event"].reply("命令格式错误！请使用：/帮助")