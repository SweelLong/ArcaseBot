import datetime
import sqlite3
import os
import re
import math
import asyncio
import glob
import json
from typing import List, Tuple, Dict
from PIL import Image, ImageDraw, ImageFont
import ncatbot
from ncatbot.plugin import BasePlugin
from ncatbot.core.event import BaseMessageEvent
from ncatbot.utils import get_log
import __main__

LOG = get_log("Rating")
class Rating(BasePlugin):
    name = "Rating"
    version = "1.0.2"
    author = "FuLuzzX"
    description = "曲目定数查询插件，支持查询指定定数或定数范围的所有曲目，范围查询时按定数分段显示"

    @__main__.arcaea_group.command("rating", ["定数"])
    async def handle_rating_command(self, msg: BaseMessageEvent, pttl: str, pttr: str = "0"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        DATABASE_PATH = config["database"]["server"]
        ILLUSTRATION_PATH = [
            config["path"]["illustrations"]
        ]
        OUTPUT_PATH = os.path.join(config["path"]["saves"], "Rating.png")
        if pttr == "0":
            rating_arg = str(pttl)
            try:
                rating_float = float(rating_arg)
                rating_int = int(rating_float * 10)
                is_range = False
            except ValueError:
                return await msg.reply("定数转换失败，请检查输入！")
        else:
            start_arg, end_arg = str(pttl), str(pttr)
            try:
                start_float = float(start_arg)
                end_float = float(end_arg)
                if start_float > end_float:
                    start_float, end_float = end_float, start_float
                start_int = int(start_float * 10)
                end_int = int(end_float * 10)
                rating_float = (start_float, end_float)
                rating_int = (start_int, end_int)
                is_range = True
            except ValueError:
                return await msg.reply("定数范围转换失败，请检查输入！")
        if not os.path.exists(DATABASE_PATH):
            return await msg.reply(f"数据库文件不存在，请检查路径: {DATABASE_PATH}")
        try:
            loop = asyncio.get_running_loop()
            if is_range:
                records = await loop.run_in_executor(None, self.query_database_range, DATABASE_PATH, *rating_int)
            else:
                records = await loop.run_in_executor(None, self.query_database, DATABASE_PATH, rating_int)
            if not records:
                if is_range:
                    return await msg.reply(f"未找到定数在 {rating_float[0]:.1f} 到 {rating_float[1]:.1f} 之间的谱面")
                else:
                    return await msg.reply(f"未找到定数为 {rating_float:.1f} 的谱面")
            image = await loop.run_in_executor(None, self.create_image, records, rating_float if not is_range else rating_float, is_range, ILLUSTRATION_PATH, config)
            image.save(OUTPUT_PATH, format='PNG')
            reply_msg = ncatbot.core.MessageChain()
            reply_msg += ncatbot.core.Image(OUTPUT_PATH)
            if hasattr(msg, 'group_id'):
                return await self.api.post_group_msg(group_id=msg.group_id, rtf=reply_msg)
            else:
                return await self.api.post_private_msg(user_id=msg.sender.user_id, rtf=reply_msg)
        except Exception as e:
            LOG.error(f"处理定数查询时出错: {str(e)}")
            return await msg.reply(f"查询失败: {str(e)}")

    def query_database(self, database_path: str, rating_int: int) -> List[Tuple]:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
            SELECT song_id, name, 'ftr' as difficulty
            FROM chart
            WHERE rating_ftr = ?
            UNION ALL
            SELECT song_id, name, 'byn' as difficulty
            FROM chart
            WHERE rating_byn = ?
            UNION ALL
            SELECT song_id, name, 'etr' as difficulty
            FROM chart
            WHERE rating_etr = ?
            """, (rating_int, rating_int, rating_int))
            records = cursor.fetchall()
            if records:
                return records
            cursor.execute("""
            SELECT song_id, song_id as name, 'ftr' as difficulty
            FROM chart
            WHERE rating_ftr = ?
            UNION ALL
            SELECT song_id, song_id as name, 'byn' as difficulty
            FROM chart
            WHERE rating_byn = ?
            UNION ALL
            SELECT song_id, song_id as name, 'etr' as difficulty
            FROM chart
            WHERE rating_etr = ?
            """, (rating_int, rating_int, rating_int))
            return cursor.fetchall()
        finally:
            conn.close()

    def query_database_range(self, database_path: str, start_int: int, end_int: int) -> List[Tuple]:
        conn = sqlite3.connect(database_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
            SELECT song_id, name, 'ftr' as difficulty, rating_ftr
            FROM chart
            WHERE rating_ftr BETWEEN ? AND ?
            UNION ALL
            SELECT song_id, name, 'byn' as difficulty, rating_byn
            FROM chart
            WHERE rating_byn BETWEEN ? AND ?
            UNION ALL
            SELECT song_id, name, 'etr' as difficulty, rating_etr
            FROM chart
            WHERE rating_etr BETWEEN ? AND ?
            """, (start_int, end_int, start_int, end_int, start_int, end_int))
            records = cursor.fetchall()
            if records:
                return records
            cursor.execute("""
            SELECT song_id, song_id as name, 'ftr' as difficulty, rating_ftr
            FROM chart
            WHERE rating_ftr BETWEEN ? AND ?
            UNION ALL
            SELECT song_id, song_id as name, 'byn' as difficulty, rating_byn
            FROM chart
            WHERE rating_byn BETWEEN ? AND ?
            UNION ALL
            SELECT song_id, song_id as name, 'etr' as difficulty, rating_etr
            FROM chart
            WHERE rating_etr BETWEEN ? AND ?
            """, (start_int, end_int, start_int, end_int, start_int, end_int))
            return cursor.fetchall()
        finally:
            conn.close()

    def get_text_width(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
        try:
            return draw.textlength(text, font=font)
        except AttributeError:
            return draw.textsize(text, font=font)[0]

    def truncate_text(self, draw: ImageDraw.ImageDraw, text: str, max_width: int, font: ImageFont.FreeTypeFont) -> str:
        if not text:
            return ""
        text_width = self.get_text_width(draw, text, font)
        if text_width <= max_width:
            return text
        ellipsis = "..."
        ellipsis_width = self.get_text_width(draw, ellipsis, font)
        max_text_width = max_width - ellipsis_width
        truncated = text
        while truncated and self.get_text_width(draw, truncated, font) > max_text_width:
            truncated = truncated[:-1]
        return truncated + ellipsis if truncated else ellipsis

    def format_song_name(self, name: str) -> str:
        if not name:
            return "UNKNOWN"
        name = name.replace('"', '').replace("'", "")
        if len(name) > 30:
            simplified = re.sub(r'\([^)]*\)', '', name)
            simplified = re.sub(r'\[[^\]]*\]', '', name)
            simplified = simplified.strip()
            if simplified and len(simplified) < len(name):
                return simplified
        return name

    def create_image(self, records: List[Tuple], rating, is_range: bool, illustration_path: List[str], config: dict) -> Image.Image:
        WIDTH = 950
        ITEM_SIZE = 200
        TITLE_HEIGHT = 40
        SHADOW_SIZE = 10
        ITEM_HEIGHT = ITEM_SIZE + TITLE_HEIGHT + SHADOW_SIZE
        ITEMS_PER_ROW = 4
        HEADER_HEIGHT = 80
        MARGIN = 20
        DIVIDER_HEIGHT = 60
        DIVIDER_PADDING = 10
        
        if is_range:
            segment_values = set()
            for record in records:
                if len(record) >= 4 and record[3] is not None:
                    segment_values.add(record[3] / 10)
            segment_values = sorted(segment_values)
            grouped_records: Dict[float, List[Tuple]] = {seg: [] for seg in segment_values}
            for record in records:
                if len(record) >= 4 and record[3] is not None:
                    seg = record[3] / 10
                    if seg in grouped_records:
                        grouped_records[seg].append((record[0], record[1], record[2]))
            height = HEADER_HEIGHT + MARGIN
            for seg in segment_values:
                items = grouped_records[seg]
                seg_rows = math.ceil(len(items) / ITEMS_PER_ROW)
                height += seg_rows * (ITEM_HEIGHT + MARGIN)
                if seg < segment_values[-1]:
                    height += DIVIDER_HEIGHT + MARGIN
        else:
            grouped_records = {0: records}
            segment_values = [0]
        
        if is_range:
            height += MARGIN + 30
        else:
            rows = math.ceil(len(records) / ITEMS_PER_ROW)
            height = HEADER_HEIGHT + (ITEM_HEIGHT + MARGIN) * rows + MARGIN + 30
        img = Image.new('RGB', (WIDTH, height), 'white')
        draw = ImageDraw.Draw(img)
        for y in range(10):
            r = int(30 + 100 * y * 8 / HEADER_HEIGHT)
            g = int(60 + 40 * y * 8 / HEADER_HEIGHT)
            b = int(100 + 100 * y * 8 / HEADER_HEIGHT)
            draw.line((0, y, WIDTH, y), fill=(r, g, b))
        font_path = os.path.join(config["path"]["fonts"], "ShangguSans-Bold.ttf")
        try:
            title_font = ImageFont.truetype(font_path, 44)
            rank_font = ImageFont.truetype(font_path, 36)
            divider_font = ImageFont.truetype(font_path, 32)
            name_font = ImageFont.truetype(font_path, 32)
            footer_font = ImageFont.truetype(font_path, 16)
        except Exception:
            title_font = ImageFont.load_default()
            rank_font = ImageFont.load_default()
            divider_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            footer_font = ImageFont.load_default()
        title = "Arcase Constant Sheet"
        draw.text((MARGIN, (HEADER_HEIGHT - 20) // 2), title, fill=(0, 0, 0), font=title_font)
        if isinstance(rating, tuple):
            level_text = f"Level {rating[0]:.1f} ~ {rating[1]:.1f}"
        else:
            level_text = f"Level {rating:.1f}"
        level_x = WIDTH - self.get_text_width(draw, level_text, rank_font) - MARGIN
        draw.text((level_x, (HEADER_HEIGHT - 20) // 2), level_text, fill=(0, 0, 0), font=rank_font)
        y_position = HEADER_HEIGHT + MARGIN
        for idx, seg in enumerate(segment_values):
            items = grouped_records[seg]
            if not items:
                continue
            if is_range:
                seg_text = f" - {seg:.1f} - "
                seg_width = self.get_text_width(draw, seg_text, divider_font)
                seg_x = (WIDTH - seg_width) // 2
                draw.rectangle([seg_x - 10, y_position, seg_x + seg_width + 10, y_position + 30], fill=(230, 230, 230))
                draw.text((seg_x, y_position + 5), seg_text, fill=(50, 50, 50), font=divider_font)
                y_position += DIVIDER_HEIGHT
            for item_idx, (song_id, song_name, difficulty) in enumerate(items):
                row = item_idx // ITEMS_PER_ROW
                col = item_idx % ITEMS_PER_ROW
                x = MARGIN + col * (ITEM_SIZE + SHADOW_SIZE + MARGIN)
                item_y = y_position + row * (ITEM_HEIGHT + MARGIN)
                song_img = None
                for path in illustration_path:
                    dl_folder = os.path.join(path, f"dl_{song_id}")
                    if os.path.exists(dl_folder):
                        jpg_files = glob.glob(os.path.join(dl_folder, "*.[jJ][pP][gG]"))
                        if jpg_files:
                            try:
                                song_img = Image.open(jpg_files[0])
                                song_img = song_img.resize((ITEM_SIZE, ITEM_SIZE))
                                break
                            except Exception:
                                pass
                    normal_folder = os.path.join(path, song_id)
                    if os.path.exists(normal_folder):
                        jpg_files = glob.glob(os.path.join(normal_folder, "*.[jJ][pP][gG]"))
                        if jpg_files:
                            try:
                                song_img = Image.open(jpg_files[0])
                                song_img = song_img.resize((ITEM_SIZE, ITEM_SIZE))
                                break
                            except Exception:
                                pass
                if song_img is None:
                    song_img = Image.new('RGB', (ITEM_SIZE, ITEM_SIZE), (240, 240, 240))
                    d = ImageDraw.Draw(song_img)
                    d.text((10, 10), "No Image", fill='gray', font=name_font)
                img.paste(song_img, (x, item_y))
                if difficulty == 'pst':
                    color = (0, 153, 255)
                elif difficulty == 'prs':
                    color = (0, 255, 136)
                elif difficulty == 'ftr':
                    color = (153, 50, 204)
                elif difficulty == 'byn':
                    color = (220, 20, 60)
                elif difficulty == 'etr':
                    color = (147, 112, 219)
                else:
                    color = (0, 0, 0)
                draw.rectangle([
                    x + 30, 
                    item_y + ITEM_SIZE + 5, 
                    x + ITEM_SIZE + SHADOW_SIZE, 
                    item_y + ITEM_SIZE + SHADOW_SIZE + 5
                ], fill=color)
                draw.rectangle([
                    x + ITEM_SIZE + 5, 
                    item_y + 30, 
                    x + ITEM_SIZE + SHADOW_SIZE + 5, 
                    item_y + ITEM_SIZE + 15
                ], fill=color)
                title_y = item_y + ITEM_SIZE + SHADOW_SIZE
                title_text = self.format_song_name(song_name)
                max_width = ITEM_SIZE + SHADOW_SIZE - 20
                truncated_text = self.truncate_text(draw, title_text, max_width, name_font)
                text_x = x + 28
                text_y = title_y + (TITLE_HEIGHT - 20) // 2
                draw.text((text_x, text_y), truncated_text, fill='black', font=name_font)
            if items:
                items_rows = math.ceil(len(items) / ITEMS_PER_ROW)
                y_position += items_rows * (ITEM_HEIGHT + MARGIN)
            if is_range and idx < len(segment_values) - 1:
                y_position += MARGIN
        copyright_text = "Copyright © 2025 FuLuzzX. All rights reserved. - " + str(datetime.datetime.now())
        copyright_x = MARGIN
        copyright_y = height - 25
        draw.text((copyright_x, copyright_y), copyright_text, fill=(100, 100, 100), font=footer_font)
        return img

    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")