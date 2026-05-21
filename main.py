import pyotp
import time
import tkinter as tk
from tkinter import messagebox
import os

# 定义保存密钥的文件名
SAVE_FILE = "2fa_secret.txt"

class TOTPApp:
    def __init__(self, root):
        self.root = root
        self.root.title("2FA 验证码生成器")
        self.root.geometry("320x280")  # 稍微调高一点窗口以容纳新按键
        self.root.eval('tk::PlaceWindow . center')  # 窗口居中显示

        self.secret = ""
        self.totp = None

        # --- 界面元素 ---
        tk.Label(root, text="请输入 16位/32位 2FA 密钥：", font=("Arial", 10)).pack(pady=(15, 5))

        self.entry_key = tk.Entry(root, width=30)
        self.entry_key.pack(pady=5)

        # 记住密钥复选框
        self.remember_var = tk.BooleanVar(value=True)  # 默认勾选
        self.chk_remember = tk.Checkbutton(root, text="记住此密钥", variable=self.remember_var)
        self.chk_remember.pack(pady=0)

        self.btn_verify = tk.Button(root, text="验证并生成", command=self.verify_key)
        self.btn_verify.pack(pady=5)

        # 验证码显示区
        self.label_code = tk.Label(root, text="---", font=("Arial", 24, "bold"), fg="blue")
        self.label_code.pack(pady=(10, 0))

        # 倒计时显示区
        self.label_time = tk.Label(root, text="剩余时间：-- 秒", fg="gray")
        self.label_time.pack(pady=5)

        # 复制按钮
        self.btn_copy = tk.Button(root, text="📋 复制验证码", state=tk.DISABLED, command=self.copy_code, bg="#e0e0e0")
        self.btn_copy.pack(pady=5)

        # 启动时检查是否有保存的密钥
        self.load_saved_key()

        # 启动定时刷新任务
        self.update_clock()

    def load_saved_key(self):
        """读取本地保存的密钥"""
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    saved_key = f.read().strip()
                    if saved_key:
                        self.entry_key.insert(0, saved_key)
                        # 如果想让它打开就自动生成，可以取消下面这行的注释
                        # self.verify_key()
            except Exception as e:
                print(f"读取密钥失败: {e}")

    def verify_key(self):
        """验证用户输入的密钥是否合法并保存"""
        raw_key = self.entry_key.get().strip()
        self.secret = raw_key.replace(" ", "").upper()

        try:
            self.totp = pyotp.TOTP(self.secret)
            self.totp.now()  # 测试生成一次，如果密钥不合法这里会报错

            # 验证成功，激活复制按钮
            self.btn_copy.config(state=tk.NORMAL)

            # 处理保存逻辑
            if self.remember_var.get():
                with open(SAVE_FILE, "w", encoding="utf-8") as f:
                    f.write(self.secret)
            else:
                # 如果用户取消勾选，则删除本地文件
                if os.path.exists(SAVE_FILE):
                    os.remove(SAVE_FILE)

            messagebox.showinfo("成功", "✅ 密钥有效，开始生成！")
        except Exception as e:
            self.totp = None
            self.btn_copy.config(state=tk.DISABLED)
            self.label_code.config(text="---", fg="red")
            self.label_time.config(text="剩余时间：-- 秒")
            messagebox.showerror("错误", f"❌ 密钥无效！\n{e}")

    def update_clock(self):
        """每秒更新一次验证码和倒计时"""
        if self.totp:
            code = self.totp.now()
            remaining = 30 - (int(time.time()) % 30)

            self.label_code.config(text=code, fg="blue")
            self.label_time.config(text=f"剩余时间：{remaining:2d} 秒")

        # 每 1000 毫秒（1秒）调用一次自己
        self.root.after(1000, self.update_clock)

    def copy_code(self):
        """将验证码复制到系统剪贴板"""
        if self.totp:
            code = self.totp.now()
            self.root.clipboard_clear()  # 清空剪贴板
            self.root.clipboard_append(code)  # 写入剪贴板
            self.root.update()  # 保持剪贴板内容

            # 给用户一个复制成功的视觉反馈
            self.btn_copy.config(text="✅ 已复制！", bg="#c8e6c9")
            self.root.after(2000, lambda: self.btn_copy.config(text="📋 复制验证码", bg="#e0e0e0"))


if __name__ == "__main__":
    # 创建主窗口并运行
    root = tk.Tk()
    app = TOTPApp(root)
    root.mainloop()