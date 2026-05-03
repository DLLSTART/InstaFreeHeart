as a user
i want to use instaFreeHeart 通过USB线给其他外设例如手机充电
so that 用户可以将instafreeheart当作充电宝携带

as a user
i want to 通过佩戴磁吸配件,将instafreeheart 通过磁吸的方式佩戴在胸前
so that 用户可以将instafreeheart 挂在胸前并且通过usb 线对外供电

as a user
i want to instafreeheart可以在充电的时候亮环形灯
so that 用户可以在instafreeheart工作的时候胸前亮起钢铁侠般的圆环

as a user
i want to 在instafreeheart 中间位置摆放一个摄像头
so that 此摄像头间断工作并拍摄周围的环境并在合适的时候上传到云端AI服务器生成用户想要的视频资料

given instafreeheart已经获得了网络通信的能力
instafreeheart 拍摄一张图片
instafreeheart 通过本地部署的大模型进行图片的处理
instafreeheat 将处理后的图片保存在本地
instafreeheart 将当前本地缓存的资料全部通过大模型处理,生成一段视频日记,作为当前一段时间的行为记录
PS:用户可以选择生成日记的风格,可以是卡通动漫风格,也可以是像素画风格
这个功能就叫做日记模式,通过离散的图片保存最后生成一整天的日记.

as a user
i want to 使用instafreeheart 记录声音数据
so that i can 更清晰的记录下一天中的某个时刻的对话信息
而且可以记录语音数据,在用户的声音持续超过1s的时候同步将用户的声音数据记录下来并保存.在固定时刻统一生成日记.生成一段视频日记.

---

# 市场调研补充用户故事

> 调研对象：市面上 2023–2026 主流的「随身摄像头 + 麦克风 + AI」类可穿戴产品。
> 含 **Humane AI Pin**（磁吸胸前 AI Pin）、**Rabbit R1**（手持 LAM AI）、
> **Plaud Note / NotePin**（磁吸 AI 录音笔）、**Limitless Pendant**（项链式 AI 转写）、
> **Friend AI Pendant**、**Bee AI Wearable**、**Meta Ray-Ban Smart Glasses**、
> **Snap Spectacles**、**Avi Schiffmann's Friend**。
> 下面整理「用户广泛喜爱、社区呼声最高、负面评价集中改进项」共 25 条补充需求。

## A. 隐私与信任（用户最关心的红线）

US8 [P0]
as a 被拍摄/被录音方
i want to 当 InstaFreeHeart 正在录制视频或音频时,设备的环形灯会强制亮起一个明显可见的"录制中"指示色（如红色 LED 或特殊呼吸灯）
so that 周围的人可以一眼看出我正在被录,我可以选择回避或要求停止
ref: Snap Spectacles 强制亮黄圈;Meta Ray-Ban 镜框 LED;Humane AI Pin Trust Light

US9 [P0]
as a user
i want to 设备上有一个物理的"隐私开关"或"长按 USER 按键 2 秒"动作,可以瞬间禁用所有摄像头/麦克风采集
so that 在洗手间、亲密场合、机密会议等敏感场景下我有绝对的硬关断保证

US10 [P1]
as a user
i want to 设备通过 BLE 周期广播一条短报文 "InstaFreeHeart_RECORDING@<匿名 ID>"
so that 任何附近运行 InstaFreeHeart 配套 App 的人可以在自己的手机上收到提醒,实现"被录制方知情"

US11 [P0]
as a user
i want to 我的所有原始视频/音频数据默认只存在本地 microSD,不强制上传任何云
so that 我对我的数据有 100% 所有权,可以一键导出/一键销毁,符合 GDPR / CCPA

US12 [P1]
as a user
i want to 设备本地 LLM 优先处理（端侧推理生成 caption/summary）,只在用户主动开启"云端增强"时才上传脱敏后的文本/缩略图到云
so that 我可以在隐私保护与 AI 能力之间自主选择

