# NeonGroove 音乐播放器

一个酷炫的桌面音乐播放器原型，使用 Python 播放内核 + HTML/CSS/JavaScript 前端（通过 PyWebview 封装）构建。支持文件夹一键导入播放列表、播放控制、进度拖动与音量调节，可在 Windows 上通过 PyInstaller 打包为 `.exe`。

## 运行

```bash
python -m venv .venv
source .venv/bin/activate  # Windows 使用 .venv\\Scripts\\activate
pip install -r requirements.txt
python music_player.py
```

启动后点击「选择音乐文件夹」，即可批量导入目录内的音频文件（支持 MP3/WAV/OGG/FLAC/AAC/M4A）。

## 打包为 Windows 可执行文件

在 Windows 环境下安装 PyInstaller 后执行：

```powershell
pyinstaller --noconsole --onefile --add-data "ui;ui" --name NeonGroove music_player.py
```

生成的 `dist/NeonGroove.exe` 即可分发使用。

### 直接从 GitHub 下载 exe

仓库已内置 GitHub Actions 工作流，会在拉取请求和 main 分支推送时自动构建 `NeonGroove.exe` 并上传为构件。

1. 打开仓库的 **Actions** 页面，选择最新的 "Build Windows EXE" 工作流运行。
2. 在运行详情底部找到 **Artifacts**，点击 `NeonGroove-exe` 即可下载构建好的 `NeonGroove.exe`。

## 功能特性
- HTML/CSS/JavaScript 打造的炫酷 UI，通过 PyWebview 封装为桌面窗口
- 选择音乐文件夹自动建立播放列表，显示文件名与元数据标题
- 播放、暂停/继续、停止、上一曲、下一曲
- 进度条拖动定位、播放时间显示，前后端轮询保持进度同步
- 音量控制，霓虹风卡片式界面

## 依赖
- Python 3.10+
- pygame 2.5+
- mutagen 1.47+
- pywebview 4.4+
