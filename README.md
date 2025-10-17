# ArcaseBot
Arcase使用的QQ机器人项目，搭配[Arcaea-server](https://github.com/Lost-MSth/Arcaea-server)服务端，使用Python语言编写，基于[NcatBot](https://github.com/liyihao1110/ncatbot)框架，需要解压[NapCat](https://github.com/NapNeko/NapCatQQ0).Shell到NapCat文件夹。
## 功能
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
## TODO
    01.个人简介插件profile+查看user_item已有的物品
    02.ai支持查询songlist信息和定数等信息
    03.添加一个打歌次数统计的版块，结合歌曲信息查询
    04.研究st3的在线下载
    05.更改recent插件的字体、重做recent插件
    06.戳一戳添加：文本、语音、图片
    07.自动收集表情包50%加工用opencv镜像或加希腊字母
    08.投票插件
    09.完成表插件：https://smartrte.github.io/completion.html
    10.修改rating插件的效果
    11.bot+server结合做一个自选段位系统
    12.bottle插件
    13.main.py拆分工具类
    14.Guy和AiChan修改为表情包而不是图片
    15.ArcaseWeb的shop和alias(修改Alias插件的Web链接输出)功能移植 -> 插件
    16.读取arcaea_log.db写一个ptt趋势图
