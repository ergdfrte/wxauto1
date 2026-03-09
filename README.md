# wxauto (2021-2025)

## 本项目于2025-10-28停止维护


### **文档**： [完整文档](https://github.com/cluic/wxauto/blob/main/docs/README.md)


|  环境  | 版本 |
| :----: | :--: |
|   OS   | [![Windows](https://img.shields.io/badge/Windows-10\|11\|Server2016+-white?logo=windows&logoColor=white)](https://www.microsoft.com/)  |
|  微信  | [![Wechat](https://img.shields.io/badge/%E5%BE%AE%E4%BF%A1-3.9.X-07c160?logo=wechat&logoColor=white)](https://pan.baidu.com/s/1FvSw0Fk54GGvmQq8xSrNjA?pwd=vsmj) |
| Python | [![Python](https://img.shields.io/badge/Python-3.9\+-blue?logo=python&logoColor=white)](https://www.python.org/)|


## 联系

Email: louxinghao@gmail.com

## 免责声明
代码仅用于对UIAutomation技术的交流学习使用，禁止用于实际生产项目，请勿用于非法用途和商业用途！如因此产生任何法律纠纷，均与作者无关！
---

## Windows 微信自动定时发送工具（GUI）

仓库新增了一个基于 `wxauto` + `APScheduler` + `tkinter` 的桌面工具：`wechat_scheduler_gui.py`。

### 功能
- 定时发送：为每条任务设置联系人、内容、时间（每天重复）。
- 多联系人：单条任务支持多个联系人（英文逗号分隔）。
- 任务管理：新增、修改、删除、启用/禁用任务。
- 持久化：任务自动保存到 `tasks.json`，启动时自动加载。
- 手动触发：可在 GUI 中选中任务“立即发送一次”。

### 运行环境
- Windows 10/11
- PC 版微信（保持已登录）
- Python 3.9+

### 安装依赖
```bash
pip install -e .
```

### 启动
```bash
python wechat_scheduler_gui.py
```

### tasks.json 示例
```json
[
  {
    "task_id": "6f4f4fc6-0aa3-4b2e-8fd6-24f2a3be0a5e",
    "users": ["张三", "李四"],
    "message": "早安",
    "time": "08:00",
    "enabled": true
  }
]
```
