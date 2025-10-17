__all__ = ['Song']

from typing import Optional, List

from pydantic import BaseModel, Field


class TitleLocalized(BaseModel):
    en: str
    ja: Optional[str] = None  # 提供默认值None
    ko: Optional[str] = None  # 保持使用ko，但错误信息寻找kr，可能需要注意数据来源
    zh_Hans: Optional[str] = Field(None, alias='zh-Hans')  # 提供默认值None
    zh_Hant: Optional[str] = Field(None, alias='zh-Hant')  # 提供默认值None


class SourceLocalized(BaseModel):
    en: str
    ja: Optional[str] = None
    ko: Optional[str] = None
    zh_Hans: Optional[str] = Field(None, alias='zh-Hans')
    zh_Hant: Optional[str] = Field(None, alias='zh-Hant')


class BgDayNight(BaseModel):
    day: str
    night: str


class Difficulty(BaseModel):
    ratingClass: int
    chartDesigner: str
    jacketDesigner: str
    jacketOverride: Optional[bool] = False  # 提供默认值None
    rating: int
    ratingPlus: Optional[bool] = False  # 提供默认值None


class Song(BaseModel):
    idx: Optional[int] = 0
    id: str
    title_localized: TitleLocalized
    source_localized: Optional[SourceLocalized] = None  # 提供默认值None
    source_copyright: Optional[str] = None
    artist: str
    bpm: str
    bpm_base: float
    set: str
    purchase: str
    audioPreview: int
    audioPreviewEnd: int
    side: int
    bg: str
    bg_daynight: Optional[BgDayNight] = None  # 提供默认值None
    bg_inverse: Optional[str] = None
    remote_dl: Optional[bool] = False  # 提供默认值None
    date: int
    version: str
    difficulties: List[Difficulty]  # 使用大写List更规范