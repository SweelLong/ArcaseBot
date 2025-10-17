from ncatbot.plugin import BasePlugin
from ncatbot.core import MessageChain
from ncatbot.core import Image as BotImage
from ncatbot.core.event import BaseMessageEvent
from ncatbot.utils import get_log
import os
import re
import math
import json
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont
import __main__

LOG = get_log("Help")
HELP_INFO = """
<div class="rule-section">
    <h2 class="rule-title">群机器人</h2>
    <p style="white-space: pre-wrap; ">
    <!--核心帮助菜单-->
    ⭐<code>/a help</code>帮助菜单
    ⭐<code>/a register [用户名] [密码]</code>注册账号(<span class="rule-note">只能在Arcase | Suo Yuki群聊中使用</span>)
    ⭐<code>/a bind [用户名] [密码]</code>绑定账号(<span class="rule-note">仅限老玩家使用，新用户无需绑定账号！</span>)
    ⭐<code>/a rename [新昵称]</code>花费1270记忆源点即可改名
    ⭐<code>/a forgot [新密码]</code>找回密码
    ⭐<code>/a aichan</code>让Ai酱推荐一首歌曲
    ⭐<code>/a alias</code>查看及编辑歌曲别名
    ⭐<code>/a b30</code>获取最新的b30成绩图，请勿频繁查询！
    ⭐<code>/a p30</code>获取最新的p30成绩图，请勿频繁查询！
    ⭐<code>/a 理30</code>获取最新的理30成绩图，请勿频繁查询！
    ⭐<code>/a chart [歌曲ID/别名(不含空格)] [难度(0-4)]</code>生成2D谱面图，难度对应：0=PAST, 1=PRESENT, 2=FUTURE, 3=BEYOND, 4=ETERNAL
    ⭐<code>/a guy</code>随机一张钙哥表情包
    ⭐<code>/a rank [类型(默认#值排名)]</code>玩家世界排名(POTENTIAL榜：['1', "ptt"]、#VALUE榜：['2', "#"])
    ⭐<code>/a recent</code>获取最近的游戏成绩图，请勿频繁查询！
    ⭐<code>/a transfer [@收款方] [数量]</code>源点转账
    ⭐<code>/a fragment [数量]</code>记忆源点等额兑换残片
    ⭐<code>/a rating [定数/起始定数] [(可选)结束定数]</code>查询某一定数下的所有曲目
    ⭐<code>/a attack [@玩家]</code>袭击指定玩家且40%成功率，随机禁言30s~300s，被袭击的玩家将获得50~100的记忆源点补偿！
    ⭐<code>/a snatch</code>记忆源点争夺战，规则如下：
        Suo Yuki有游戏账号且好友码为000000000存有她记忆源点余额！
        约  2% 概率随机翻 2 ~ 3 倍记忆源点，
        约  6% 概率获得她的 (25% ~ 35%) x (50% ~ 100%) 的记忆源点，
        约 20% 概率获得 0 ~ 100 个记忆源点，
        约 32% 概率被夺取 50 ~ MAX(50, 自身50%) 个记忆源点，
        约 40% 概率被夺取 0 ~ 100 个记忆源点。
        <span class="rule-note">※拥有的记忆源点数量必须超过100才会触发！</span>
    ⭐<code>签到</code>每日签到，获得200~500个记忆源点
    ⭐<code>定数表</code>从数据库获取最新的定数表文件
    ⭐<code>Arcaea</code>获取Arcaea最新下载链接(<span class="rule-note">文本以Arcaea开头，不区分大小写！</span>)
    ⭐<code>》戳一戳《</code>触发随机文本
    ⭐<code>Suo Yuki (/Suo/Yuki)</code>触发Suo Yuki的Ai聊天回复
    ==================================================
    大多数指令均支持私发，若未接收到消息，可尝试添加好友！
    所有指令直接通过使用者的QQ号码查询，无需绑定游戏账号！
    如您有Arcase相关功能上的其他需求，请联系管理员！
    感谢NekoNekoNiko120(0xc0ef2d8)提供的GPT-4.1接口支持！
    <br>
    <span class="rule-note">※B30和RecentPlay生成的#值由个人ptt降序排名，与游戏中的实际值并不相同！</span>
    <span class="rule-note">※禁止在AI聊天功能中进行色情、暴力等可能对聊天功能造成损害的引导！</span>
    <!--核心帮助菜单-->
    </p>
</div>
"""
PANEL_PADDING = 40
CONTENT_FONT_SIZE = 18
CODE_FONT_SIZE = 16
LINE_SPACING = 15
PANEL_RADIUS = 15
PANEL_COLOR = (255, 255, 255, 220) 
TITLE_FONT_SIZE = 24
FOOTER_FONT_SIZE = 14
TITLE_TEXT = "指令列表 - 帮助菜单"
FOOTER_TEXT = f"Copyright 2025 © SweelLong - 帮助"
TITLE_COLOR = (30, 30, 180)
FOOTER_COLOR = (100, 100, 100)
TITLE_SPACING = 20
FOOTER_SPACING = 15
CODE_STYLE = {
    'bg_color': (225, 225, 225, 225),
    'padding': (2, 6),
    'border_radius': 4,
    'font_size': CODE_FONT_SIZE
}
STAR_SIZE = 10
STAR_COLOR = (255, 215, 0)