## B. 录制与回看的基础体验（同类产品负面评价的高发地）

US13 [P0]
as a user
i want to 当我按一下 USER 按键时,设备立即拍一张照片或开始一段 30 秒短视频,并在拍摄前给我一个明显的反馈（灯环短亮 + 振动）
so that 我可以主动捕捉关键瞬间,而不是依赖 AI 自动判断时机
ref: Humane AI Pin 用户最大的吐槽是"AI 自动拍的照片经常错过我想要的瞬间"

US14 [P1]
as a user
i want to 在配套 App 中可以看到一条按时间排列的"日记时间线",每条目自动配上 AI 生成的标题、地点、参与者
so that 我可以快速回顾今天/本周/本月发生的事
ref: Limitless 的「Lifelog Timeline」是其核心卖点

US15 [P1]
as a user
i want to 设备能识别"重要时刻"关键词（如"记下"、"提醒我"、"重要"、"快门"）并在录音中自动打 bookmark
so that 后续回看时可以直接跳到关键片段,不用从头听

US16 [P2]
as a user
i want to 在配套 App 中可以预览设备视角的实时取景画面（按住按键启用,松开关闭,带 5 秒倒计时）
so that 拍照前我能确认构图,避免"拍了一堆废片"
ref: Humane AI Pin 没有预览屏被广泛吐槽

US17 [P1]
as a user
i want to 长按 USER 按键 5 秒触发"SOS 模式":立即开启长录像 + GPS 定位 + 通过 WiFi/BLE 转手机紧急联系人
so that 在突发危险时我有最后一道安全保障
ref: Apple Watch SOS、Garmin inReach 同类设计

## C. AI 增值能力（用户付费意愿最高的功能）

US18 [P0]
as a user
i want to 设备可以对录到的语音做实时转写,并支持中/英/日多语言以及实时翻译
so that 跨国会议、外语学习、采访都能省去后期听打
ref: Plaud Note 的核心卖点;Meta Ray-Ban 翻译功能在 2024 推出后销量翻倍

US19 [P0]
as a user
i want to 在会议结束后 30 秒内,设备生成一份带「行动项 / 决议 / 待办」结构的会议纪要
so that 直接发到工作群,不再为整理纪要熬夜
ref: Plaud Note "Summary"、Otter.ai 模式

US20 [P1]
as a user
i want to 设备能识别多个说话人并在转写中区分「Speaker A / B / C」,如果在 App 中绑定过姓名则直接用姓名标注
so that 多人会议的转写可读性大幅提升

US21 [P2]
as a user
i want to 设备能识别说话人的情绪语调（兴奋 / 平静 / 焦虑等）并在日记中标注
so that 我可以回看自己每天的情绪变化,做情绪日志

US22 [P2]
as a user
i want to 配套 App 支持"自然语言搜索"（例如:"上周三和小王讨论的预算是多少"）
so that 海量录音/视频积累后,我仍能快速翻到某个具体瞬间

## D. 续航与佩戴体验（决定能否每天戴）

US23 [P0]
as a user
i want to 设备支持 MagSafe 风格的磁吸无线充电底座（也可选 USB-C 有线）
so that 每天放回底座就充电,不必拧 USB-C
ref: Apple MagSafe / Plaud NotePin 磁吸充电

US24 [P1]
as a user
i want to 配套 App 在我的设备电量 < 20% 时推送一条低电量提醒
so that 我有时间在出门前充电,不会工作中断电

US25 [P1]
as a user
i want to 设备外壳支持一组可替换的磁吸"装饰盖"（不同颜色 / 材质 / 反应堆图案）
so that 我可以按场合（运动 / 商务 / 派对）切换外观
ref: Pebble、Fitbit Versa、Apple Watch 表带文化

## E. 设备生态与可靠性

