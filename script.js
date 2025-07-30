const THEME_KEY = 'theme';
const toggleButton = document.getElementById('theme-toggle');

// 根据主题名称设置页面属性
function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
}

// 从本地存储获取主题，默认为 light
function getStoredTheme() {
    return localStorage.getItem(THEME_KEY) || 'light';
}

// 切换主题并保存到本地
function toggleTheme() {
    const current = getStoredTheme();
    const next = current === 'light' ? 'dark' : 'light';
    localStorage.setItem(THEME_KEY, next);
    applyTheme(next);
}

// 初始化并绑定事件
document.addEventListener('DOMContentLoaded', () => {
    applyTheme(getStoredTheme());
    toggleButton.addEventListener('click', toggleTheme);
});
