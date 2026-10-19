// utils/request.js
const config = require('./config.js');
const auth = require('./auth.js');

function request(options) {
  return new Promise((resolve, reject) => {
    const token = auth.getToken();
    const header = Object.assign(
      { 'Content-Type': 'application/json' },
      options.header || {}
    );
    if (token) {
      header['Authorization'] = 'Bearer ' + token;
    }

    let url = options.url;
    if (url && !/^https?:\/\//.test(url)) {
      url = config.baseUrl + url;
    }

    wx.request({
      url,
      method: options.method || 'GET',
      data: options.data || {},
      header,
      timeout: options.timeout || 15000,
      success: (res) => {
        const data = res.data;
        if (res.statusCode === 401) {
          auth.clearAuth();
          const app = getApp();
          if (app) {
            app.globalData.token = null;
            app.globalData.userInfo = null;
          }
          wx.showToast({ title: '请重新登录', icon: 'none' });
          setTimeout(() => {
            const pages = getCurrentPages();
            const current = pages[pages.length - 1];
            if (current && current.route !== 'pages/login/login') {
              wx.navigateTo({ url: '/pages/login/login' });
            }
          }, 800);
          reject(data || { code: 401, message: '未登录' });
          return;
        }
        if (res.statusCode === 403) {
          wx.showToast({ title: '没有权限', icon: 'none' });
          reject(data || { code: 403, message: '没有权限' });
          return;
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          if (data && typeof data === 'object' && 'code' in data) {
            if (data.code === 0 || data.code === 200) {
              resolve(data.data !== undefined ? data.data : data);
            } else {
              wx.showToast({
                title: data.message || '请求失败',
                icon: 'none',
              });
              reject(data);
            }
          } else {
            resolve(data);
          }
        } else {
          wx.showToast({
            title: (data && (data.message || data.detail)) || `请求错误(${res.statusCode})`,
            icon: 'none',
          });
          reject(data || { code: res.statusCode, message: '网络错误' });
        }
      },
      fail: (err) => {
        console.error('Request failed:', err);
        wx.showToast({ title: '网络连接失败', icon: 'none' });
        reject(err);
      },
    });
  });
}

function get(url, data, options = {}) {
  return request(Object.assign({ url, method: 'GET', data }, options));
}

function post(url, data, options = {}) {
  return request(Object.assign({ url, method: 'POST', data }, options));
}

function put(url, data, options = {}) {
  return request(Object.assign({ url, method: 'PUT', data }, options));
}

function del(url, data, options = {}) {
  return request(Object.assign({ url, method: 'DELETE', data }, options));
}

const api = {
  // auth
  register: (d) => post('/api/auth/register', d),
  login: (d) => post('/api/auth/login', d),
  getMe: () => get('/api/auth/me'),

  // users
  updateMe: (d) => put('/api/users/me', d),
  changePassword: (d) => put('/api/users/me/password', d),
  deactivateMe: () => del('/api/users/me'),
  userList: (p) => get('/api/users', p),
  deleteUser: (id) => del(`/api/users/${id}`),
  updateRole: (id, role) => put(`/api/users/${id}/role`, { role }),

  // categories
  categoryList: (p) => get('/api/categories', p),
  categoryCreate: (d) => post('/api/categories', d),
  categoryUpdate: (id, d) => put(`/api/categories/${id}`, d),
  categoryDelete: (id) => del(`/api/categories/${id}`),

  // notices
  noticeList: (p) => get('/api/notices', p),
  topNotices: (limit = 5) => get('/api/notices/top', { limit }),
  noticeDetail: (id) => get(`/api/notices/${id}`),
  noticeCreate: (d) => post('/api/notices', d),
  noticeUpdate: (id, d) => put(`/api/notices/${id}`, d),
  noticeDelete: (id) => del(`/api/notices/${id}`),
  toggleFavorite: (id) => post(`/api/notices/${id}/favorite`),
  toggleLike: (id) => post(`/api/notices/${id}/like`),
  myFavorites: (p) => get('/api/notices/my/favorites', p),
  myPublished: (p) => get('/api/notices/my/published', p),
  hotKeywords: (limit = 10) => get('/api/notices/hot-keywords', { limit }),

  // stats
  overview: () => get('/api/stats'),

  // notifications
  notificationList: (p) => get('/api/notifications', p),
  notificationUnread: () => get('/api/notifications/unread-count'),
  notificationRead: (id) => put(`/api/notifications/${id}/read`),
  notificationReadAll: () => put('/api/notifications/read-all'),

  // comments
  commentList: (noticeId, p) => get('/api/comments', { notice_id: noticeId, ...(p || {}) }),
  commentCreate: (noticeId, content) => post('/api/comments', { notice_id: noticeId, content }),
  commentDelete: (id) => del(`/api/comments/${id}`),

  // operation logs（管理员）
  operationLogList: (p) => get('/api/operation-logs', p),
};

/**
 * 上传文件到后端 /api/upload
 * @param {string} filePath 本地临时文件路径
 * @returns {Promise<string>} 上传后的文件 URL
 */
function uploadFile(filePath) {
  return new Promise((resolve, reject) => {
    const token = auth.getToken();
    wx.uploadFile({
      url: config.baseUrl + '/api/upload',
      filePath,
      name: 'file',
      header: token ? { Authorization: 'Bearer ' + token } : {},
      success: (res) => {
        try {
          const data = JSON.parse(res.data);
          if (data.code === 0 && data.data && data.data.url) {
            resolve(data.data.url);
          } else {
            wx.showToast({ title: data.message || '上传失败', icon: 'none' });
            reject(data);
          }
        } catch (e) {
          wx.showToast({ title: '上传失败', icon: 'none' });
          reject(e);
        }
      },
      fail: (err) => {
        wx.showToast({ title: '网络连接失败', icon: 'none' });
        reject(err);
      },
    });
  });
}

/**
 * 下载 CSV 导出内容（管理员）
 * 小程序无法直接打开 CSV 文件，这里以文本方式取回，供复制到剪贴板后粘贴到 Excel。
 * @param {string} path 接口路径，如 /api/users/export.csv
 * @returns {Promise<string>} CSV 文本
 */
function exportCsv(path) {
  return new Promise((resolve, reject) => {
    const token = auth.getToken();
    wx.request({
      url: config.baseUrl + path,
      method: 'GET',
      header: token ? { Authorization: 'Bearer ' + token } : {},
      dataType: 'text', // 关键：不按 JSON 解析，直接拿原始 CSV 文本
      timeout: 20000,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data || '');
        } else {
          wx.showToast({ title: '导出失败（' + res.statusCode + '）', icon: 'none' });
          reject(res);
        }
      },
      fail: (err) => {
        wx.showToast({ title: '网络连接失败', icon: 'none' });
        reject(err);
      },
    });
  });
}

module.exports = {
  request,
  get,
  post,
  put,
  del,
  uploadFile,
  exportCsv,
  api,
};
