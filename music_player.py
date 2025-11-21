from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import mutagen
import pygame
import webview

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".aac", ".m4a"}


@dataclass
class Track:
    path: Path
    title: str
    duration: float


class PlayerCore:
    def __init__(self) -> None:
        pygame.mixer.init()
        self.playlist: list[Track] = []
        self.current_index: int = -1
        self.paused = False
        self.volume = 0.75
        self.track_length = 0.0
        self._pause_position = 0.0
        self._lock = threading.Lock()
        self._running = True
        self._started = False
        pygame.mixer.music.set_volume(self.volume)
        self._watcher = threading.Thread(target=self._watch_playback, daemon=True)
        self._watcher.start()

    def load_folder(self, folder: str) -> list[dict[str, Any]]:
        folder_path = Path(folder)
        if not folder_path.is_dir():
            return []

        tracks: list[Track] = []
        for entry in sorted(folder_path.iterdir()):
            if not entry.is_file():
                continue
            if entry.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            title, duration = self._read_metadata(entry)
            tracks.append(Track(path=entry, title=title, duration=duration))

        with self._lock:
            self.playlist = tracks
            self.current_index = 0 if tracks else -1
            self._pause_position = 0.0

        return self.serialize_playlist()

    def serialize_playlist(self) -> list[dict[str, Any]]:
        return [
            {
                "id": idx,
                "title": track.title,
                "filename": track.path.name,
                "duration": track.duration,
            }
            for idx, track in enumerate(self.playlist)
        ]

    def play(self, index: int | None = None) -> bool:
        with self._lock:
            if index is not None:
                if not 0 <= index < len(self.playlist):
                    return False
                self.current_index = index

            if not self.playlist or self.current_index < 0:
                return False

            track = self.playlist[self.current_index]
            pygame.mixer.music.load(track.path.as_posix())
            pygame.mixer.music.play()
            pygame.mixer.music.set_volume(self.volume)
            self.track_length = track.duration
            self.paused = False
            self._pause_position = 0.0
            self._started = True
        return True

    def toggle_pause(self) -> None:
        with self._lock:
            if self.current_index == -1:
                return
            if self.paused:
                pygame.mixer.music.unpause()
                self.paused = False
                self._started = True
            else:
                elapsed_ms = pygame.mixer.music.get_pos()
                if elapsed_ms >= 0:
                    self._pause_position = elapsed_ms / 1000.0
                pygame.mixer.music.pause()
                self.paused = True

    def stop(self) -> None:
        with self._lock:
            pygame.mixer.music.stop()
            self.paused = False
            self._pause_position = 0.0
            self._started = False

    def next_track(self) -> bool:
        return self._advance(1)

    def prev_track(self) -> bool:
        return self._advance(-1)

    def _advance(self, step: int) -> bool:
        with self._lock:
            if not self.playlist:
                return False
            self.current_index = (self.current_index + step) % len(self.playlist)
            track = self.playlist[self.current_index]
            pygame.mixer.music.load(track.path.as_posix())
            pygame.mixer.music.play()
            pygame.mixer.music.set_volume(self.volume)
            self.track_length = track.duration
            self.paused = False
            self._pause_position = 0.0
            self._started = True
        return True

    def set_volume(self, value: float) -> float:
        with self._lock:
            self.volume = max(0.0, min(1.0, value))
            pygame.mixer.music.set_volume(self.volume)
            return self.volume

    def seek(self, percent: float) -> None:
        with self._lock:
            if self.current_index == -1 or self.track_length <= 0:
                return
            percent = max(0.0, min(100.0, percent))
            position = percent / 100.0 * self.track_length
            pygame.mixer.music.play(start=position)
            pygame.mixer.music.set_volume(self.volume)
            self.paused = False
            self._pause_position = position
            self._started = True

    def status(self) -> dict[str, Any]:
        with self._lock:
            elapsed = self._pause_position
            elapsed_ms = pygame.mixer.music.get_pos()
            if elapsed_ms >= 0 and not self.paused:
                elapsed = elapsed_ms / 1000.0
                self._pause_position = elapsed

            percent = 0.0
            if self.track_length > 0:
                percent = min(100.0, (elapsed / self.track_length) * 100)

            current = self.playlist[self.current_index] if self.current_index != -1 else None
            return {
                "playing": bool(self.playlist) and self._started and not self.paused,
                "paused": self.paused,
                "progress": percent,
                "elapsed": elapsed,
                "duration": self.track_length,
                "current_index": self.current_index,
                "current_title": current.title if current else "",
                "playlist_size": len(self.playlist),
                "volume": self.volume,
            }

    def shutdown(self) -> None:
        self._running = False
        self._watcher.join(timeout=1.0)
        pygame.mixer.music.stop()
        pygame.mixer.quit()

    def _watch_playback(self) -> None:
        while self._running:
            time.sleep(0.4)
            with self._lock:
                if not self.playlist or not self._started or self.paused:
                    continue
                if not pygame.mixer.music.get_busy() and self.track_length > 0:
                    self._advance(1)

    def _read_metadata(self, path: Path) -> tuple[str, float]:
        title = path.stem
        duration = 0.0
        try:
            audio = mutagen.File(path)
            if audio is not None:
                duration = float(getattr(audio, "info", None).length or 0.0)
                if getattr(audio, "tags", None):
                    for key in ("TIT2", "TITLE", "title", "\u00a9nam"):
                        if key in audio.tags:
                            raw = audio.tags[key]
                            try:
                                title = str(raw.text[0]) if hasattr(raw, "text") else str(raw[0])
                            except Exception:
                                title = str(raw)
                            break
        except Exception:
            pass
        return title, duration


def resource_path(*parts: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base.joinpath(*parts)


class WebAPI:
    def __init__(self, player: PlayerCore) -> None:
        self.player = player
        self.current_folder = ""

    def choose_folder(self) -> dict[str, Any]:
        selection = webview.create_file_dialog(webview.FOLDER_DIALOG)
        if selection:
            self.current_folder = selection[0]
            tracks = self.player.load_folder(self.current_folder)
        else:
            tracks = self.player.serialize_playlist()
        return {"folder": self.current_folder, "tracks": tracks, "status": self.player.status()}

    def get_tracks(self) -> dict[str, Any]:
        return {"folder": self.current_folder, "tracks": self.player.serialize_playlist()}

    def play(self, index: int) -> dict[str, Any]:
        ok = self.player.play(index)
        return {"ok": ok, "status": self.player.status()}

    def toggle_pause(self) -> dict[str, Any]:
        self.player.toggle_pause()
        return self.player.status()

    def stop(self) -> dict[str, Any]:
        self.player.stop()
        return self.player.status()

    def next(self) -> dict[str, Any]:
        self.player.next_track()
        return self.player.status()

    def prev(self) -> dict[str, Any]:
        self.player.prev_track()
        return self.player.status()

    def set_volume(self, value: float) -> dict[str, Any]:
        volume = self.player.set_volume(value)
        return {"volume": volume}

    def seek(self, percent: float) -> dict[str, Any]:
        self.player.seek(percent)
        return self.player.status()

    def get_status(self) -> dict[str, Any]:
        return self.player.status()


def main() -> None:
    player = PlayerCore()
    api = WebAPI(player)
    index_path = resource_path("ui", "index.html")
    window = webview.create_window(
        "NeonGroove - 炫酷音乐播放器",
        url=index_path.as_uri(),
        js_api=api,
        width=1080,
        height=720,
    )

    try:
        webview.start(debug=False)
    finally:
        if window:
            player.shutdown()


if __name__ == "__main__":
    main()