class Help(BasePlugin):
    name = "Help"
    version = "1.0.0" 
    author = "SweelLong"
    description = "帮助菜单"

    def draw_star(self, draw, x, y):
        y += 12
        points = []
        for i in range(10):
            radius = STAR_SIZE if i % 2 == 0 else STAR_SIZE * 0.4
            angle = math.pi / 2 + i * math.pi * 2 / 10
            points.append((
                x + radius * math.cos(angle),
                y + radius * math.sin(angle)
            ))
        draw.polygon(points, fill=STAR_COLOR)
        return STAR_SIZE * 2, STAR_SIZE * 2

    @__main__.arcaea_group.command("help", ["帮助"])
    async def help(self, msg: BaseMessageEvent):
        # 读取配置文件
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        FONT_PATH = os.path.join(config["path"]["fonts"], "DingTalk JinBuTi.ttf")
        OUTPUT_PATH = os.path.join(config["path"]["saves"], "Help.png")
        
        soup = BeautifulSoup(HELP_INFO, "html.parser")
        content_lines = next((
            [line.strip() for line in str(section.select_one("p")).split('\n')[2:-2] if line.strip()]
            for section in soup.select(".rule-section")
            if section.select_one(".rule-title").get_text(strip=True) == "群机器人"
        ), ['未找到相关内容'])
        processed_lines = []
        for line in content_lines:
            processed_line = re.sub(r'<br\s*/?>', '\n', line)
            for sub_line in processed_line.split('\n'):
                if sub_line.strip():
                    processed_lines.append(sub_line.strip())
        content_lines = processed_lines
        parsed_lines = []
        for line in content_lines:
            parts = re.findall(r'(⭐|<code>.*?</code>|<span class="rule-note">.*?</span>|[^<⭐]+)', line)
            parsed_line = []
            for part in parts:
                if not part:
                    continue
                if part == '⭐':
                    parsed_line.append(('star', ''))
                elif part.startswith('<code>'):
                    parsed_line.append(('code', part[6:-7].strip()))
                elif part.startswith('<span class="rule-note">'):
                    parsed_line.append(('note', part[24:-7].strip()))
                else:
                    parsed_line.append(('text', part.strip()))
            parsed_lines.append(parsed_line)
        content_font = ImageFont.truetype(FONT_PATH, CONTENT_FONT_SIZE)
        code_font = ImageFont.truetype(FONT_PATH, CODE_STYLE['font_size'])
        title_font = ImageFont.truetype(FONT_PATH, TITLE_FONT_SIZE)
        footer_font = ImageFont.truetype(FONT_PATH, FOOTER_FONT_SIZE)
        temp_img = Image.new("RGBA", (1, 1))
        temp_draw = ImageDraw.Draw(temp_img)
        title_bbox = temp_draw.textbbox((0, 0), TITLE_TEXT, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        footer_bbox = temp_draw.textbbox((0, 0), FOOTER_TEXT, font=footer_font)
        footer_width = footer_bbox[2] - footer_bbox[0]
        footer_height = footer_bbox[3] - footer_bbox[1]
        max_width = 0
        total_height = 0
        star_width, star_height = STAR_SIZE * 2, STAR_SIZE * 2
        for parsed_line in parsed_lines:
            line_width = 0
            max_height = 0
            for part_type, content in parsed_line:
                if part_type == 'star':
                    width = star_width
                    height = star_height
                else:
                    font = code_font if part_type == 'code' else content_font
                    bbox = temp_draw.textbbox((0, 0), content, font=font)
                    width = bbox[2] - bbox[0]
                    height = bbox[3] - bbox[1]
                    if part_type == 'code':
                        width += CODE_STYLE['padding'][1] * 2
                        height += CODE_STYLE['padding'][0] * 2
                line_width += width
                max_height = max(max_height, height)
            max_width = max(max_width, line_width)
            total_height += max_height + LINE_SPACING
        total_width = max(max_width, title_width, footer_width) + 2 * PANEL_PADDING
        total_height = (2 * PANEL_PADDING + title_height + TITLE_SPACING + total_height + FOOTER_SPACING + footer_height)
        final_img = Image.new("RGBA", (total_width, total_height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(final_img)
        draw.rounded_rectangle([(0, 0), (total_width, total_height)], PANEL_RADIUS, fill=PANEL_COLOR)
        title_x = (total_width - title_width) // 2
        draw.text((title_x, PANEL_PADDING), TITLE_TEXT, font=title_font, fill=TITLE_COLOR)
        x = PANEL_PADDING
        y = PANEL_PADDING + title_height + TITLE_SPACING
        for parsed_line in parsed_lines:
            current_x = x
            max_height = 0
            for part_type, content in parsed_line:
                if part_type == 'star':
                    star_w, star_h = self.draw_star(draw, current_x, y)
                    current_x += star_w
                    max_height = max(max_height, star_h)
                elif part_type == 'code':
                    pad_y, pad_x = CODE_STYLE['padding']
                    bbox = draw.textbbox((0, 0), content, font=code_font)
                    text_width = bbox[2]
                    text_height = bbox[3] - bbox[1]
                    bg_x2 = current_x + text_width + pad_x * 2
                    bg_y2 = y + text_height + pad_y * 2
                    draw.rounded_rectangle(
                        [(current_x, y), (bg_x2, bg_y2)],
                        CODE_STYLE['border_radius'],
                        fill=CODE_STYLE['bg_color']
                    )
                    draw.text((current_x + pad_x, y + pad_y), content, font=code_font, fill=(0, 0, 0))
                    current_x = bg_x2
                    max_height = max(max_height, bg_y2 - y)
                else:
                    color = (200, 30, 30) if part_type == 'note' else (0, 0, 0)
                    bbox = draw.textbbox((0, 0), content, font=content_font)
                    text_width = bbox[2] - bbox[0]
                    text_height = bbox[3] - bbox[1]
                    draw.text((current_x, y), content, font=content_font, fill=color)
                    current_x += text_width
                    max_height = max(max_height, text_height)
            y += max_height + LINE_SPACING
        footer_x = (total_width - footer_width) // 2
        draw.text((footer_x, y + FOOTER_SPACING), FOOTER_TEXT, font=footer_font, fill=FOOTER_COLOR)
        final_img.convert("RGB").save(OUTPUT_PATH, quality=95)
        LOG.info(f"图片已生成: {OUTPUT_PATH} ({total_width}x{total_height})")
        try:
            if hasattr(msg, "group_id"):
                await self.api.post_group_msg(msg.group_id, rtf=MessageChain(BotImage(OUTPUT_PATH)))
            else:
                await self.api.post_private_msg(msg.sender.user_id, rtf=MessageChain(BotImage(OUTPUT_PATH)))
        except Exception as e:
            LOG.error(f"图片发送失败: {str(e)}")
            await msg.reply(text="成绩卡片生成失败，请稍后再试")

    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")
