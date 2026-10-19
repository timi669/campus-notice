// pages/notifications/notifications.js
const app = getApp();
const { api } = require('../../utils/request.js');
const { friendlyTime } = require('../../utils/util.js');

Page({
  data: {
    list: [],
    page: 1,
    pageSize: 20,
    total: 0,
    totalPages: 0,
    loading: false,
    hasMore: true,
    filter: 'all', // all / unread
  },

  onLoad() {
    if (!app.requireLogin()) return;
    this.loadList(true);
  },

  onPullDownRefresh() {
    this.loadList(true).then(() => wx.stopPullDownRefresh());
  },

  onReachBottom() {
    if (this.data.hasMore && !this.data.loading) {
      this.loadList(false);
    }
  },

  async loadList(reset = false) {
    if (this.data.loading) return;
    this.setData({ loading: true });
    try {
      const page = reset ? 1 : this.data.page;
      const params = { page, page_size: this.data.pageSize };
      if (this.data.filter === 'unread') {
        params.is_read = 0;
      }
      const data = await api.notificationList(params);
      const items = (data.items || []).map(n => ({
        ...n,
        timeText: friendlyTime(n.created_at),
      }));
      const newList = reset ? items : this.data.list.concat(items);
      this.setData({
        list: newList,
        page: page + 1,
        total: data.total || 0,
        totalPages: data.total_pages || 0,
        hasMore: page < (data.total_pages || 0),
      });
    } catch (e) {
      console.error(e);
    } finally {
      this.setData({ loading: false });
    }
  },

  switchFilter(e) {
    const filter = e.currentTarget.dataset.filter;
    if (filter === this.data.filter) return;
    this.setData({ filter, page: 1, list: [], hasMore: true });
    this.loadList(true);
  },

  async tapItem(e) {
    const item = e.currentTarget.dataset.item;
    // 标记已读
    if (item.is_read === 0) {
      try {
        await api.notificationRead(item.id);
        const list = this.data.list.map(n =>
          n.id === item.id ? { ...n, is_read: 1 } : n
        );
        this.setData({ list });
      } catch (e) { console.error(e); }
    }
    // 跳转到公告详情
    if (item.notice_id) {
      wx.navigateTo({ url: `/pages/detail/detail?id=${item.notice_id}` });
    }
  },

  async markAllRead() {
    if (this.data.list.length === 0) return;
    try {
      await api.notificationReadAll();
      const list = this.data.list.map(n => ({ ...n, is_read: 1 }));
      this.setData({ list });
      wx.showToast({ title: '已全部标记已读', icon: 'success' });
    } catch (e) { console.error(e); }
  },
});
