// utils/auth.js
const TOKEN_KEY = 'token';
const USER_KEY = 'userInfo';

function setToken(token) {
  wx.setStorageSync(TOKEN_KEY, token);
}

function getToken() {
  try {
    return wx.getStorageSync(TOKEN_KEY) || '';
  } catch (e) {
    return '';
  }
}

function setUserInfo(info) {
  wx.setStorageSync(USER_KEY, info);
}

function getUserInfo() {
  try {
    return wx.getStorageSync(USER_KEY) || null;
  } catch (e) {
    return null;
  }
}

function clearAuth() {
  wx.removeStorageSync(TOKEN_KEY);
  wx.removeStorageSync(USER_KEY);
}

function isLogin() {
  return !!getToken();
}

function isAdmin() {
  const info = getUserInfo();
  return !!(info && info.role === 'admin');
}

function checkLogin() {
  if (!isLogin()) {
    wx.showModal({
      title: '提示',
      content: '请先登录',
      confirmText: '去登录',
      success: (res) => {
        if (res.confirm) {
          wx.navigateTo({ url: '/pages/login/login' });
        }
      },
    });
    return false;
  }
  return true;
}

module.exports = {
  setToken,
  getToken,
  setUserInfo,
  getUserInfo,
  clearAuth,
  isLogin,
  isAdmin,
  checkLogin,
};
