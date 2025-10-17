from ncatbot.plugin import BasePlugin
from ncatbot.core.message import BaseMessage
from ncatbot.core import MessageChain
from ncatbot.core import Image as BotImage
from ncatbot.utils import get_log
import os
import sqlite3
import json
import __main__
from .render import Render
from .utils import fetch_song_info

LOG = get_log("Chart")
class Chart(BasePlugin):
    name = "Chart"
    version = "1.0.0"
    author = "SweelLong"
    description = "Arcaea谱面渲染插件"

    def parse_command(self, arg) -> tuple:
        args = arg.rsplit(maxsplit=1)
        song_identifier = args[0].strip()
        try:
            difficulty = int(args[1].strip())
            if difficulty < 0 or difficulty > 4:
                return None, None
            return song_identifier, difficulty
        except ValueError:
            return None, None

    def is_valid_song_id(self, song_id: str) -> bool:
        if not SONGLIST_PATH or not os.path.exists(SONGLIST_PATH):
            LOG.error("songlist文件不存在，无法验证歌曲ID")
            return False
        try:
            with open(SONGLIST_PATH, "r", encoding="utf-8") as f:
                songlist = json.load(f)["songs"]
                return any(song["id"] == song_id for song in songlist)
        except Exception as e:
            LOG.error(f"验证歌曲ID失败: {e}")
            return False

    def get_song_id_from_alias(self, alias: str) -> str:
        try:
            with sqlite3.connect(USER_DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT song_id FROM alias 
                    WHERE alias = ?
                """, (alias,))
                result = cursor.fetchone()
                return result["song_id"] if result else None
        except Exception as e:
            LOG.error(f"查询别名失败: {e}")
            return None

    def find_song_folder(self, song_id: str) -> str:
        for base_path in SONGS_PATH:
            if not os.path.exists(base_path):
                continue
            possible_folders = [
                os.path.join(base_path, song_id)
            ]
            for folder in possible_folders:
                if os.path.isdir(folder):
                    return folder
        return None

    def get_aff_path(self, song_folder: str, difficulty: int) -> str:
        aff_path = os.path.join(song_folder, f"{difficulty}.aff")
        return aff_path if os.path.exists(aff_path) else None

    def get_cover_path(self, song_folder: str) -> str:
        for file in os.listdir(song_folder):
            if file.lower().endswith(".jpg") and not file.startswith("."):
                cover_path = os.path.join(song_folder, file)
                return cover_path if os.path.isfile(cover_path) else None
        return None

    def get_difficulty_rating(self, difficulty: int) -> str:
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
        
    def generate_chart_image(self, song_id: str, difficulty: int) -> str:
        song_folder = self.find_song_folder(song_id)
        if not song_folder:
            LOG.error(f"未找到歌曲文件夹: {song_id}")
            return None, "歌曲文件夹不存在"
        aff_path = self.get_aff_path(song_folder, difficulty)
        cover_path = self.get_cover_path(song_folder)
        if not aff_path:
            LOG.error(f"未找到aff文件: {song_id}_{difficulty}.aff")
            return None, "aff文件不存在"
        if not cover_path:
            LOG.error(f"未找到封面图片: {song_folder}")
            return None, "封面图片不存在"
        try:
            song_info = fetch_song_info(SONGLIST_PATH, song_id) if SONGLIST_PATH else None
        except Exception as e:
            LOG.warning(f"获取歌曲信息失败，使用默认值: {e}")
            song_info = None
        try:
            constant = 0.0
            with sqlite3.connect(GAME_DB_PATH, timeout=30) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM chart WHERE song_id = ?", (song_id,))
                get_chart_info = cursor.fetchone()
                constant = round(float(get_chart_info[self.get_difficulty_rating(difficulty)]) / 10, 1)
            render = Render(
                aff_path=aff_path,
                cover_path=cover_path,
                song=song_info,
                difficulty=difficulty,
                constant=constant
            )
            render.save(SAVE_PATH)
            LOG.info(f"✅ Chart图片已保存至: {SAVE_PATH}")
            return SAVE_PATH, None
        except Exception as e:
            LOG.error(f"渲染图片失败: {e}", exc_info=True)
            if os.path.exists(SAVE_PATH):
                os.remove(SAVE_PATH)
            return None, "请选择其他难度！"

    @__main__.arcaea_group.command("chart", ["谱面"])
    async def handle_chart(self, msg: BaseMessage, song_identifier: str, difficulty: int):
        song_id = song_identifier
        if not self.is_valid_song_id(song_id):
            LOG.info(f"尝试从别名查询: {song_identifier}")
            song_id = self.get_song_id_from_alias(song_identifier)
            if not song_id:
                return await msg.reply(f"未找到歌曲: {song_identifier}（请检查ID或别名是否正确）")
        returnimginfo = self.generate_chart_image(song_id, difficulty)
        image_path, error_msg = returnimginfo
        if not image_path:
            return await msg.reply(f"谱面图片生成失败：{error_msg}")
        try:
            if hasattr(msg, "group_id"):
                return await self.api.post_group_msg(msg.group_id, rtf=MessageChain(BotImage(image_path)))
            else:
                return await msg.reply(BotImage(image_path))
        except Exception as e:
            LOG.error(f"发送图片失败: {e}", exc_info=True)
            return await msg.reply("图片发送失败，请稍后再试")
        
    async def on_load(self):
        global SONGS_PATH, SONGLIST_PATH, USER_DB_PATH, GAME_DB_PATH, SAVE_PATH
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        SAVE_PATH = os.path.join(config["path"]["saves"], "Chart.png")
        USER_DB_PATH = config["database"]["bot"]
        GAME_DB_PATH = config["database"]["server"]
        SONGS_PATH = [
            config["path"]["database_songs"],
            config["path"]["illustrations"]
        ]
        SONGLIST_PATH = config["path"]["songlist"]
        LOG.info(f"{self.name}插件({self.version})已加载，作者: {self.author}")
