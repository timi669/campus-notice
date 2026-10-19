// pages/login/login.js
const app = getApp();
const { api } = require('../../utils/request.js');

Page({
  data: {
    mode: 'login', // login / register
    form: {
      username: '',
      password: '',
      nickname: '',
      confirm: '',
    },
    submitting: false,
    agree: true,
  },

  switchMode(e) {
    const mode = e.currentTarget.dataset.mode;
    this.setData({ mode });
  },

  onInput(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: e.detail.value });
  },

  toggleAgree() {
    this.setData({ agree: !this.data.agree });
  },

  validate() {
    const { username, password, nickname, confirm } = this.data.form;
    if (!username || username.trim().length < 3) {
      wx.showToast({ title: '用户名至少3位', icon: 'none' });
      return false;
    }
    if (!password || password.length < 6) {
      wx.showToast({ title: '密码至少6位', icon: 'none' });
      return false;
    }
    if (this.data.mode === 'register') {
      if (!nickname || nickname.trim().length < 1) {
        wx.showToast({ title: '请输入昵称', icon: 'none' });
        return false;
      }
      if (password !== confirm) {
        wx.showToast({ title: '两次密码不一致', icon: 'none' });
        return false;
      }
    }
    if (!this.data.agree) {
      wx.showToast({ title: '请同意用户协议', icon: 'none' });
      return false;
    }
    return true;
  },

  async submit() {
    if (!this.validate() || this.data.submitting) return;
    this.setData({ submitting: true });
    try {
      const { username, password, nickname } = this.data.form;
      let res;
      if (this.data.mode === 'register') {
        res = await api.register({ username: username.trim(), password, nickname: nickname.trim() });
      } else {
        res = await api.login({ username: username.trim(), password });
      }
      if (res && res.access_token && res.user) {
        app.setAuthInfo(res.access_token, res.user);
        wx.showToast({
          title: this.data.mode === 'register' ? '注册成功' : '登录成功',
          icon: 'success',
        });
        setTimeout(() => {
          const pages = getCurrentPages();
          if (pages.length > 1) {
            wx.navigateBack();
          } else {
            wx.switchTab({ url: '/pages/index/index' });
          }
        }, 800);
      }
    } catch (e) {
      console.error(e);
    } finally {
      this.setData({ submitting: false });
    }
  },

  async quickAdmin() {
    this.setData({ 'form.username': 'admin', 'form.password': '123456' });
  },

  async quickUser() {
    try {
      let username = 'student' + Math.floor(Math.random() * 1000);
      this.setData({
        mode: 'register',
        'form.username': username,
        'form.password': '123456',
        'form.confirm': '123456',
        'form.nickname': '测试同学',
      });
    } catch (e) {
      console.error(e);
    }
  },
});
