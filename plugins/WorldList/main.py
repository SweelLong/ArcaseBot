import sqlite3
import os
import json
from typing import List, Tuple, Dict
from PIL import Image, ImageDraw, ImageFont
import ncatbot
from ncatbot.plugin import BasePlugin
from ncatbot.core.event import BaseMessageEvent
from ncatbot.utils import get_log
import __main__

LOG = get_log("WorldList")
class WorldList(BasePlugin):
    name = "WorldList"
    version = "1.0.0"
    author = "SweelLong"
    description = "玩家排行榜插件，支持PTT榜和#值榜"

    @__main__.arcaea_group.command("rank", ["排行", "排名"])
    async def handle_rank_command(self, msg: BaseMessageEvent, rank_type: str = "2"):
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        OUTPUT_PATH = os.path.join(config["path"]["saves"], "WorldList.png")
        if rank_type.lower() in ["1", "ptt"]:
            rank_type = "1"
        elif rank_type.lower() in ["2", "#"]:
            rank_type = "2"
        with sqlite3.connect(config["database"]["server"], timeout=30) as conn:
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            try:
                if rank_type == "1": 
                    c.execute("SELECT name, rating_ptt FROM user ORDER BY rating_ptt DESC LIMIT 40")
                    users = c.fetchall()
                    data = [(name, (ptt / 100) if ptt is not None else 0.0) for name, ptt in users]
                    title = "Arcase POTENTIAL Rankings"
                    value_label = "PTT"
                else: 
                    c.execute("""
                        SELECT user_id, score, song_id, difficulty, 
                               shiny_perfect_count, perfect_count, near_count, miss_count, rating
                        FROM best_score
                    """)
                    best_scores = c.fetchall()
                    song_ids = set(score[2] for score in best_scores)
                    chart_data = {}
                    if song_ids:
                        placeholders = ','.join('?' for _ in song_ids)
                        c.execute(f"""
                            SELECT song_id, rating_ftr, rating_byn, rating_etr
                            FROM chart WHERE song_id IN ({placeholders})
                        """, list(song_ids))
                        charts = c.fetchall()
                        for chart in charts:
                            song_id = chart[0]
                            chart_data[song_id] = {
                                "ftr": chart[1],
                                "byn": chart[2],
                                "etr": chart[3]
                            }
                    user_scores: Dict[int, float] = {}
                    for score in best_scores:
                        user_id, score_val, song_id, difficulty, sp, p, n, m, _ = score
                        song_ratings = chart_data.get(song_id)
                        if not song_ratings:
                            continue
                        if difficulty == 2:
                            chart_rating = song_ratings["ftr"]
                        elif difficulty == 3:
                            chart_rating = song_ratings["byn"]
                        elif difficulty == 4:
                            chart_rating = song_ratings["etr"]
                        else:
                            continue
                        total_notes = p + n + m
                        if total_notes > 0:
                            acc_ratio = sp / total_notes
                            acc_component = max(0, min(acc_ratio - 0.9, 0.095))
                        else:
                            acc_component = 0
                        score_ratio = score_val / 10000000
                        score_component = max(0, min(score_ratio - 0.99, 0.01))
                        k = 100
                        song_value = k * chart_rating * (acc_component + 28.5 * score_component)
                        user_scores[user_id] = user_scores.get(user_id, 0.0) + song_value
                    sorted_users = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)[:200]
                    user_ids = [user[0] for user in sorted_users]
                    data = []
                    if user_ids:
                        placeholders = ','.join('?' for _ in user_ids)
                        c.execute(f"SELECT user_id, name FROM user WHERE user_id IN ({placeholders})", user_ids)
                        user_names = {row[0]: row[1] for row in c.fetchall()}
                        data = [
                            (user_names.get(user_id, f"未知玩家({user_id})"), score)
                            for user_id, score in sorted_users
                        ]
                    title = "Arcase #VALUE Rankings"
                    value_label = "#"
                if not data:
                    return await msg.reply("未找到用户数据，请确认数据库中有记录")
                image = self.generate_rank_image(data, title, value_label, rank_type, config)
                image.save(OUTPUT_PATH, format='PNG')
                reply_msg = ncatbot.core.MessageChain()
                reply_msg += ncatbot.core.Image(OUTPUT_PATH)
                if hasattr(msg, "group_id"):
                    return await self.api.post_group_msg(msg.group_id, rtf=reply_msg)
                else:
                    return await self.api.post_private_msg(msg.sender.user_id, rtf=reply_msg)
            except Exception as e:
                LOG.error(f"处理排行榜时出错: {str(e)}")
                return await msg.reply(f"查询失败: {str(e)}")

    def generate_rank_image(self, data: List[Tuple[str, float]], title: str, value_label: str, rank_type: str, config: dict) -> Image.Image:
        width = 800
        header_height = 160
        item_height = 90
        margin = 30
        footer_height = 50
        shadow_offset = 5
        shadow_radius = 15
        total_height = header_height + len(data) * item_height + margin * 2 + footer_height + shadow_offset * 2
        img = Image.new('RGBA', (width, total_height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        bg_radius = 24
        shadow_color = (220, 220, 220, 100)
        for i in range(shadow_radius):
            r = bg_radius + shadow_radius - i
            draw.rounded_rectangle(
                [margin + shadow_offset - i, margin + shadow_offset - i, 
                 width - margin - shadow_offset + i, total_height - margin - footer_height - shadow_offset + i],
                radius=r, fill=shadow_color
            )
        main_bg_rect = [margin + shadow_offset, margin + shadow_offset, 
                       width - margin - shadow_offset, total_height - margin - footer_height - shadow_offset]
        draw.rounded_rectangle(main_bg_rect, radius=bg_radius, fill=(255, 255, 255))
        path = os.path.join(config["path"]["fonts"], "DingTalk JinBuTi.ttf")
        title_font = ImageFont.truetype(path, 50)
        rank_font = ImageFont.truetype(path, 40)
        name_font = ImageFont.truetype(path, 34)
        value_font = ImageFont.truetype(path, 32)
        footer_font = ImageFont.truetype(path, 18)
        title_bg_height = 140
        title_bg_rect = [margin + shadow_offset, margin + shadow_offset, 
                        width - margin - shadow_offset, margin + shadow_offset + title_bg_height]
        draw.rounded_rectangle(title_bg_rect, radius=bg_radius, fill=(255, 255, 255), corners=(True, True, False, False))
        title_width = draw.textlength(title, font=title_font)
        draw.text(((width - title_width) // 2, margin + shadow_offset + 30), title, fill=(30, 30, 30), font=title_font)
        subtitle = f"Top {len(data)} · {value_label}"
        subtitle_width = draw.textlength(subtitle, font=name_font)
        draw.text(((width - subtitle_width) // 2, margin + shadow_offset + 90), subtitle, fill=(80, 80, 80), font=name_font)
        valid_values = [v for _, v in data if v is not None]
        max_value = max(valid_values) if valid_values else 1
        for idx, (name, value) in enumerate(data):
            y_pos = margin + shadow_offset + header_height + idx * item_height
            bg_color = (255, 255, 255) if idx % 2 == 0 else (250, 250, 250)
            draw.rectangle([margin + shadow_offset, y_pos, width - margin - shadow_offset, y_pos + item_height], fill=bg_color)
            rank = idx + 1
            rank_bg_radius = 25
            rank_pos = margin + shadow_offset + 50
            if rank == 1:
                draw.ellipse([rank_pos - rank_bg_radius, y_pos + item_height//2 - rank_bg_radius,
                             rank_pos + rank_bg_radius, y_pos + item_height//2 + rank_bg_radius], fill=(255, 240, 200))
                draw.ellipse([rank_pos - rank_bg_radius + 2, y_pos + item_height//2 - rank_bg_radius + 2,
                             rank_pos + rank_bg_radius - 2, y_pos + item_height//2 + rank_bg_radius - 2], fill=(255, 184, 28))
                rank_color = (255, 255, 255)
            elif rank == 2:
                draw.ellipse([rank_pos - rank_bg_radius, y_pos + item_height//2 - rank_bg_radius,
                             rank_pos + rank_bg_radius, y_pos + item_height//2 + rank_bg_radius], fill=(240, 240, 240))
                draw.ellipse([rank_pos - rank_bg_radius + 2, y_pos + item_height//2 - rank_bg_radius + 2,
                             rank_pos + rank_bg_radius - 2, y_pos + item_height//2 + rank_bg_radius - 2], fill=(169, 169, 169))
                rank_color = (255, 255, 255)
            elif rank == 3:
                draw.ellipse([rank_pos - rank_bg_radius, y_pos + item_height//2 - rank_bg_radius,
                             rank_pos + rank_bg_radius, y_pos + item_height//2 + rank_bg_radius], fill=(250, 230, 200))
                draw.ellipse([rank_pos - rank_bg_radius + 2, y_pos + item_height//2 - rank_bg_radius + 2,
                             rank_pos + rank_bg_radius - 2, y_pos + item_height//2 + rank_bg_radius - 2], fill=(205, 127, 50))
                rank_color = (255, 255, 255)
            else:
                rank_color = (70, 70, 70)
            rank_text = str(rank)
            if rank_type == "1":
                draw.text((rank_pos, y_pos + item_height // 2), rank_text, fill=rank_color, font=rank_font, anchor="mm")
            else:
                draw.text((rank_pos, y_pos + item_height // 2), rank_text, fill=rank_color, font=rank_font, anchor="mm")
            max_name_width = width - 2 * (margin + shadow_offset) - 320
            display_name = name
            while draw.textlength(display_name + "...", font=name_font) > max_name_width and len(display_name) > 1:
                display_name = display_name[:-1]
            if len(name) != len(display_name):
                display_name += "..."
            name_x = margin + shadow_offset + 150
            draw.text((name_x, y_pos + item_height // 2), display_name, fill=(50, 50, 50), font=name_font, anchor="lm")
            progress_width = width - margin - shadow_offset - 200 - name_x
            progress_height = 12
            progress_bg_y = y_pos + item_height // 2 + 20
            draw.rounded_rectangle(
                [name_x, progress_bg_y, name_x + progress_width, progress_bg_y + progress_height],
                radius=progress_height//2, fill=(230, 230, 230)
            )
            if value is not None:
                progress_ratio = value / max_value if max_value != 0 else 0
            else:
                progress_ratio = 0
            draw.rounded_rectangle(
                [name_x, progress_bg_y, name_x + progress_width * progress_ratio, progress_bg_y + progress_height],
                radius=progress_height//2, fill=(100, 180, 255)
            )
            value_text = f"{value:.2f}" if isinstance(value, float) else str(value)
            draw.text((width - margin - shadow_offset - 80, y_pos + item_height // 2), value_text, fill=(50, 50, 50), font=value_font, anchor="mm")
            if idx < len(data) - 1:
                draw.line([(margin + shadow_offset + 40, y_pos + item_height), 
                          (width - margin - shadow_offset - 40, y_pos + item_height)], 
                          fill=(240, 240, 240), width=1)
        footer_y = total_height - footer_height - shadow_offset
        draw.line([(margin + shadow_offset + 40, footer_y - 20), 
                  (width - margin - shadow_offset - 40, footer_y - 20)], 
                  fill=(240, 240, 240), width=1)
        copyright_text = "Copyright © 2025 FuLuzzX & SweelLong"
        copyright_width = draw.textlength(copyright_text, font=footer_font)
        draw.text(((width - copyright_width) // 2, footer_y + 10), copyright_text, fill=(150, 150, 150), font=footer_font)
        mask = Image.new('L', (width, total_height), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.rounded_rectangle(
            [margin//2, margin//2, width - margin//2, total_height - margin//2], 
            radius=bg_radius + 8, fill=255
        )
        img.putalpha(mask)
        return img

    async def on_load(self):
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")