const $ = (selector) => document.querySelector(selector);

const playlistEl = $('#playlist');
const currentTitleEl = $('#current-title');
const timeMetaEl = $('#time-meta');
const folderLabel = $('#folder-label');
const chipTotal = $('#chip-total');
const chipState = $('#chip-state');
const chipVolume = $('#chip-volume');
const progressEl = $('#progress');
const progressText = $('#progress-text');
const volumeEl = $('#volume');
const toastEl = $('#toast');

let tracks = [];
let currentIndex = -1;
let polling;

function formatTime(seconds) {
  const safe = Number.isFinite(seconds) ? Math.max(0, seconds) : 0;
  const m = Math.floor(safe / 60)
    .toString()
    .padStart(2, '0');
  const s = Math.floor(safe % 60)
    .toString()
    .padStart(2, '0');
  return `${m}:${s}`;
}

function renderPlaylist() {
  playlistEl.innerHTML = '';
  if (!tracks.length) {
    playlistEl.innerHTML = '<p class="muted">请选择音乐文件夹来加载曲目。</p>';
    return;
  }

  tracks.forEach((track, index) => {
    const item = document.createElement('div');
    item.className = `track${index === currentIndex ? ' active' : ''}`;
    const duration = track.duration ? formatTime(track.duration) : '未知时长';
    item.innerHTML = `
      <div>
        <div class="track-title">${track.title}</div>
        <div class="track-meta">${track.filename}</div>
      </div>
      <div class="track-meta">${duration}</div>
    `;
    item.addEventListener('click', () => playIndex(index));
    playlistEl.appendChild(item);
  });
}

function showToast(message) {
  toastEl.textContent = message;
  toastEl.hidden = false;
  clearTimeout(showToast.timer);
  showToast.timer = setTimeout(() => {
    toastEl.hidden = true;
  }, 3200);
}

async function chooseFolder() {
  try {
    const response = await window.pywebview.api.choose_folder();
    tracks = response.tracks || [];
    currentIndex = response.status?.current_index ?? -1;
    folderLabel.textContent = response.folder || '未选择目录';
    chipTotal.textContent = `曲目 · ${tracks.length}`;
    renderPlaylist();
    await refreshStatus();
    showToast('已更新播放列表');
  } catch (err) {
    showToast('选择文件夹失败，请重试');
    console.error(err);
  }
}

async function playIndex(index) {
  try {
    const result = await window.pywebview.api.play(index);
    if (!result.ok) {
      showToast('无法播放该曲目');
      return;
    }
    currentIndex = index;
    renderPlaylist();
    await refreshStatus();
  } catch (err) {
    showToast('播放时出现问题');
    console.error(err);
  }
}

async function togglePause() {
  await window.pywebview.api.toggle_pause();
  await refreshStatus();
}

async function stop() {
  await window.pywebview.api.stop();
  await refreshStatus();
}

async function next() {
  await window.pywebview.api.next();
  await refreshStatus();
}

async function prev() {
  await window.pywebview.api.prev();
  await refreshStatus();
}

async function seek(value) {
  await window.pywebview.api.seek(parseFloat(value));
  await refreshStatus();
}

async function setVolume(value) {
  const res = await window.pywebview.api.set_volume(parseFloat(value));
  chipVolume.textContent = `音量 · ${Math.round((res.volume || value) * 100)}%`;
}

function syncStatusUi(status) {
  currentIndex = status.current_index ?? -1;
  if (status.duration) {
    progressText.textContent = `${formatTime(status.elapsed)} / ${formatTime(status.duration)}`;
  } else {
    progressText.textContent = '00:00 / 00:00';
  }
  progressEl.value = status.progress || 0;
  currentTitleEl.textContent = status.current_title || '未播放';
  timeMetaEl.textContent = progressText.textContent;
  chipState.textContent = `状态 · ${status.playing ? '播放中' : status.paused ? '已暂停' : '空闲'}`;
  chipVolume.textContent = `音量 · ${Math.round((status.volume || 0) * 100)}%`;
  renderPlaylist();
}

async function refreshStatus() {
  try {
    const status = await window.pywebview.api.get_status();
    syncStatusUi(status);
  } catch (err) {
    console.error(err);
  }
}

function startPolling() {
  if (polling) clearInterval(polling);
  polling = setInterval(refreshStatus, 600);
}

function bindEvents() {
  $('#choose-folder').addEventListener('click', chooseFolder);
  $('#btn-play').addEventListener('click', togglePause);
  $('#btn-stop').addEventListener('click', stop);
  $('#btn-next').addEventListener('click', next);
  $('#btn-prev').addEventListener('click', prev);
  $('#btn-refresh').addEventListener('click', refreshStatus);
  progressEl.addEventListener('change', (e) => seek(e.target.value));
  volumeEl.addEventListener('input', (e) => setVolume(e.target.value));
}

window.addEventListener('pywebviewready', async () => {
  bindEvents();
  const initial = await window.pywebview.api.get_tracks();
  tracks = initial.tracks || [];
  folderLabel.textContent = initial.folder || '未选择目录';
  chipTotal.textContent = `曲目 · ${tracks.length}`;
  renderPlaylist();
  await refreshStatus();
  startPolling();
});
