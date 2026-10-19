// pages/admin/user-manage.js
const app = getApp();
const { api } = require('../../utils/request.js');
const config = require('../../utils/config.js');

Page({
  data: {
    list: [],
    page: 1,
    pageSize: config.pageSize,
    total: 0,
    totalPages: 0,
    loading: false,
    noMore: false,
    keyword: '',
    roleFilter: 'all',
  },

  onLoad() { if (!app.requireAdmin()) return; },

  onShow() {
    if (app.isAdmin()) {
      this.setData({ page: 1, noMore: false });
      this.loadList(true);
    }
  },

  onPullDownRefresh() {
    this.setData({ page: 1, noMore: false });
    this.loadList(true).then(() => wx.stopPullDownRefresh());
  },

  onReachBottom() {
    if (!this.data.noMore && !this.data.loading) this.loadList(false);
  },

  onKeywordInput(e) {
    this.setData({ keyword: e.detail.value });
  },

  search() {
    this.setData({ page: 1, noMore: false });
    this.loadList(true);
  },

  filterRole(e) {
    const r = e.currentTarget.dataset.role;
    this.setData({ roleFilter: r, page: 1, noMore: false });
    this.loadList(true);
  },

  async loadList(refresh) {
    if (this.data.loading) return;
    const page = refresh ? 1 : this.data.page;
    this.setData({ loading: true });
    try {
      const params = { page, page_size: this.data.pageSize };
      if (this.data.keyword) params.keyword = this.data.keyword;
      if (this.data.roleFilter !== 'all') params.role = this.data.roleFilter;
      const res = await api.userList(params) || {};
      let items = res.items || [];
      items = items.map(u => Object.assign({}, u, {
        createdText: (u.created_at || '').slice(0, 10),
        roleText: u.role === 'admin' ? '管理员' : '学生',
      }));
      const total = res.total || 0;
      const newList = refresh ? items : this.data.list.concat(items);
      const totalPages = res.total_pages || 0;
      this.setData({
        list: newList,
        total,
        totalPages,
        page: page + 1,
        noMore: page >= totalPages,
      });
    } catch (e) { console.error(e); }
    finally { this.setData({ loading: false }); }
  },

  toggleRole(e) {
    const id = e.currentTarget.dataset.id;
    const name = e.currentTarget.dataset.name;
    const cur = e.currentTarget.dataset.role;
    const newRole = cur === 'admin' ? 'student' : 'admin';
    wx.showModal({
      title: '修改角色',
      content: `确定将「${name}」${newRole === 'admin' ? '提升为管理员' : '降级为学生'}吗？`,
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.updateRole(id, newRole);
            wx.showToast({ title: '修改成功', icon: 'success' });
            this.loadList(true);
          } catch (e) { console.error(e); }
        }
      },
    });
  },

  deleteUser(e) {
    const id = e.currentTarget.dataset.id;
    const name = e.currentTarget.dataset.name;
    const me = app.globalData.userInfo;
    if (me && me.id === id) {
      wx.showToast({ title: '不能删除自己', icon: 'none' });
      return;
    }
    wx.showModal({
      title: '删除用户',
      content: `确定删除用户「${name}」吗？此操作不可恢复。`,
      confirmColor: '#F56C6C',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.deleteUser(id);
            wx.showToast({ title: '已删除', icon: 'success' });
            this.loadList(true);
          } catch (e) { console.error(e); }
        }
      },
    });
  },
});
