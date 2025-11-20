# NeonGroove 音乐播放器

一个酷炫的桌面音乐播放器原型，使用 Python + Tkinter + pygame 构建。支持播放列表管理、基础播放控制、进度拖动与音量调节，可在 Windows 上通过 PyInstaller 打包为 `.exe`。

## 运行

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\\Scripts\\activate
pip install -r requirements.txt
python music_player.py
```

## 打包为 Windows 可执行文件

在 Windows 环境下安装 PyInstaller 后执行：

```powershell
pyinstaller --noconsole --onefile --name NeonGroove music_player.py
```

生成的 `dist/NeonGroove.exe` 即可分发使用。

## 功能特性
- 支持 MP3/WAV/OGG/FLAC 导入，自动建立播放列表
- 播放、暂停/继续、停止、上一曲、下一曲
- 进度条拖动定位、播放时间显示
- 音量控制，深色霓虹风格界面

## 依赖
- Python 3.10+
- pygame 2.5+
- mutagen 1.47+
