from ncatbot.plugin import BasePlugin
from ncatbot.core import MessageChain
from ncatbot.core import Image as BotImage
from ncatbot.core.event import BaseMessageEvent
from ncatbot.utils import get_log
import os
import sqlite3
import json 
import glob
from datetime import datetime
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import __main__

LOG = get_log("RecentPlay")    
class RecentPlay(BasePlugin):
    name = "RecentPlay"
    version = "1.0.0"
    author = "SweelLong"
    description = "显示最近游玩的曲目信息"

    def get_font(self, size, allow_utf8=False, config=None):
        if config is None:
            # 兼容旧代码
            font_path = os.path.join("src", "Fonts", "DingTalk JinBuTi.ttf")
            font_utf8_path = os.path.join("src", "Fonts", "ShangguSans-Bold.ttf")
        else:
            font_path = os.path.join(config["path"]["fonts"], "DingTalk JinBuTi.ttf")
            font_utf8_path = os.path.join(config["path"]["fonts"], "ShangguSans-Bold.ttf")
        
        if allow_utf8:
            return ImageFont.truetype(font_utf8_path, size)
        return ImageFont.truetype(font_path, size)
    
    def load_image(self, path, size=None, alpha=True):
        img = Image.open(path)
        if alpha and img.mode != "RGBA":
            img = img.convert("RGBA")
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
            img = img.filter(ImageFilter.UnsharpMask(radius=0.5, percent=100, threshold=3))
        return img

    def load_processed_image(self, background, img_path, position, size):
        img = Image.open(img_path)
        if img.mode != "RGBA":
            img = img.convert("RGBA")
        if size:
            img = img.resize(size, Image.Resampling.LANCZOS)
            img = img.filter(ImageFilter.UnsharpMask(radius=0.3, percent=80, threshold=5))
            r, g, b, a = img.split()
            a = a.point(lambda x: 0 if x < 30 else 255)
            img = Image.merge("RGBA", (r, g, b, a))
        r, g, b, a = img.split()
        mask = a
        background.paste(img, position, mask)
        return background
    
    def draw_text(self, draw, pos, text, font, color):
        x, y = pos
        draw.text((x, y), text, font=font, fill=color)

    def draw_text_with_shadow(self, draw, pos, text, font, main_color, shadow_color, shadow_offset=(2, 2)):
        x, y = pos
        draw.text((x + shadow_offset[0], y + shadow_offset[1]), text, font=font, fill=shadow_color)
        draw.text((x, y), text, font=font, fill=main_color)

    def draw_text_with_purple_border(self, draw, position, text, font, text_color=(255, 255, 255), border_color=(128, 0, 128)):
        x, y = position
        draw.text((x-1, y), text, font=font, fill=border_color)
        draw.text((x+1, y), text, font=font, fill=border_color)
        draw.text((x, y-1), text, font=font, fill=border_color)
        draw.text((x, y+1), text, font=font, fill=border_color)
        draw.text((x, y), text, font=font, fill=text_color)

    def get_diff_text(self, diff):
        if diff == 0:
            return "Past"
        elif diff == 1:
            return "Present"
        elif diff == 2:
            return "Future"
        elif diff == 3:
            return "Beyond"
        elif diff == 4:
            return "Eternal"

    def get_diff_small_text(self, diff):
        if diff == 0:
            return "rating_pst"
        elif diff == 1:
            return "rating_prs"
        elif diff == 2:
            return "rating_ftr"
        elif diff == 3:
            return "rating_byn"
        elif diff == 4:
            return "rating_etr"

    def format_score(self, score: int) -> str:
        s = str(score)[::-1]
        if len(s) <= 8:
            s = s.ljust(8, "0")
        return "'".join([s[i:i+3] for i in range(0, len(s), 3)])[::-1] or "0"

    def get_grade(self, score: int) -> str:
        if score >= 9900000:
            return "EX+"
        elif score >= 9800000:
            return "EX"
        elif score >= 9500000:
            return "AA"
        elif score >= 9200000:
            return "A"
        elif score >= 8900000:
            return "B"
        elif score >= 8600000:
            return "C"
        else:
            return "D"
        
    def get_illustration_path(self, song_id, config=None):
        if config is None:
            null_path = os.path.join("src", "random.jpg")
            path = "src/illustrations"
        else:
            null_path = os.path.join(config["path"]["src"], "random.jpg")
            path = config["path"]["illustrations"]
        if os.path.exists(os.path.join(path, "dl_" + song_id)):
            jacket_path = glob.glob(os.path.join(path, "dl_" + song_id, "*.[jJ][pP][gG]"))
            if jacket_path:
                return jacket_path[0]
        elif os.path.exists(os.path.join(path, song_id)):
            jacket_path = glob.glob(os.path.join(path, song_id, "*.[jJ][pP][gG]"))
            if jacket_path:
                return jacket_path[0]
        return null_path

    def get_rating_box_img(self, rating_ptt: str) -> str:
        rating_value = float(rating_ptt)
        if rating_value <= 3.49:
            return "rating_0.png"
        elif rating_value <= 6.99:
            return "rating_1.png"
        elif rating_value <= 9.99:
            return "rating_2.png"
        elif rating_value <= 10.99:
            return "rating_3.png"
        elif rating_value <= 11.99:
            return "rating_4.png"
        elif rating_value <= 12.49:
            return "rating_5.png"
        elif rating_value <= 12.99:
            return "rating_6.png"
        else:
            return "rating_7.png"

    def get_clear_type(self, clear_type: int) -> str:
        if clear_type == 0:
            return "clear_fail.png"
        elif clear_type == 1:
            return "clear_normal.png"
        elif clear_type == 2:
            return "clear_full.png"
        elif clear_type == 3:
            return "clear_pure.png"
        elif clear_type == 6:
            return "clear_pure.png"
        else:
            return "clear_normal.png"
        
    @__main__.arcaea_group.command("recent", ["最近"])
    async def recent(self, msg: BaseMessageEvent):
        # 读取配置文件
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        # 设置路径
        IMG_PATH = os.path.join(config["path"]["src"], "recent_play")  
        SLST_PATH = config["path"]["songlist"]
        OUTPUT_PATH = os.path.join(config["path"]["saves"], "RecentPlay.png")
        
        qq_id = str(msg.sender.user_id)
        
        # 连接数据库
        with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            c.execute("""SELECT * FROM 
                           (
                            SELECT *, ROW_NUMBER() OVER(ORDER BY rating_ptt DESC) AS rank FROM 
                            user 
                            NATURAL JOIN 
                            (SELECT song_id, name song_name, rating_pst, rating_prs, rating_ftr, rating_byn, rating_etr FROM chart)
                           ) WHERE email = ? 
                           ORDER BY rank;""", (qq_id + "@qq.com",))
            info = c.fetchone()
            if not info:
                LOG.error("玩家不存在")
                await msg.reply("玩家不存在")
                return
        player_name = info["name"]
        hash_number = str(info["rank"])
        potential = str(info["rating_ptt"] / 100)
        diff = info["difficulty"]
        difficulty = self.get_diff_text(diff)
        song_name = info["song_name"]
        artist = "UNKNOWN"
        constant = "？"
        max_recall = str(datetime.fromtimestamp(int(info["time_played"]) / 1000).strftime("%Y-%m-%d %H:%M:%S"))
        hp_value = str(info["health"])
        score_current = self.format_score(info["score"])
        score_pb = str(round(info[self.get_diff_small_text(diff)] / 10, 1)) + " > "
        score_diff = str(round(info["rating"], 5))
        grade = self.get_grade(info["score"])
        pure = str(info["shiny_perfect_count"])
        pure_add = f"({info["shiny_perfect_count"] - info["perfect_count"]})"
        far = str(info["near_count"])
        lost = str(info["miss_count"])
        this_illustration_path = self.get_illustration_path(info["song_id"], config)
        rating_box_img = self.get_rating_box_img(info["rating_ptt"] / 100)
        clear_type_imgge = self.get_clear_type(info["clear_type"])
        avatar_image = str(info["character_id"]) + ("u_icon.png" if not info["is_char_uncapped_override"] and info["is_char_uncapped"] else "_icon.png")
        character_imgae = str(info["character_id"]) + ("u.png" if not info["is_char_uncapped_override"] and info["is_char_uncapped"] else ".png")
        with open(SLST_PATH, "r", encoding="utf-8") as f:
            json_data = json.load(f)["songs"]
        jacketDesigner = "UNKNOWN"
        chartDesigner = "UNKNOWN"
        for song in json_data:
            if song["id"] == info["song_id"]:
                if song_name == "UNKNOWN":
                    song_name = song["title_localized"]["en"]
                artist = song["artist"]
                this_diff = song["difficulties"]
                for this in this_diff:
                    if this["ratingClass"] == diff:
                        constant = (str(this["rating"]) + ("+" if this.get("ratingPlus", False) else ""))
                        jacketDesigner = this.get("jacketDesigner", "")
                        chartDesigner = this.get("chartDesigner", "")
                        break
                break
        background = self.load_image(os.path.join(IMG_PATH, "bg.png"), size=(1440, 900))
        main_banner = self.load_image(os.path.join(IMG_PATH, "res_banner.png"), size=(1440, 700))
        background.paste(main_banner, (0, 100), main_banner)
        bg_w = background.size[0]
        draw = ImageDraw.Draw(background)
        character = self.load_image(os.path.join(config["path"]["src"], "char", "1080", character_imgae))
        target_scale = 0.8
        original_width, original_height = character.size
        cut_height = int (original_height * 0.8)
        top = (original_height - cut_height) // 2
        bottom = top + cut_height
        cropped_character = character.crop((0, top, original_width, bottom))
        resized_width = int(cropped_character.width * target_scale)
        resized_height = int(cropped_character.height * target_scale)
        resized_character = cropped_character.resize((resized_width, resized_height),resample=Image.Resampling.LANCZOS)
        background.paste(resized_character, (bg_w // 3, 80), resized_character)
        top_bar_bg = self.load_image(os.path.join(IMG_PATH, "top_bar_bg.png"))
        top_bar_right = self.load_image(os.path.join(IMG_PATH, "top_bar_bg_right.png"))
        background.paste(top_bar_bg, (0, 0), top_bar_bg)
        background.paste(top_bar_right, (bg_w - top_bar_right.width, 0), top_bar_right)
        course_banner = self.load_image(os.path.join(IMG_PATH, "26.png"), size=(350, top_bar_bg.height - 20))
        background.paste(course_banner, (400, 0), course_banner)
        self.draw_text_with_shadow(
            draw, (550 - len(player_name) // 2 * 15, 5), player_name, self.get_font(30, config=config), 
            (255, 255, 255), (0, 0, 0, 128)
        )
        hash_mark_box = self.load_image(os.path.join(IMG_PATH, "usercell_shape_bg.png"), size=(220, 165))
        background.paste(hash_mark_box, (653, -53), hash_mark_box)
        avatar_icon = self.load_image(os.path.join(config["path"]["src"], "char", avatar_image), size=(110, 110))
        background.paste(avatar_icon, (680, -25), avatar_icon)
        hash_mark = self.load_image(os.path.join(IMG_PATH, "hash.png"), size=(15, 15))
        background.paste(hash_mark, (785, 3), hash_mark)
        self.draw_text_with_shadow(
            draw, (798, -2), hash_number, self.get_font(20, config=config), 
            (255, 255, 255), (0, 0, 0, 128)
        )
        self.draw_text_with_shadow(
            draw, (20, 4), "© SweelLong", self.get_font(30, config=config), 
            (0, 0, 0), (255, 255, 255, 180)
        )
        fragment_bg = self.load_image(os.path.join(IMG_PATH, "frag_diamond_topplus.png"), size=(115, top_bar_bg.height - 20))
        memory_bg = self.load_image(os.path.join(IMG_PATH, "memory_diamond.png"), size=(115, top_bar_bg.height - 20))
        background.paste(fragment_bg, (1050, 0), fragment_bg)
        self.draw_text_with_shadow(
            draw, (1100, 15), "-", self.get_font(22, config=config), 
            (255, 255, 255), (0, 0, 0, 128)
        )
        self.draw_text_with_shadow(
            draw, (990, 10), "残片", self.get_font(22, config=config), 
            (0, 0, 0), (255, 255, 255)
        )
        background.paste(memory_bg, (1300, 0), memory_bg)
        self.draw_text_with_shadow(
            draw, (1350, 15), "-", self.get_font(22, config=config), 
            (173, 216, 230), (0, 0, 0, 128)
        )
        self.draw_text_with_shadow(
            draw, (1200, 10), "记忆源点", self.get_font(22, config=config), 
            (0, 0, 0), (255, 255, 255)
        )
        self.draw_text_with_shadow(
            draw, (25, 120), "最近游玩记录", self.get_font(30, True, config=config), 
            (255, 255, 255), (0, 0, 0, 180)
        )
        self.draw_text_with_shadow(
            draw, (25, 150), "画师：" + jacketDesigner, self.get_font(30, True, config=config), 
            (255, 255, 255), (0, 0, 0, 180)
        )
        self.draw_text_with_shadow(
            draw, (25, 180), "谱师：" + chartDesigner, self.get_font(30, True, config=config), 
            (255, 255, 255), (0, 0, 0, 180)
        )
        font = self.get_font(48, True, config=config)
        text_width = font.getlength(song_name)
        x_position = (background.width - text_width) // 2
        self.draw_text_with_shadow(
            draw, (x_position, 120), song_name, font, 
            (255, 255, 255), (0, 0, 0, 180)
        )
        font = self.get_font(30, True, config=config)
        text_width = font.getlength(song_name)
        x_position = (background.width - text_width) // 2
        self.draw_text_with_shadow(
            draw, (x_position, 180), artist, font, 
            (255, 255, 255), (0, 0, 0, 180)
        )
        potential_border = self.load_image(os.path.join(config["path"]["src"], "rating", rating_box_img), size=(65, 65))
        border_x, border_y = (750, 30)
        border_width = potential_border.size[0]
        background.paste(potential_border, (border_x, border_y), potential_border)
        font = self.get_font(21, config=config)
        text_width = font.getlength(potential)
        center_x = border_x + (border_width - text_width) // 2
        self.draw_text_with_shadow(
            draw, (center_x, 48), potential, font, 
            (255, 255, 255), (0, 0, 0, 128), shadow_offset=(-2, -2)
        )
        background = self.load_processed_image(background, os.path.join(IMG_PATH, "back.png"), (0, 826), (240, 76))
        self.draw_text(
            draw, (80, 836), "返回", self.get_font(25, config=config), 
            (118, 126, 140)
        )
        background = self.load_processed_image(background, os.path.join(IMG_PATH, "mid_button.png"), (625, 826), (240, 76))
        self.draw_text(
            draw, (718, 836), "分享", self.get_font(25, config=config), 
            (118, 126, 140)
        )
        background = self.load_processed_image(background, os.path.join(IMG_PATH, "retry.png"), (1200, 826), (240, 76))
        self.draw_text(
            draw, (1310, 836), "重试", self.get_font(25, config=config), 
            (118, 126, 140)
        )
        illustration = self.load_image(os.path.join(this_illustration_path), size=(400, 400))
        background.paste(illustration, (50, 350), illustration)
        max_recall_bg = self.load_image(os.path.join(IMG_PATH, f"max-recall-{difficulty.lower()}.png"), size=(300, 84))
        background.paste(max_recall_bg, (10, 250), max_recall_bg)
        draw.text((50, 270), constant, font=self.get_font(33, config=config), 
                fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))  
        diff_font = self.get_font(23, config=config)
        bg_width = 300  
        text_width = diff_font.getlength(difficulty)
        center_x = 10 + (bg_width - text_width) // 2  
        self.draw_text_with_purple_border(
            draw, (center_x, 265), difficulty, diff_font
        )
        self.draw_text_with_purple_border(
            draw, (120, 295), "TIME", self.get_font(22, config=config)
        )
        self.draw_text_with_purple_border(
            draw, (180, 295), max_recall, self.get_font(22, config=config)
        )
        clear_type = self.load_image(os.path.join(config["path"]["src"], "clear_type", clear_type_imgge), size=(600, 65))
        background.paste(clear_type, (420, 270), clear_type)
        hp_base = self.load_image(os.path.join(IMG_PATH, "hp_base.png"), size=(32, 400))
        try:
            hp_bar = self.load_image(os.path.join(IMG_PATH, "hp_bar_clear.png"), size=(32, int(int(hp_value) * 4)))
        except:
            hp_bar = self.load_image(os.path.join(IMG_PATH, "hp_bar_clear.png"), size=(32, 4))
        hp_grid = self.load_image(os.path.join(IMG_PATH, "hp_grid.png"), size=(32, 400))
        background.paste(hp_base, (450, 350), hp_base)
        background.paste(hp_bar, (450, 350 + 400 - int(int(hp_value) * 4)), hp_bar)
        background.paste(hp_grid, (450, 350), hp_grid)
        self.draw_text_with_shadow(
            draw, (495 - len(hp_value) * 15, 345), hp_value, self.get_font(16, config=config), 
            (255, 255, 255), (0, 0, 0, 128)
        )
        score_panel = self.load_image(os.path.join(IMG_PATH, "res_rating.png"), size=(525, 299))
        background.paste(score_panel, (482, 331), score_panel)
        self.draw_text_with_shadow(
            draw, (640 - len(score_current) * 7, 365), score_current, self.get_font(60, config=config), 
            (255, 255, 255), (0, 0, 0)
        )
        self.draw_text_with_shadow(
            draw, (705 - len(score_pb) * 3, 453), score_pb, self.get_font(25, config=config), 
            (255, 255, 255), (0, 0, 0)
        )
        self.draw_text_with_shadow(
            draw, (785 - len(score_diff) * 3, 453), score_diff, self.get_font(25, config=config), 
            (255, 255, 255), (0, 0, 0)
        )
        grade_img = self.load_image(os.path.join(config["path"]["src"], "grade", f"{grade}.png"), size=(180, 180))
        background.paste(grade_img, (620, 460), grade_img)
        pure_icon = self.load_image(os.path.join(IMG_PATH, "pure-count.png"), size=(180, 33))
        background.paste(pure_icon, (600, 625), pure_icon)
        self.draw_text_with_shadow(
            draw, (720, 625), pure, self.get_font(20, config=config), 
            (255, 255, 255), (0, 0, 0)
        )
        self.draw_text_with_shadow(
            draw, (785, 625), pure_add, self.get_font(20, config=config), 
            (255, 255, 255), (0, 0, 0)
        )
        self.draw_text_with_shadow(
            draw, (635, 625), "PURE", self.get_font(22, config=config), 
            (255, 255, 255), (0, 0, 0)
        )
        far_icon = self.load_image(os.path.join(IMG_PATH, "far-count.png"), size=(180, 33))
        background.paste(far_icon, (600, 665), far_icon)
        self.draw_text_with_shadow(
            draw, (720, 665), far, self.get_font(20, config=config), 
            (255, 255, 255), (0, 0, 0)
        )
        self.draw_text_with_shadow(
            draw, (640, 665), "FAR", self.get_font(22, config=config), 
            (255, 255, 255), (0, 0, 0)
        )
        lost_icon = self.load_image(os.path.join(IMG_PATH, "lost-count.png"), size=(180, 33))
        background.paste(lost_icon, (600, 705), lost_icon)
        self.draw_text_with_shadow(
            draw, (720, 705), lost, self.get_font(20, config=config), 
            (255, 255, 255), (0, 0, 0)
        )
        self.draw_text_with_shadow(
            draw, (635, 705), "LOST", self.get_font(22, config=config), 
            (255, 255, 255), (0, 0, 0)
        )
        background.convert("RGB").save(OUTPUT_PATH, quality=95)
        LOG.info(f"✅ RecentPlay图片已保存至: {OUTPUT_PATH}")
        try:
            if hasattr(msg, "group_id"):
                await self.api.post_group_msg(msg.group_id, rtf=MessageChain(BotImage(OUTPUT_PATH)))
            else:
                await self.api.post_private_msg(msg.sender.user_id, rtf=MessageChain(BotImage(OUTPUT_PATH)))
        except Exception as e:
            LOG.error(f"图片生成失败: {str(e)}")
            await msg.reply(text="成绩卡片生成失败，请稍后再试")
    
    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")