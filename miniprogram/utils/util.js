// utils/util.js
const config = require('./config.js');

function formatTime(date, withSec = true) {
  if (!date) return '';
  if (typeof date === 'string' || typeof date === 'number') {
    date = new Date(date);
  }
  const pad = (n) => n < 10 ? '0' + n : '' + n;
  const year = date.getFullYear();
  const month = pad(date.getMonth() + 1);
  const day = pad(date.getDate());
  const hour = pad(date.getHours());
  const minute = pad(date.getMinutes());
  const second = pad(date.getSeconds());
  if (withSec) {
    return `${year}-${month}-${day} ${hour}:${minute}:${second}`;
  }
  return `${year}-${month}-${day} ${hour}:${minute}`;
}

function formatDate(date) {
  if (!date) return '';
  if (typeof date === 'string' || typeof date === 'number') {
    date = new Date(date);
  }
  const pad = (n) => n < 10 ? '0' + n : '' + n;
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function friendlyTime(dateStr) {
  if (!dateStr) return '';
  const date = typeof dateStr === 'string' || typeof dateStr === 'number' ? new Date(dateStr) : dateStr;
  const now = new Date();
  const diff = Math.floor((now - date) / 1000);
  if (diff < 60) return '刚刚';
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前';
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前';
  if (diff < 86400 * 30) return Math.floor(diff / 86400) + '天前';
  if (diff < 86400 * 365) return formatDate(date).slice(5);
  return formatDate(date);
}

function stripHtml(html) {
  if (!html) return '';
  return String(html).replace(/<[^>]+>/g, '').replace(/&nbsp;/g, ' ').trim();
}

function debounce(fn, delay = 500) {
  let timer = null;
  return function (...args) {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

function throttle(fn, delay = 500) {
  let last = 0;
  return function (...args) {
    const now = Date.now();
    if (now - last >= delay) {
      last = now;
      fn.apply(this, args);
    }
  };
}

function randomColor() {
  const colors = ['#4F7DFB', '#37C6C4', '#FF976A', '#F56C6C', '#8F6FE8', '#09BB07'];
  return colors[Math.floor(Math.random() * colors.length)];
}

/**
 * 将后端返回的相对 URL 转为完整 URL
 * 例如 /uploads/xxx.jpg -> http://127.0.0.1:8000/uploads/xxx.jpg
 * 绝对 URL（http/https 开头）原样返回
 */
function resolveUrl(url) {
  if (!url) return '';
  if (/^https?:\/\//.test(url)) return url;
  return config.baseUrl + url;
}

module.exports = {
  formatTime,
  formatDate,
  friendlyTime,
  stripHtml,
  debounce,
  throttle,
  randomColor,
  resolveUrl,
};
