from __future__ import annotations

import json
import threading
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Callable

import tkinter as tk
from tkinter import messagebox, ttk

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

try:
    from wxauto import WeChat
except Exception:  # wxauto unavailable when developing on non-Windows hosts
    WeChat = None


TASKS_FILE = Path("tasks.json")


@dataclass
class Task:
    task_id: str
    users: list[str]
    message: str
    time: str  # HH:MM
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
        users = [u.strip() for u in data.get("users", []) if u.strip()]
        return cls(
            task_id=data.get("task_id") or str(uuid.uuid4()),
            users=users,
            message=str(data.get("message", "")).strip(),
            time=str(data.get("time", "")).strip(),
            enabled=bool(data.get("enabled", True)),
        )

    def to_dict(self) -> dict:
        return asdict(self)


class TaskStore:
    def __init__(self, path: Path):
        self.path = path

    def load(self) -> list[Task]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            return [Task.from_dict(item) for item in raw]
        except (json.JSONDecodeError, OSError) as exc:
            raise RuntimeError(f"读取任务文件失败: {exc}") from exc

    def save(self, tasks: list[Task]) -> None:
        payload = [task.to_dict() for task in tasks]
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


class WeChatSender:
    def __init__(self, log: Callable[[str], None]):
        self._wx = None
        self._lock = threading.Lock()
        self._log = log

    def _ensure_client(self):
        if WeChat is None:
            raise RuntimeError("wxauto 未安装或当前环境不支持，请在 Windows + 微信环境运行")
        if self._wx is None:
            self._wx = WeChat()
        return self._wx

    def send_to_users(self, users: list[str], message: str) -> None:
        if not users:
            raise ValueError("联系人不能为空")
        if not message:
            raise ValueError("发送内容不能为空")

        with self._lock:
            wx = self._ensure_client()
            for user in users:
                wx.SendMsg(message, who=user)
                self._log(f"发送成功 -> {user}: {message}")
                time.sleep(0.3)


class TaskScheduler:
    def __init__(self, sender: WeChatSender, log: Callable[[str], None]):
        self.scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
        self.sender = sender
        self.log = log

    def start(self) -> None:
        if not self.scheduler.running:
            self.scheduler.start()
            self.log("调度器已启动")

    def stop(self) -> None:
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            self.log("调度器已停止")

    def sync_tasks(self, tasks: list[Task]) -> None:
        existing_ids = {job.id for job in self.scheduler.get_jobs()}
        desired_ids = {task.task_id for task in tasks if task.enabled}

        for job_id in existing_ids - desired_ids:
            self.scheduler.remove_job(job_id)
            self.log(f"移除任务: {job_id}")

        for task in tasks:
            if not task.enabled:
                continue
            hour, minute = self._parse_time(task.time)
            trigger = CronTrigger(hour=hour, minute=minute)
            self.scheduler.add_job(
                func=self._run_task,
                trigger=trigger,
                args=[task],
                id=task.task_id,
                replace_existing=True,
                misfire_grace_time=300,
            )
            self.log(
                f"已调度任务: {','.join(task.users)} @ {task.time}"
            )

    def _run_task(self, task: Task) -> None:
        try:
            self.sender.send_to_users(task.users, task.message)
        except Exception as exc:
            self.log(f"任务执行失败({task.task_id}): {exc}")

    @staticmethod
    def _parse_time(time_text: str) -> tuple[int, int]:
        try:
            hour_text, minute_text = time_text.split(":", 1)
            hour, minute = int(hour_text), int(minute_text)
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
            return hour, minute
        except ValueError as exc:
            raise ValueError(f"非法时间格式: {time_text}，应为 HH:MM") from exc


class TaskDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, task: Task | None = None):
        super().__init__(parent)
        self.title("新建任务" if task is None else "编辑任务")
        self.resizable(False, False)
        self.result: Task | None = None

        self.users_var = tk.StringVar(value=",".join(task.users) if task else "")
        self.message_var = tk.StringVar(value=task.message if task else "")
        self.time_var = tk.StringVar(value=task.time if task else "08:00")
        self.enabled_var = tk.BooleanVar(value=task.enabled if task else True)
        self.task_id = task.task_id if task else str(uuid.uuid4())

        self._build()
        self.grab_set()
        self.transient(parent)

    def _build(self):
        pad = {"padx": 10, "pady": 6}

        ttk.Label(self, text="联系人(多个用逗号分隔):").grid(row=0, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.users_var, width=40).grid(row=1, column=0, **pad)

        ttk.Label(self, text="消息内容:").grid(row=2, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.message_var, width=40).grid(row=3, column=0, **pad)

        ttk.Label(self, text="时间(HH:MM):").grid(row=4, column=0, sticky="w", **pad)
        ttk.Entry(self, textvariable=self.time_var, width=20).grid(row=5, column=0, sticky="w", **pad)

        ttk.Checkbutton(self, text="启用任务", variable=self.enabled_var).grid(row=6, column=0, sticky="w", **pad)

        actions = ttk.Frame(self)
        actions.grid(row=7, column=0, sticky="e", **pad)
        ttk.Button(actions, text="取消", command=self.destroy).pack(side="right", padx=4)
        ttk.Button(actions, text="保存", command=self._on_save).pack(side="right", padx=4)

    def _on_save(self):
        users = [u.strip() for u in self.users_var.get().split(",") if u.strip()]
        message = self.message_var.get().strip()
        time_text = self.time_var.get().strip()

        if not users:
            messagebox.showerror("错误", "请至少输入一个联系人")
            return
        if not message:
            messagebox.showerror("错误", "消息内容不能为空")
            return
        TaskScheduler._parse_time(time_text)

        self.result = Task(
            task_id=self.task_id,
            users=users,
            message=message,
            time=time_text,
            enabled=self.enabled_var.get(),
        )
        self.destroy()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("微信定时发送工具 (wxauto)")
        self.geometry("860x520")

        self.store = TaskStore(TASKS_FILE)
        self.tasks: list[Task] = []
        self.log_var = tk.StringVar(value="准备就绪")

        self.sender = WeChatSender(self._log)
        self.task_scheduler = TaskScheduler(self.sender, self._log)

        self._build_ui()
        self._load_tasks()
        self.task_scheduler.start()
        self.task_scheduler.sync_tasks(self.tasks)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self):
        columns = ("users", "message", "time", "enabled")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=14)
        self.tree.heading("users", text="联系人")
        self.tree.heading("message", text="内容")
        self.tree.heading("time", text="时间")
        self.tree.heading("enabled", text="状态")
        self.tree.column("users", width=220)
        self.tree.column("message", width=320)
        self.tree.column("time", width=100, anchor="center")
        self.tree.column("enabled", width=100, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        buttons = ttk.Frame(self)
        buttons.pack(fill="x", padx=10)

        ttk.Button(buttons, text="新增任务", command=self.add_task).pack(side="left", padx=4)
        ttk.Button(buttons, text="修改任务", command=self.edit_task).pack(side="left", padx=4)
        ttk.Button(buttons, text="删除任务", command=self.delete_task).pack(side="left", padx=4)
        ttk.Button(buttons, text="启用/禁用", command=self.toggle_task).pack(side="left", padx=4)
        ttk.Button(buttons, text="立即发送一次", command=self.send_now).pack(side="left", padx=4)

        ttk.Label(self, textvariable=self.log_var, foreground="#055").pack(fill="x", padx=10, pady=8)

    def _load_tasks(self):
        try:
            self.tasks = self.store.load()
            self._refresh_tree()
            self._log(f"已加载任务 {len(self.tasks)} 条")
        except Exception as exc:
            messagebox.showerror("加载失败", str(exc))
            self.tasks = []

    def _save_and_reschedule(self):
        self.store.save(self.tasks)
        self.task_scheduler.sync_tasks(self.tasks)
        self._refresh_tree()

    def _refresh_tree(self):
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        for task in self.tasks:
            self.tree.insert(
                "",
                "end",
                iid=task.task_id,
                values=(
                    ", ".join(task.users),
                    task.message,
                    task.time,
                    "启用" if task.enabled else "禁用",
                ),
            )

    def _selected_task(self) -> Task | None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("提示", "请先在列表中选择任务")
            return None
        task_id = selected[0]
        for task in self.tasks:
            if task.task_id == task_id:
                return task
        return None

    def add_task(self):
        dialog = TaskDialog(self)
        self.wait_window(dialog)
        if dialog.result:
            self.tasks.append(dialog.result)
            self._save_and_reschedule()
            self._log("任务已新增")

    def edit_task(self):
        task = self._selected_task()
        if not task:
            return
        dialog = TaskDialog(self, task)
        self.wait_window(dialog)
        if dialog.result:
            idx = self.tasks.index(task)
            self.tasks[idx] = dialog.result
            self._save_and_reschedule()
            self._log("任务已修改")

    def delete_task(self):
        task = self._selected_task()
        if not task:
            return
        if messagebox.askyesno("确认", "确定删除该任务吗？"):
            self.tasks = [t for t in self.tasks if t.task_id != task.task_id]
            self._save_and_reschedule()
            self._log("任务已删除")

    def toggle_task(self):
        task = self._selected_task()
        if not task:
            return
        task.enabled = not task.enabled
        self._save_and_reschedule()
        self._log(f"任务已{'启用' if task.enabled else '禁用'}")

    def send_now(self):
        task = self._selected_task()
        if not task:
            return
        try:
            self.sender.send_to_users(task.users, task.message)
            self._log("手动发送完成")
        except Exception as exc:
            messagebox.showerror("发送失败", str(exc))
            self._log(f"手动发送失败: {exc}")

    def _log(self, text: str):
        self.log_var.set(text)
        print(text)

    def _on_close(self):
        self.task_scheduler.stop()
        self.destroy()


def ensure_tasks_json_exists():
    if not TASKS_FILE.exists():
        TASKS_FILE.write_text("[]\n", encoding="utf-8")


if __name__ == "__main__":
    ensure_tasks_json_exists()
    app = App()
    app.mainloop()
