# 仓库代码总览（按文件）

> 本文是对当前仓库文件职责的快速拆解，帮助读者先建立“哪些文件负责什么”的全局认知。

## 1. 根目录文件

### `README.md`
- 项目状态说明：仓库在 2025-10-28 停止维护。
- 给出基础环境矩阵（Windows / 微信版本 / Python 版本）。
- 重点介绍新增桌面工具 `wechat_scheduler_gui.py` 的功能、安装与启动方式，并附 `tasks.json` 样例。

### `pyproject.toml`
- Python 包元数据：名称 `wxauto`、版本 `39.2.1`、作者信息、Python 版本范围。
- 运行依赖（`tenacity`、`pywin32`、`apscheduler` 等）。
- 使用 setuptools 进行构建打包。

### `wechat_scheduler_gui.py`
- 这是仓库里唯一“实质业务代码”文件，完成微信定时消息 GUI 工具：
  - `Task`：任务数据模型（联系人、消息、时间、启用状态）。
  - `TaskStore`：任务 JSON 读写。
  - `WeChatSender`：实际调用 `wxauto.WeChat` 发送消息，并串行化发送（线程锁）。
  - `TaskScheduler`：用 APScheduler 建立/同步定时任务。
  - `TaskDialog`：任务新增/编辑弹窗。
  - `App`：主窗口（任务列表 + 增删改查 + 启停 + 手动发送）。
  - `ensure_tasks_json_exists` + `main`：启动前确保数据文件存在并拉起 GUI。

### `tasks.json`
- GUI 的任务持久化文件，默认是空数组 `[]`。

### `LICENSE`
- Apache 2.0 许可证文本。

## 2. 文档目录 `docs/`

### `docs/README.md`
- 极简快速开始：初始化微信实例、发送消息、读取当前聊天消息。

### `docs/example.md`
- 示例脚本集合：
  - 基本使用
  - 消息监听
  - 好友申请处理
  - 打字机发送
  - 多客户端/登录窗口
  - 自动登录与二维码
  - 合并转发
  - 创建群聊

## 3. 类文档目录 `docs/class/`

### `docs/class/WeChat.md`
- `WeChat` 主入口类文档。
- 覆盖实例初始化、窗口切换、监听、联系人/好友申请、朋友圈入口、在线状态、个人信息等。

### `docs/class/Chat.md`
- `Chat` 会话窗口对象文档。
- 包含发消息、发文件、发表情、加载历史、群管理、合并转发、对话框等。

### `docs/class/Session.md`
- 会话列表相关对象文档。
- 提供搜索、置顶、滚动、会话元素点击/删除/隐藏等。

### `docs/class/Message.md`
- 消息体系文档（体量最大）。
- 从基类 `Message` 到各消息子类（文本、图片、视频、语音、文件、引用、链接、名片、系统消息等）的方法说明。

### `docs/class/Moment.md`
- 朋友圈对象文档。
- 包括获取朋友圈、刷新、点赞、评论、保存图片等。

### `docs/class/Other.md`
- 其余辅助对象文档：
  - `WxResponse`、`WxParam`
  - `NewFriendElement`
  - `LoginWnd`
  - `WeChatImage`
  - `WeChatDialog`
  - `get_wx_clients` / `get_wx_logins`
