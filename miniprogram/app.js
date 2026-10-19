// app.js
const { checkLogin, getToken, getUserInfo } = require('./utils/auth.js');
const config = require('./utils/config.js');

App({
  globalData: {
    userInfo: null,
    token: null,
    categories: [],
    baseUrl: config.baseUrl,
  },

  onLaunch() {
    const token = getToken();
    const userInfo = getUserInfo();
    if (token && userInfo) {
      this.globalData.token = token;
      this.globalData.userInfo = userInfo;
    }
  },

  setAuthInfo(token, userInfo) {
    this.globalData.token = token;
    this.globalData.userInfo = userInfo;
    wx.setStorageSync('token', token);
    wx.setStorageSync('userInfo', userInfo);
  },

  clearAuthInfo() {
    this.globalData.token = null;
    this.globalData.userInfo = null;
    wx.removeStorageSync('token');
    wx.removeStorageSync('userInfo');
  },

  isLogin() {
    return !!this.globalData.token;
  },

  isAdmin() {
    return this.globalData.userInfo && this.globalData.userInfo.role === 'admin';
  },

  requireLogin(callback) {
    if (this.isLogin()) {
      callback && callback();
      return true;
    }
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
  },

  requireAdmin(callback) {
    if (!this.isLogin()) {
      wx.showModal({
        title: '提示',
        content: '请先登录管理员账号',
        confirmText: '去登录',
        success: (res) => {
          if (res.confirm) wx.navigateTo({ url: '/pages/login/login' });
        },
      });
      return false;
    }
    if (!this.isAdmin()) {
      wx.showToast({ title: '需要管理员权限', icon: 'none' });
      return false;
    }
    callback && callback();
    return true;
  },
});
