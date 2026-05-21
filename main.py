import pyotp
import time
import tkinter as tk
from tkinter import messagebox, filedialog
import os
import urllib.parse
from PIL import Image, ImageGrab  # 增加了 ImageGrab 用于截图
from pyzbar.pyzbar import decode

# 定义保存密钥的文件名
SAVE_FILE = "2fa_secret.txt"


class TOTPApp:
    def __init__(self, root):
        self.root = root
        self.root.title("2FA 验证码生成器")
        self.root.geometry("320x380")  # 再次稍微调高窗口以容纳新按钮
        self.root.eval('tk::PlaceWindow . center')

        self.secret = ""
        self.totp = None

        # --- 界面元素 ---
        tk.Label(root, text="请输入 16位/32位 2FA 密钥：", font=("Arial", 10)).pack(pady=(15, 5))

        self.entry_key = tk.Entry(root, width=30)
        self.entry_key.pack(pady=5)

        # 屏幕/剪贴板识别按钮（新功能）
        self.btn_screen = tk.Button(root, text="✂️ 识别剪贴板 / 屏幕上的二维码", command=self.scan_screen_qr,
                                    bg="#e3f2fd")
        self.btn_screen.pack(pady=(5, 5))

        # 文件识别按钮
        self.btn_qr = tk.Button(root, text="🖼️ 从本地图片读取二维码", command=self.scan_qr_image)
        self.btn_qr.pack(pady=(0, 5))

        # 记住密钥复选框
        self.remember_var = tk.BooleanVar(value=True)
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

        self.load_saved_key()
        self.update_clock()

    def process_qr_data(self, qr_data):
        """处理识别出来的二维码文本内容（提取 secret）"""
        try:
            parsed_url = urllib.parse.urlparse(qr_data)
            if parsed_url.scheme == "otpauth":
                query_params = urllib.parse.parse_qs(parsed_url.query)
                secret = query_params.get("secret", [None])[0]

                if secret:
                    self.entry_key.delete(0, tk.END)
                    self.entry_key.insert(0, secret)
                    self.verify_key()
                else:
                    messagebox.showerror("错误", "⚠️ 二维码有效，但未包含 2FA 密钥 (secret)！")
            else:
                self.entry_key.delete(0, tk.END)
                self.entry_key.insert(0, qr_data)
                self.verify_key()
        except Exception as e:
            messagebox.showerror("解析错误", f"提取密钥失败: {e}")

    def scan_screen_qr(self):
        """抓取剪贴板图片或全屏截图进行识别"""
        try:
            # 1. 优先尝试从系统剪贴板读取图片 (用户刚用 Win+Shift+S 截的图)
            img = ImageGrab.grabclipboard()

            # 2. 如果剪贴板里不是图片，则自动进行全屏扫描
            if img is None or not hasattr(img, 'convert'):
                self.root.iconify()  # 暂时最小化窗口，防止挡住屏幕上的二维码
                self.root.update()
                time.sleep(0.3)  # 等待最小化动画完成

                img = ImageGrab.grab()  # 截取全屏
                self.root.deiconify()  # 恢复窗口显示

            if not img:
                messagebox.showerror("错误", "获取屏幕截图失败！")
                return

            # 解析图片中的二维码
            decoded_objects = decode(img)

            if not decoded_objects:
                messagebox.showerror(
                    "未找到二维码",
                    "❌ 屏幕或剪贴板中没有检测到清晰的二维码！\n\n💡 强烈建议：先使用系统自带截图 (Win+Shift+S) 或微信截图，将二维码框选复制后，再点此按钮。"
                )
                return

            qr_data = decoded_objects[0].data.decode('utf-8')
            self.process_qr_data(qr_data)

        except Exception as e:
            self.root.deiconify()  # 确保出错时窗口能恢复
            messagebox.showerror("识别错误", f"屏幕识别失败: {e}")

    def scan_qr_image(self):
        """打开文件对话框，选择图片并解析二维码"""
        file_path = filedialog.askopenfilename(
            title="选择包含二维码的图片",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp")]
        )
        if not file_path: return
        try:
            img = Image.open(file_path)
            decoded_objects = decode(img)
            if not decoded_objects:
                messagebox.showerror("错误", "❌ 未能在图片中检测到二维码！")
                return
            qr_data = decoded_objects[0].data.decode('utf-8')
            self.process_qr_data(qr_data)
        except Exception as e:
            messagebox.showerror("错误", f"图片读取失败: {e}")

    def load_saved_key(self):
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as f:
                    saved_key = f.read().strip()
                    if saved_key:
                        self.entry_key.insert(0, saved_key)
            except Exception as e:
                pass

    def verify_key(self):
        raw_key = self.entry_key.get().strip()
        self.secret = raw_key.replace(" ", "").upper()
        try:
            self.totp = pyotp.TOTP(self.secret)
            self.totp.now()

            self.btn_copy.config(state=tk.NORMAL)

            if self.remember_var.get():
                with open(SAVE_FILE, "w", encoding="utf-8") as f:
                    f.write(self.secret)
            else:
                if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)

            # 静默验证，成功不再弹窗打扰用户
            # messagebox.showinfo("成功", "✅ 密钥有效，开始生成！")
        except Exception as e:
            self.totp = None
            self.btn_copy.config(state=tk.DISABLED)
            self.label_code.config(text="---", fg="red")
            self.label_time.config(text="剩余时间：-- 秒")
            messagebox.showerror("错误", f"❌ 密钥无效！\n{e}")

    def update_clock(self):
        if self.totp:
            code = self.totp.now()
            remaining = 30 - (int(time.time()) % 30)
            self.label_code.config(text=code, fg="blue")
            self.label_time.config(text=f"剩余时间：{remaining:2d} 秒")
        self.root.after(1000, self.update_clock)

    def copy_code(self):
        if self.totp:
            code = self.totp.now()
            self.root.clipboard_clear()
            self.root.clipboard_append(code)
            self.root.update()
            self.btn_copy.config(text="✅ 已复制！", bg="#c8e6c9")
            self.root.after(2000, lambda: self.btn_copy.config(text="📋 复制验证码", bg="#e0e0e0"))


if __name__ == "__main__":
    root = tk.Tk()
    app = TOTPApp(root)
    root.mainloop()