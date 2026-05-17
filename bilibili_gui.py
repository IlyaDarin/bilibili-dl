"""
bilibili_gui.py — tkinter GUI for Bilibili downloader (Windows-friendly)
"""
import json
import os
import re
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from bilibili_dl import (
    QUALITY_MAP,
    get_bvid,
    get_metadata,
    get_playurl,
    download_file,
    quality_name,
)


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bilibili Downloader")
        self.root.geometry("520x280")
        self.root.resizable(False, False)

        # URL
        tk.Label(self.root, text="Ссылка (b23.tv / BV...):").pack(anchor="w", padx=10, pady=(10, 0))
        self.url_entry = tk.Entry(self.root, width=70)
        self.url_entry.pack(padx=10, pady=(2, 5))
        self.url_entry.focus()

        # Quality
        qframe = tk.Frame(self.root)
        qframe.pack(fill="x", padx=10, pady=2)
        tk.Label(qframe, text="Качество:").pack(side="left")
        self.quality_var = tk.StringVar(value="720p")
        qcombo = ttk.Combobox(qframe, textvariable=self.quality_var, values=list(QUALITY_MAP.keys()), state="readonly", width=10)
        qcombo.pack(side="left", padx=(10, 0))

        # Info
        self.info_var = tk.StringVar(value="")
        self.info_label = tk.Label(self.root, textvariable=self.info_var, wraplength=480, justify="left", fg="#555")
        self.info_label.pack(padx=10, pady=5, fill="x")

        # Progress
        self.progress = ttk.Progressbar(self.root, mode="determinate")
        self.progress.pack(padx=10, pady=5, fill="x")
        self.progress_label = tk.Label(self.root, text="", fg="#888", font=("", 9))
        self.progress_label.pack()

        # Buttons
        bframe = tk.Frame(self.root)
        bframe.pack(pady=10)
        self.dl_btn = tk.Button(bframe, text="Скачать", command=self.download, width=12, height=1)
        self.dl_btn.pack(side="left", padx=5)
        tk.Button(bframe, text="Выход", command=self.root.quit, width=8).pack(side="left", padx=5)

        self.downloading = False

    def run(self):
        self.root.mainloop()

    def set_info(self, text, fg="#333"):
        self.info_var.set(text)
        self.info_label.config(fg=fg)

    def download(self):
        if self.downloading:
            return
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Ошибка", "Вставьте ссылку")
            return

        quality = QUALITY_MAP[self.quality_var.get()]
        self.downloading = True
        self.dl_btn.config(state="disabled", text="Скачивание...")
        self.progress["value"] = 0
        self.progress_label["text"] = ""

        def _progress(dl, total):
            if total:
                pct = min(int(dl / total * 100), 100)
                mb = dl / 1024 / 1024
                total_mb = total / 1024 / 1024
                self.root.after(0, lambda: self.progress.configure(value=pct))
                self.root.after(0, lambda: self.progress_label.configure(text=f"{mb:.0f} / {total_mb:.0f} MB ({pct}%)"))
            else:
                self.root.after(0, lambda: self.progress_label.configure(text=f"{dl/1024/1024:.0f} MB"))

        def _work():
            try:
                self.root.after(0, lambda: self.set_info("Определяю видео...", "#333"))
                bvid = get_bvid(url)
                meta = get_metadata(bvid)
                self.root.after(0, lambda: self.set_info(
                    f"🎬 {meta['title']}  ⏱ {meta['duration']//60}:{meta['duration']%60:02d}",
                    "#333"
                ))

                play = get_playurl(bvid, meta["cid"], quality)
                q_actual = quality_name(play["actual_quality"])
                size_mb = play["size_bytes"] / 1024 / 1024
                self.root.after(0, lambda: self.set_info(
                    f"🎬 {meta['title']}  ⏱ {meta['duration']//60}:{meta['duration']%60:02d}  📐 {q_actual}  📦 {size_mb:.0f} MB",
                    "#333"
                ))

                self.root.after(0, lambda: self.root.withdraw())
                folder = filedialog.askdirectory(title="Куда сохранить?")
                self.root.after(0, lambda: self.root.deiconify())
                if not folder:
                    self._done()
                    return

                safe = re.sub(r'[\\/:*?"<>|]', "_", meta["title"])
                out = os.path.join(folder, f"{safe}.mp4")

                self.root.after(0, lambda: self.set_info(f"⬇ Скачиваю... {q_actual} {size_mb:.0f} MB", "#333"))

                try:
                    download_file(play["primary_url"], out, _progress)
                except Exception:
                    if play["backup_urls"]:
                        self.root.after(0, lambda: self.set_info("Первичный сервер не ответил, пробую backup...", "#e67e22"))
                        backup = play["backup_urls"][0]
                        download_file(backup, out, _progress)
                    else:
                        raise

                self.root.after(0, lambda: self.set_info(
                    f"✅ Сохранено: {os.path.basename(out)} ({size_mb:.0f} MB)", "green"
                ))
                self.root.after(0, lambda: messagebox.showinfo(
                    "Готово", f"Скачано:\n{out}\n\n{size_mb:.0f} MB / {q_actual}"
                ))

            except Exception as e:
                self.root.after(0, lambda: self.set_info(f"❌ {e}", "red"))
                self.root.after(0, lambda: messagebox.showerror("Ошибка", str(e)))
            finally:
                self._done()

        t = threading.Thread(target=_work, daemon=True)
        t.start()

    def _done(self):
        self.downloading = False
        self.dl_btn.config(state="normal", text="Скачать")


if __name__ == "__main__":
    App().run()
