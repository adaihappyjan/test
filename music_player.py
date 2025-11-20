import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import mutagen
import pygame


class MusicPlayer:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("NeonGroove - 音乐播放器")
        self.root.geometry("720x480")
        self.root.configure(bg="#0f1620")
        self.root.minsize(640, 420)

        pygame.mixer.init()
        self.playlist: list[str] = []
        self.current_index = -1
        self.paused = False
        self.track_length = 0.0

        self._build_ui()
        self._start_progress_timer()

    def _build_ui(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#0f1620")
        style.configure("TLabel", background="#0f1620", foreground="#e5e5e5", font=("Segoe UI", 11))
        style.configure("TButton", background="#1f2937", foreground="#e5e5e5", padding=8, font=("Segoe UI", 11))
        style.map("TButton", background=[("active", "#2563eb")])
        style.configure("Horizontal.TScale", background="#0f1620")

        header = ttk.Frame(self.root)
        header.pack(fill=tk.X, padx=16, pady=(14, 8))
        ttk.Label(header, text="NeonGroove - 氛围感音乐播放器", font=("Segoe UI", 16, "bold"), foreground="#60a5fa").pack(side=tk.LEFT)

        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=8)

        playlist_frame = ttk.Frame(main_frame)
        playlist_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(playlist_frame, text="播放列表").pack(anchor=tk.W)
        self.playlist_box = tk.Listbox(
            playlist_frame,
            bg="#111827",
            fg="#e5e5e5",
            selectbackground="#2563eb",
            selectforeground="#ffffff",
            activestyle="none",
            font=("Consolas", 11),
        )
        self.playlist_box.pack(fill=tk.BOTH, expand=True, padx=(0, 10), pady=(8, 0))

        controls_frame = ttk.Frame(main_frame)
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y)

        ttk.Label(controls_frame, text="播放控制").pack(anchor=tk.W)
        buttons = ttk.Frame(controls_frame)
        buttons.pack(fill=tk.X, pady=8)

        ttk.Button(buttons, text="▶ 播放", command=self.play_selected).grid(row=0, column=0, padx=4, pady=4, sticky=tk.EW)
        ttk.Button(buttons, text="⏸ 暂停/继续", command=self.pause_resume).grid(row=0, column=1, padx=4, pady=4, sticky=tk.EW)
        ttk.Button(buttons, text="⏹ 停止", command=self.stop).grid(row=1, column=0, padx=4, pady=4, sticky=tk.EW)
        ttk.Button(buttons, text="⏮ 上一曲", command=self.prev_track).grid(row=1, column=1, padx=4, pady=4, sticky=tk.EW)
        ttk.Button(buttons, text="⏭ 下一曲", command=self.next_track).grid(row=2, column=0, padx=4, pady=4, sticky=tk.EW)
        ttk.Button(buttons, text="➕ 添加音频", command=self.add_files).grid(row=2, column=1, padx=4, pady=4, sticky=tk.EW)
        ttk.Button(buttons, text="➖ 移除选中", command=self.remove_selected).grid(row=3, column=0, padx=4, pady=4, sticky=tk.EW)

        for i in range(2):
            buttons.columnconfigure(i, weight=1)

        ttk.Label(controls_frame, text="进度").pack(anchor=tk.W, pady=(12, 2))
        self.progress = tk.DoubleVar(value=0)
        self.progress_scale = ttk.Scale(controls_frame, variable=self.progress, from_=0, to=100, command=self._seek)
        self.progress_scale.pack(fill=tk.X)

        self.time_label = ttk.Label(controls_frame, text="00:00 / 00:00", font=("Segoe UI", 10))
        self.time_label.pack(anchor=tk.W, pady=(4, 10))

        ttk.Label(controls_frame, text="音量").pack(anchor=tk.W, pady=(8, 2))
        self.volume = tk.DoubleVar(value=0.7)
        self.volume_scale = ttk.Scale(controls_frame, variable=self.volume, from_=0, to=1, orient=tk.HORIZONTAL, command=self._set_volume)
        self.volume_scale.pack(fill=tk.X)
        pygame.mixer.music.set_volume(self.volume.get())

    def add_files(self) -> None:
        files = filedialog.askopenfilenames(
            filetypes=[("音频文件", "*.mp3 *.wav *.ogg *.flac"), ("所有文件", "*.*")]
        )
        if not files:
            return
        for fpath in files:
            if fpath not in self.playlist:
                self.playlist.append(fpath)
                self.playlist_box.insert(tk.END, os.path.basename(fpath))

    def remove_selected(self) -> None:
        selection = list(self.playlist_box.curselection())
        if not selection:
            return
        for index in reversed(selection):
            del self.playlist[index]
            self.playlist_box.delete(index)
        if self.current_index >= len(self.playlist):
            self.current_index = len(self.playlist) - 1

    def play_selected(self) -> None:
        selection = self.playlist_box.curselection()
        if selection:
            self.current_index = selection[0]
        if not self.playlist or self.current_index == -1:
            messagebox.showinfo("提示", "请先添加音频并选择一首曲目")
            return
        self._play_track(self.current_index)

    def _play_track(self, index: int) -> None:
        track = self.playlist[index]
        try:
            pygame.mixer.music.load(track)
            pygame.mixer.music.play()
            self.paused = False
            self._update_track_length(track)
            self._highlight_current()
        except pygame.error as exc:
            messagebox.showerror("无法播放", f"加载 {os.path.basename(track)} 失败:\n{exc}")

    def pause_resume(self) -> None:
        if pygame.mixer.music.get_busy():
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
            else:
                pygame.mixer.music.pause()
                self.paused = True

    def stop(self) -> None:
        pygame.mixer.music.stop()
        self.paused = False
        self.progress.set(0)
        self.time_label.config(text="00:00 / 00:00")

    def next_track(self) -> None:
        if not self.playlist:
            return
        self.current_index = (self.current_index + 1) % len(self.playlist)
        self._play_track(self.current_index)

    def prev_track(self) -> None:
        if not self.playlist:
            return
        self.current_index = (self.current_index - 1) % len(self.playlist)
        self._play_track(self.current_index)

    def _highlight_current(self) -> None:
        self.playlist_box.selection_clear(0, tk.END)
        if self.current_index != -1:
            self.playlist_box.selection_set(self.current_index)
            self.playlist_box.see(self.current_index)

    def _update_track_length(self, track: str) -> None:
        try:
            audio = mutagen.File(track)
            self.track_length = float(getattr(audio, "info", None).length or 0)
        except Exception:
            self.track_length = 0.0
        self.progress.set(0)
        self._update_time_label(0)

    def _seek(self, _value: str) -> None:
        if self.track_length <= 0:
            return
        position = self.progress.get() / 100 * self.track_length
        try:
            pygame.mixer.music.play(start=position)
            pygame.mixer.music.set_volume(self.volume.get())
            if self.current_index == -1 and self.playlist:
                self.current_index = 0
            self.paused = False
        except pygame.error:
            pass

    def _set_volume(self, _value: str) -> None:
        pygame.mixer.music.set_volume(self.volume.get())

    def _start_progress_timer(self) -> None:
        self._update_progress()

    def _update_progress(self) -> None:
        if pygame.mixer.music.get_busy() and not self.paused and self.track_length > 0:
            elapsed_ms = pygame.mixer.music.get_pos()
            if elapsed_ms >= 0:
                elapsed = elapsed_ms / 1000.0
                if elapsed >= self.track_length - 0.5:
                    self.next_track()
                else:
                    percent = min(100, (elapsed / self.track_length) * 100)
                    self.progress.set(percent)
                    self._update_time_label(elapsed)
        self.root.after(300, self._update_progress)

    def _update_time_label(self, elapsed: float) -> None:
        def fmt(seconds: float) -> str:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes:02d}:{secs:02d}"

        self.time_label.config(text=f"{fmt(elapsed)} / {fmt(self.track_length)}")


def main() -> None:
    root = tk.Tk()
    MusicPlayer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
