from ncatbot.plugin import BasePlugin
from ncatbot.core.message import BaseMessage
from ncatbot.core import MessageChain
from ncatbot.core import Image as BotImage
from ncatbot.utils import get_log
import os
import sqlite3
import json 
from PIL import Image as Image, ImageDraw, ImageFont, ImageFilter
import glob
import datetime
import math
from typing import List, Dict
import __main__

LOG = get_log("B30")
TARGET_SIZE = (1152, 2304)
CARD_WIDTH = 250
CARD_HEIGHT = 145
CARDS_PER_ROW = 4
CARD_GAP = 24
TITLE_PADDING = 25
TEXT_PADDING = 10

class B30(BasePlugin):
    name = "B30"
    version = "1.0.0" 
    author = "SweelLong"
    description = "Best 30 查分插件"

    def get_best_font(size: int, planB: bool = False) -> ImageFont.FreeTypeFont:
        if planB:
            return ImageFont.truetype(SPECIFIC_FONT[1], size)
        return ImageFont.truetype(SPECIFIC_FONT[0], size)
    
    def load_image(path: str, size: tuple = None, keep_aspect: bool = True) -> Image.Image:
        if not os.path.exists(path):
            return None
        try:
            img = Image.open(path).convert("RGBA")
            if size:
                if keep_aspect:
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                else:
                    img = img.resize(size, Image.Resampling.LANCZOS)
            return img
        except Exception as e:
            LOG.error(f"加载失败: {path} → {e}")
            return None
        
    def format_score(score: int) -> str:
        s = str(score)[::-1]
        return "'".join([s[i:i+3] for i in range(0, len(s), 3)])[::-1] or "0"
    
    def get_rating_box_img(rating_ptt: str) -> str:
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
    
    def get_difficulty_str(self, difficulty: int) -> str:
        if difficulty == 0:
            self.DIFF_COLOR = (45, 183, 218) 
            return "PAST"
        elif difficulty == 1:
            self.DIFF_COLOR = (46, 204, 113)
            return "PRESENT"
        elif difficulty == 2:
            self.DIFF_COLOR = (231, 76, 60) 
            return "FUTURE"
        elif difficulty == 3:
            self.DIFF_COLOR = (192, 57, 43) 
            return "BEYOND"
        elif difficulty == 4:
            self.DIFF_COLOR = (155, 89, 182) 
            return "ETERNAL"
        
    def get_difficulty_rating(difficulty: int) -> str:
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
        
    def get_clear_type(clear_type: int) -> str:
        if clear_type == 0:
            return "fail.png"
        elif clear_type == 1:
            return "normal.png"
        elif clear_type == 2:
            return "full.png"
        elif clear_type == 3:
            return "pure.png"
        elif clear_type == 4:
            return "easy.png"
        elif clear_type == 5:
            return "hard.png"
        elif clear_type == 6:
            return "pure.png"
        
    def draw_user_info(draw: ImageDraw.ImageDraw, user: Dict, bg: Image.Image, y: int, type) -> int:
        course_bg = B30.load_image(COURSE_PATH, (400, 60))
        if course_bg:
            bg.paste(course_bg, (145, y + 50), course_bg)
        draw.text((200, y + 60), user["name"], font=B30.get_best_font(30), fill=(255, 255, 255))
        avatar = B30.load_image(os.path.join(AVATAR_FOLDER, user["avatar"]), (150, 150))
        if avatar:
            bg.paste(avatar, (30, y + 10), avatar)
        RATING_BOX = os.path.join(RATING_FOLDER, B30.get_rating_box_img(user['rating_ptt']))
        rating_box = B30.load_image(RATING_BOX, (75, 75))
        if rating_box:
            rating_box_x = 120
            rating_box_y = y + 90
            bg.paste(rating_box, (rating_box_x, rating_box_y), rating_box)
            level_text = user["rating_ptt"]
            font_level = B30.get_best_font(24)
            text_bbox = draw.textbbox((0, 0), level_text, font=font_level)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = rating_box_x + (75 - text_width) // 2
            text_y = rating_box_y + (75 - text_height) // 2 - 7
            stroke_color = (150, 50, 200)
            main_color = (255, 255, 255)
            offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
            for ox, oy in offsets:
                draw.text((text_x + ox, text_y + oy), level_text, font=font_level, fill=stroke_color)
            draw.text((text_x, text_y), level_text, font=font_level, fill=main_color)
        rank = user["rank"]
        font_level = B30.get_best_font(30) 
        stroke_color = (197, 41, 7 )
        main_color = (255, 255, 255)
        offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
        for ox, oy in offsets:
            draw.text((135 + ox, y + 15 + oy), rank, font=font_level, fill=stroke_color)
        draw.text((135, y + 15), rank, font=font_level, fill=main_color)
        draw.text((200, y + 120), f"ID: {user['id']}", font=B30.get_best_font(26), fill=(255, 255, 255))
        ptt_x = 900
        if type == 0:
            draw.text((ptt_x, y + 20), f"Max : {user['max_ptt']}", font=B30.get_best_font(36), fill=(255, 255, 255))
            draw.text((ptt_x, y + 60), f"B30 : {user['b30_ptt']}", font=B30.get_best_font(36), fill=(255, 255, 255))
            draw.text((ptt_x, y + 100), f"R10 : {user['r10_ptt']}", font=B30.get_best_font(36), fill=(255, 255, 255))
        if type == 1:
            draw.text((ptt_x, y + 20), f"PMAX : {user['max_ptt']}", font=B30.get_best_font(36), fill=(255, 255, 255))
            draw.text((ptt_x, y + 60), f"P30 : {user['b30_ptt']}", font=B30.get_best_font(36), fill=(255, 255, 255))
            draw.text((ptt_x, y + 100), f"PR10 : {user['r10_ptt']}", font=B30.get_best_font(36), fill=(255, 255, 255))
        if type == 2:
            ptt_x -= 100
            draw.text((ptt_x, y + 20), f"理论潜力值 : {user['max_ptt']}", font=B30.get_best_font(36), fill=(255, 255, 255))
            draw.text((ptt_x, y + 60), f"最佳理论30首 : {user['b30_ptt']}", font=B30.get_best_font(36), fill=(255, 255, 255))
            draw.text((ptt_x, y + 100), f"最近理论10首 : {user['r10_ptt']}", font=B30.get_best_font(36), fill=(255, 255, 255))
        return y + 180
    
    def draw_song_section(draw: ImageDraw.ImageDraw, bg: Image.Image, songs: List[Dict], title_path: str, start_y: int) -> int:
        title_img = B30.load_image(title_path, (250, 50))
        if title_img:
            title_x = (TARGET_SIZE[0] - title_img.width) // 2
            bg.paste(title_img, (title_x, start_y), title_img)
            start_y += title_img.height + TITLE_PADDING
        song_count = len(songs)
        rows = math.ceil(song_count / CARDS_PER_ROW)
        total_row_width = CARDS_PER_ROW * CARD_WIDTH + (CARDS_PER_ROW - 1) * CARD_GAP
        start_x = (TARGET_SIZE[0] - total_row_width) // 2
        for row in range(rows):
            for col in range(CARDS_PER_ROW):
                idx = row * CARDS_PER_ROW + col
                if idx >= song_count:
                    break
                song = songs[idx]
                x = start_x + col * (CARD_WIDTH + CARD_GAP)
                y = start_y + row * (CARD_HEIGHT + CARD_GAP)
                card_bg = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
                card_draw = ImageDraw.Draw(card_bg)
                card_draw.rounded_rectangle([(0, 0), (CARD_WIDTH, CARD_HEIGHT)], radius=20, fill=(255, 255, 255, 128))
                bg.paste(card_bg, (x, y), card_bg)
                illus_path = song["illustration_path"]
                if not os.path.exists(illus_path):
                    illus_path = os.path.join(SRC_FOLDER, "random.jpg")
                illustration = B30.load_image(illus_path, (115, 115), keep_aspect=False)
                if illustration:
                    bg.paste(illustration, (x + 10, y + 10), illustration)
                y_text = y + CARD_HEIGHT - 25
                song_name = song["song_name"][:22] + "..." if len(song["song_name"]) > 22 else song["song_name"]
                draw.text((x + TEXT_PADDING, y_text), song_name, font=B30.get_best_font(16, True), fill=(0, 0, 0))
                y_text += 20
                level_text = song['order']
                font_level = B30.get_best_font(16) 
                stroke_color = (150, 50, 200)
                main_color = (255, 255, 255)
                offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
                for ox, oy in offsets:
                    draw.text((x + TEXT_PADDING + CARD_WIDTH - 50 + ox, y_text - CARD_HEIGHT + 15 + oy), level_text, font=font_level, fill=stroke_color)
                draw.text((x + TEXT_PADDING + CARD_WIDTH - 50, y_text - CARD_HEIGHT + 15), level_text, font=font_level, fill=main_color)
                draw.text((x + TEXT_PADDING + 120, y_text - CARD_HEIGHT + 20), song["rating"], font=B30.get_best_font(14), fill=(255, 107, 107))
                y_text += 20
                draw.text((x + TEXT_PADDING + 120, y_text - CARD_HEIGHT + 20), B30.format_score(song["score"]), font=B30.get_best_font(22), fill=(255, 107, 107))
                y_text += 30
                draw.text((x + TEXT_PADDING + 120, y_text - CARD_HEIGHT + 20), song["difficulty"] + f"[{song['chart_const']}]", font=B30.get_best_font(13), fill=song['diff_color'])
                y_text += 20
                draw.text((x + TEXT_PADDING + 120, y_text - CARD_HEIGHT + 20), f"P/{song['pm_num']}({song['delta_pm_num']})", font=B30.get_best_font(14), fill=(213, 0, 255))
                y_text += 20
                draw.text((x + TEXT_PADDING + 120, y_text - CARD_HEIGHT + 20), f"F/{song['far_num']}", font=B30.get_best_font(14), fill=(255, 211, 0 ))
                draw.text((x + TEXT_PADDING + 120 + 40, y_text - CARD_HEIGHT + 20), f"L/{song['lost_num']}", font=B30.get_best_font(14), fill=(152, 4, 4))
                rating_img = B30.load_image(os.path.join(CLEAR_TYPE_FOLDER, song['clear_type']), (50, 50))
                if rating_img:
                    bg.paste(rating_img, (x + CARD_WIDTH - 50, y + CARD_HEIGHT - 45), rating_img)
        
        return start_y + rows * (CARD_HEIGHT + CARD_GAP) + TITLE_PADDING

    def generate_rating_card(user: Dict, song_data: Dict, type) -> None:
        bg = B30.load_image(BG_PATH, size=TARGET_SIZE, keep_aspect=False).filter(ImageFilter.GaussianBlur(radius=5))
        if not bg:
            bg = Image.new("RGB", TARGET_SIZE, (255, 255, 255))
        draw = ImageDraw.Draw(bg)
        current_y = B30.draw_user_info(draw, user, bg, y=20, type=type)
        current_y = B30.draw_song_section(draw, bg, song_data["b30"], BEST30_TITLE, current_y)
        current_y = B30.draw_song_section(draw, bg, song_data["overflow"], OVERFLOW_TITLE, current_y)
        now = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        draw.text(
            (TARGET_SIZE[0] // 2, TARGET_SIZE[1] - 40),
            f"The rating card is generated by Suo Yuki. Generate at {now}. \n Copyright © 2025 SweelLong All rights reserved. Only for player in Arcase.",
            font=B30.get_best_font(16),
            fill=(255, 255, 255),
            anchor="mm"
        )
        bg.convert("RGB").save(OUTPUT_PATH, quality=95)
        LOG.info(f"✅ B30图片已保存至: {OUTPUT_PATH}")

    async def b30_common_tool(self, msg: BaseMessage, type):
        QQ_ID = str(msg.user_id)
        email = QQ_ID + "@qq.com"
        tmp_data = dict()
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        with sqlite3.connect(config["database"]["server"]) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("""
                SELECT * FROM (SELECT
                           user_id, 
                           name, 
                           user_code,
                           rating_ptt, 
                           email, 
                           character_id,
                           is_char_uncapped,
                           is_char_uncapped_override,
                           RANK() OVER (ORDER BY rating_ptt DESC) AS rank
                           FROM user
                           ) WHERE email = ?
                           """, (email,))
            info = c.fetchone()
            if not info:
                return await msg.reply("请先注册或绑定游戏账号！")
            tmp_data = dict(info)
            user_id = tmp_data["user_id"]
            avatar_path = str(tmp_data["character_id"]) + ("u_icon.png" if not tmp_data["is_char_uncapped_override"] and tmp_data["is_char_uncapped"] else "_icon.png")
            if not os.path.exists(os.path.join(AVATAR_FOLDER, avatar_path)):
                avatar_path = "unknown_icon.png"
            user_info = {
                "id": tmp_data["user_code"],
                "name": tmp_data["name"],
                "rank": f"# {tmp_data['rank']}",
                "avatar": avatar_path,
                "rating_ptt": str(round(tmp_data["rating_ptt"] / 100, 2)),
            }
            song_jacket_path = {}
            song_difficulties_info = {}
            slst_path = config["path"]["songlist"]
            with open(slst_path, "r", encoding="utf-8") as f:
                slst_data = json.load(f)["songs"]
                for song in slst_data:
                    difDict = dict()
                    for diff in song["difficulties"]:
                        difDict[diff["ratingClass"]] = (diff["rating"], diff.get("ratingPlus", False))
                    song_difficulties_info[song["id"]] = difDict
                    path = config["path"]["illustrations"]
                    if os.path.exists(os.path.join(path, "dl_" + song["id"])):
                        jacket_path = glob.glob(os.path.join(path, "dl_" + song["id"], "*.[jJ][pP][gG]"))
                        if jacket_path:
                            song_jacket_path[song["id"]] = jacket_path[0]
                    elif os.path.exists(os.path.join(path, song["id"])):
                        jacket_path = glob.glob(os.path.join(path, song["id"], "*.[jJ][pP][gG]"))
                        if jacket_path:
                            song_jacket_path[song["id"]] = jacket_path[0]
            b30 = []
            b30sum = 0
            if type == 0:
                c.execute("""
                            SELECT song_id, difficulty, rating, MAX(score) score, name, best_clear_type, perfect_count, shiny_perfect_count, near_count, miss_count, rating_pst, rating_prs, rating_ftr, rating_byn, rating_etr
                            FROM best_score NATURAL JOIN chart
                            WHERE user_id = ?
                            GROUP BY song_id, difficulty
                            ORDER BY rating DESC 
                            LIMIT 30
                        """, (user_id,))
            elif type == 1:
                c.execute("""
                            SELECT song_id, difficulty, rating, MAX(score) score, name, best_clear_type, perfect_count, shiny_perfect_count, near_count, miss_count, rating_pst, rating_prs, rating_ftr, rating_byn, rating_etr
                            FROM best_score NATURAL JOIN chart
                            WHERE user_id = ? AND near_count=0 AND miss_count=0
                            GROUP BY song_id, difficulty
                            ORDER BY rating DESC 
                            LIMIT 30
                        """, (user_id,))
            elif type == 2:
                c.execute("""
                            SELECT song_id, difficulty, rating, MAX(score) score, name, best_clear_type, perfect_count, shiny_perfect_count, near_count, miss_count, rating_pst, rating_prs, rating_ftr, rating_byn, rating_etr
                            FROM best_score NATURAL JOIN chart
                            WHERE user_id = ? AND shiny_perfect_count=perfect_count AND near_count=0 AND miss_count=0
                            GROUP BY song_id, difficulty
                            ORDER BY rating DESC 
                            LIMIT 30
                        """, (user_id,))
            for idx, row in enumerate(c.fetchall()):
                tmp_data = dict(row)
                diffInfo = song_difficulties_info.get(tmp_data["song_id"], {}).get(tmp_data["difficulty"], (0, False))
                b30.append({
                    "order": f"# {idx + 1}",
                    "song_name": tmp_data["name"],
                    "difficulty": f"{B30.get_difficulty_str(self, tmp_data['difficulty'])} {diffInfo[0]}{'+' if diffInfo[1] else ''}",
                    "diff_color": self.DIFF_COLOR,
                    "clear_type": B30.get_clear_type(tmp_data["best_clear_type"]),
                    "score": tmp_data["score"],
                    "chart_const": round(float(tmp_data[B30.get_difficulty_rating(tmp_data['difficulty'])]) / 10, 1),
                    "rating": str(round(float(tmp_data["rating"]), 2)),
                    "pm_num": str(tmp_data["perfect_count"]),
                    "delta_pm_num": str(tmp_data["shiny_perfect_count"] - tmp_data["perfect_count"]),
                    "far_num": str(tmp_data["near_count"]),
                    "lost_num": str(tmp_data["miss_count"]),
                    "illustration_path": song_jacket_path.get(tmp_data["song_id"], "")
                })
                b30sum += float(tmp_data["rating"])
            overflow = []
            overflowsum = 0
            if type == 0:
                c.execute("""
                            SELECT song_id, difficulty, rating, MAX(score) score, name, clear_type, perfect_count, shiny_perfect_count, near_count, miss_count, rating_pst, rating_prs, rating_ftr, rating_byn, rating_etr
                            FROM recent30 NATURAL JOIN chart
                            WHERE user_id = ?
                            GROUP BY song_id, difficulty
                            ORDER BY rating DESC 
                            LIMIT 10
                        """, (user_id,))
            elif type == 1:
                c.execute("""
                            SELECT song_id, difficulty, rating, MAX(score) score, name, clear_type, perfect_count, shiny_perfect_count, near_count, miss_count, rating_pst, rating_prs, rating_ftr, rating_byn, rating_etr
                            FROM recent30 NATURAL JOIN chart
                            WHERE user_id = ? AND near_count=0 AND miss_count=0
                            GROUP BY song_id, difficulty
                            ORDER BY rating DESC 
                            LIMIT 10
                        """, (user_id,))
            elif type == 2:
                c.execute("""
                            SELECT song_id, difficulty, rating, MAX(score) score, name, clear_type, perfect_count, shiny_perfect_count, near_count, miss_count, rating_pst, rating_prs, rating_ftr, rating_byn, rating_etr
                            FROM recent30 NATURAL JOIN chart
                            WHERE user_id = ? AND shiny_perfect_count=perfect_count AND near_count=0 AND miss_count=0
                            GROUP BY song_id, difficulty
                            ORDER BY rating DESC 
                            LIMIT 10
                        """, (user_id,))
            for idx, row in enumerate(c.fetchall()):
                tmp_data = dict(row)
                diffInfo = song_difficulties_info.get(tmp_data["song_id"], {}).get(tmp_data["difficulty"], (0, False))
                overflow.append({
                    "order": f"# {idx + 1}",
                    "song_name": tmp_data["name"],
                    "difficulty": f"{B30.get_difficulty_str(self, tmp_data['difficulty'])} {diffInfo[0]}{'+' if diffInfo[1] else ''}",
                    "diff_color": self.DIFF_COLOR,
                    "clear_type": B30.get_clear_type(tmp_data["clear_type"]),
                    "score": tmp_data["score"],
                    "chart_const": round(float(tmp_data[B30.get_difficulty_rating(tmp_data['difficulty'])]) / 10, 1),
                    "rating": str(round(float(tmp_data["rating"]), 2)),
                    "pm_num": str(tmp_data["perfect_count"]),
                    "delta_pm_num": str(tmp_data["shiny_perfect_count"] - tmp_data["perfect_count"]),
                    "far_num": str(tmp_data["near_count"]),
                    "lost_num": str(tmp_data["miss_count"]),
                    "illustration_path": song_jacket_path.get(tmp_data["song_id"], "")
                })
                overflowsum += float(tmp_data["rating"])
            user_info["max_ptt"] = str(round((b30sum + overflowsum) / 40, 2))
            user_info["b30_ptt"] = str(round(b30sum / 30, 2))
            user_info["r10_ptt"] = str(round(overflowsum / 10, 2))
            B30.generate_rating_card(user_info, {"b30": b30, "overflow": overflow}, type=type)
            try:
                if hasattr(msg, "group_id"):
                    return await self.api.post_group_msg(msg.group_id, rtf=MessageChain(BotImage(OUTPUT_PATH)))
                else:
                    return await self.api.post_private_msg(msg.user_id, rtf=MessageChain(BotImage(OUTPUT_PATH)))
            except Exception as e:
                LOG.error(f"图片生成失败: {str(e)}")
                return await msg.reply(text="成绩卡片生成失败，请稍后再试")
            
    @__main__.arcaea_group.command("b30", ["ab30"])
    async def b30(self, msg: BaseMessage):
        return await B30.b30_common_tool(self, msg, type=0)
    
    @__main__.arcaea_group.command("p30", ["ap30"])
    async def p30(self, msg: BaseMessage):
        return await B30.b30_common_tool(self, msg, type=1)
    
    @__main__.arcaea_group.command("理30", ["a理30"])
    async def t30(self, msg: BaseMessage):
        return await B30.b30_common_tool(self, msg, type=2)
    
    async def on_load(self):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        global SRC_FOLDER, AVATAR_FOLDER, CLEAR_TYPE_FOLDER, RATING_FOLDER, BEST30_TITLE, OVERFLOW_TITLE, BG_PATH, COURSE_PATH, OUTPUT_PATH, SPECIFIC_FONT
        SRC_FOLDER = config["path"]["src"]
        AVATAR_FOLDER = os.path.join(config["path"]["src"], "char")
        CLEAR_TYPE_FOLDER = os.path.join(config["path"]["src"], "clear_type")
        RATING_FOLDER = os.path.join(config["path"]["src"], "rating")
        BEST30_TITLE = os.path.join(config["path"]["src"], "b30", "best30.png")
        OVERFLOW_TITLE = os.path.join(config["path"]["src"], "b30", "overflow.png")
        BG_PATH = os.path.join(config["path"]["src"], "b30", "bg.jpg")
        COURSE_PATH = os.path.join(config["path"]["src"], "b30", "26.png")
        OUTPUT_PATH = os.path.join(config["path"]["saves"], "B30.png")
        SPECIFIC_FONT = [
            os.path.join(config["path"]["fonts"], "DingTalk JinBuTi.ttf"),
            os.path.join(config["path"]["fonts"], "ShangguSans-Bold.ttf")
        ]
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")