// pages/profile/profile.js
const app = getApp();
const { api } = require('../../utils/request.js');
const auth = require('../../utils/auth.js');

Page({
  data: {
    userInfo: null,
    isLogin: false,
    isAdmin: false,
    unreadCount: 0,
    menu: [
      { icon: '🔔', key: 'notifications', title: '消息通知', desc: '查看系统通知' },
      { icon: '⭐', key: 'fav', title: '我的收藏', desc: '查看收藏的公告' },
      { icon: '📤', key: 'pub', title: '我发布的', desc: '管理员可见', adminOnly: true },
    ],
    adminMenu: [
      { icon: '✏️', key: 'notice-edit', title: '发布公告', desc: '创建新公告' },
      { icon: '📋', key: 'notice-list', title: '公告管理', desc: '编辑/删除公告' },
      { icon: '📂', key: 'category-manage', title: '分类管理', desc: '维护公告分类' },
      { icon: '👥', key: 'user-manage', title: '用户管理', desc: '管理系统用户' },
      { icon: '📊', key: 'stats', title: '数据统计', desc: '查看运营数据' },
    ],
    settings: [
      { icon: '⚙️', key: 'edit', title: '修改资料' },
      { icon: '🔐', key: 'pwd', title: '修改密码' },
      { icon: '🗑️', key: 'deactivate', title: '注销账号' },
    ],
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 3 });
    }
    this.refreshUser();
    if (this.data.isLogin) {
      this.loadUnreadCount();
    }
  },

  async loadUnreadCount() {
    try {
      const data = await api.notificationUnread();
      this.setData({ unreadCount: data.unread_count || 0 });
    } catch (e) { /* ignore */ }
  },

  refreshUser() {
    const info = app.globalData.userInfo || auth.getUserInfo();
    const token = app.globalData.token || auth.getToken();
    this.setData({
      isLogin: !!token,
      userInfo: info,
      isAdmin: !!(info && info.role === 'admin'),
    });
    if (token) {
      this.loadUnreadCount();
    }
  },

  goLogin() {
    wx.navigateTo({ url: '/pages/login/login' });
  },

  onMenuTap(e) {
    if (!app.requireLogin()) return;
    const key = e.currentTarget.dataset.key;
    const adminOnly = e.currentTarget.dataset.admin;
    if (adminOnly && !this.data.isAdmin) {
      wx.showToast({ title: '需要管理员权限', icon: 'none' });
      return;
    }
    switch (key) {
      case 'notifications':
        wx.navigateTo({ url: '/pages/notifications/notifications' });
        break;
      case 'fav':
        wx.navigateTo({ url: '/pages/favorites/favorites' });
        break;
      case 'pub':
        wx.navigateTo({ url: '/pages/admin/notice-list' });
        break;
      case 'notice-edit':
        wx.navigateTo({ url: '/pages/admin/notice-edit' });
        break;
      case 'notice-list':
        wx.navigateTo({ url: '/pages/admin/notice-list' });
        break;
      case 'category-manage':
        wx.navigateTo({ url: '/pages/admin/category-manage' });
        break;
      case 'user-manage':
        wx.navigateTo({ url: '/pages/admin/user-manage' });
        break;
      case 'stats':
        wx.navigateTo({ url: '/pages/admin/stats' });
        break;
      case 'edit':
        this.editProfile();
        break;
      case 'pwd':
        this.editPassword();
        break;
      case 'deactivate':
        this.deactivateAccount();
        break;
    }
  },

  editProfile() {
    const user = this.data.userInfo || {};
    wx.showModal({
      title: '修改昵称',
      editable: true,
      placeholderText: '请输入新昵称',
      content: user.nickname || '',
      success: async (res) => {
        if (res.confirm && res.content) {
          try {
            await api.updateMe({ nickname: res.content });
            const info = await api.getMe();
            app.setAuthInfo(auth.getToken(), info);
            this.refreshUser();
            wx.showToast({ title: '修改成功', icon: 'success' });
          } catch (e) { console.error(e); }
        }
      },
    });
  },

  editPassword() {
    wx.showModal({
      title: '输入旧密码',
      editable: true,
      placeholderText: '请输入当前密码',
      success: (res) => {
        if (!res.confirm) return;
        const oldPwd = res.content || '';
        if (!oldPwd) {
          wx.showToast({ title: '请输入旧密码', icon: 'none' });
          return;
        }
        wx.showModal({
          title: '设置新密码',
          editable: true,
          placeholderText: '6-50位，须包含字母和数字',
          success: async (res2) => {
            if (!res2.confirm) return;
            const newPwd = res2.content || '';
            if (newPwd.length < 6) {
              wx.showToast({ title: '密码至少6位', icon: 'none' });
              return;
            }
            try {
              await api.changePassword({ old_password: oldPwd, new_password: newPwd });
              wx.showToast({ title: '修改成功', icon: 'success' });
            } catch (e) { console.error(e); }
          },
        });
      },
    });
  },

  logout() {
    wx.showModal({
      title: '确认退出',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          app.clearAuthInfo();
          auth.clearAuth();
          this.refreshUser();
          wx.showToast({ title: '已退出登录', icon: 'success' });
        }
      },
    });
  },

  deactivateAccount() {
    if (this.data.isAdmin) {
      wx.showToast({ title: '管理员账号不可注销', icon: 'none' });
      return;
    }
    wx.showModal({
      title: '注销账号',
      content: '注销后账号及相关数据将被永久删除，且无法恢复。确定继续吗？',
      confirmText: '确认注销',
      confirmColor: '#e64340',
      success: async (res) => {
        if (!res.confirm) return;
        try {
          await api.deactivateMe();
          app.clearAuthInfo();
          auth.clearAuth();
          wx.showToast({ title: '账号已注销', icon: 'success' });
          setTimeout(() => {
            this.refreshUser();
            wx.switchTab({ url: '/pages/index/index' });
          }, 1000);
        } catch (e) {
          console.error(e);
          wx.showToast({ title: e.detail || '注销失败', icon: 'none' });
        }
      },
    });
  },

  goAdminHome() {
    app.requireAdmin(() => {
      wx.navigateTo({ url: '/pages/admin/index' });
    });
  },
});