US26 [P1]
as a user
i want to 设备固件支持 OTA 升级（通过配套 App 经 BLE / WiFi 推送）
so that 厂商修 bug、加新功能时我不必拆机刷固件
ref: 所有量产消费电子的标配

US27 [P1]
as a user
i want to 设备能与我的其他设备（手机、Apple Watch、Mac）通过 iCloud / 自建云同步日记数据
so that 我可以在任何设备上回看,且数据不会因设备丢失而消失

US28 [P2]
as a user
i want to 设备有 IPX5 防溅 + 1 m 跌落保护
so that 突遭小雨或不慎跌落时设备不报废
ref: Apple Watch、GoPro 防护等级

US29 [P2]
as a user
i want to 设备支持 BLE 防丢功能（类似 AirTag,设备遗失时手机能定位最后一次连接的位置）
so that 不会因摘下后忘记位置而真正丢失

## F. 社交与分享

US30 [P1]
as a user
i want to 设备有"快速分享"手势(双击灯环面板),立即把刚拍的照片/30 秒短视频发到我预设的好友群
so that 旅行 / 演唱会 / 聚会场景下可以即刻共享精彩瞬间
ref: Snap Spectacles 一键发 Snapchat、GoPro Quik 一键剪辑

US31 [P2]
as a user
i want to 配套 App 在每日生成日记时,可以选择"私人 / 朋友 / 公开"三种隐私级别,公开版可一键发到社交媒体
so that 我可以选择性地分享生活,而不是 all-or-nothing

## G. 特殊场景与人群

US32 [P2]
as a user (老人/儿童监护人)
i want to 设备有一个"安心模式":一键发起视频通话 + 自动 GPS 上报 + 录制 30 分钟环境音
so that 老人/儿童遇险时一键 SOS,监护人远程能看能听

US33 [P2]
as a user (视障人群)
i want to 设备能持续描述眼前场景（"前方 3 米有台阶"/"对面是张三"）通过骨传导耳机或蓝牙耳机播报
so that 设备成为我的"AI 视觉助手"
ref: OrCam MyEye、Microsoft Seeing AI

US34 [P2]
as a user (内容创作者)
i want to 设备录的素材自动按"高光时刻"剪辑成 15 秒短视频,直接生成竖屏 9:16 适配抖音/小红书
so that 我可以无脑日更 vlog
ref: GoPro Quik、Insta360 AI 编辑

## 优先级说明

- **P0** = 必须做（红线 / 同类产品最高频差评点）
- **P1** = 应该做（关键差异化或体验提升）
- **P2** = 可以做（v2 路线扩展）

---

## 落实路线图（与已有方案的关联）

| US# | 已落地于 | 备注 |
|-----|---------|------|
| US8 录制指示灯 | 灯环可复用 IO38 / WS2812B | 固件改色策略即可，硬件无新增 |
| US9 物理隐私开关 | 已有 SW2 USER 键 + IO21 PWDN | 长按 2s 切断摄像头电源 |
| US11 数据本地存储 | microSD（已 BOM） | 默认行为，无新增 |
| US12 端侧 LLM | ESP32-S3 8 MB PSRAM + esp-dl | 已规划 |
| US13 主动拍照 | SW2 + diary_mode.c 事件 | 当前已有 EVT_USER_BTN |
| US18 实时转写 | 双 INMP441 + WiFi 上传 | 软件链路全通 |
| US23 无线充电 | 需评估加 Qi 接收线圈 5 W（影响厚度+1.5 mm） | 待 v2 评估 |
| US25 磁吸装饰盖 | 已有 Halbach 中央磁铁 Φ22 | 增加同极性吸附盖即可 |
| US26 OTA | esp_ota_https | 软件，零硬件成本 |
| US28 防溅 | Gore-Tex 麦孔防水膜（已 BOM） | 后续做整机硅胶密封圈即可达 IPX5 |
| US33 视障助手 | 增加 BLE 音频通道（已支持） | 软件 + 配套 App |
