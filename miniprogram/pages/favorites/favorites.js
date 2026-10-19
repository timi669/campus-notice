// pages/favorites/favorites.js
const app = getApp();
const { api } = require('../../utils/request.js');
const { friendlyTime } = require('../../utils/util.js');
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
  },

  onLoad() {
    if (!app.requireLogin()) return;
    this.loadList(true);
  },

  onPullDownRefresh() {
    this.setData({ page: 1, noMore: false });
    this.loadList(true).then(() => wx.stopPullDownRefresh());
  },

  onReachBottom() {
    if (!this.data.noMore && !this.data.loading) this.loadList(false);
  },

  async loadList(refresh) {
    if (this.data.loading) return;
    const page = refresh ? 1 : this.data.page;
    this.setData({ loading: true });
    try {
      const res = await api.myFavorites({ page, page_size: this.data.pageSize });
      const items = (res.items || []).map(n => Object.assign({}, n, { timeText: friendlyTime(n.created_at) }));
      const newList = refresh ? items : this.data.list.concat(items);
      const totalPages = res.total_pages || 0;
      this.setData({
        list: newList,
        total: res.total || 0,
        totalPages,
        page: page + 1,
        noMore: page >= totalPages,
      });
    } catch (e) {
      console.error(e);
    } finally {
      this.setData({ loading: false });
    }
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  },

  async unFavorite(e) {
    const id = e.currentTarget.dataset.id;
    wx.showModal({
      title: '取消收藏',
      content: '确定取消收藏这篇公告吗？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.toggleFavorite(id);
            wx.showToast({ title: '已取消收藏', icon: 'success' });
            this.setData({ page: 1, noMore: false });
            this.loadList(true);
          } catch (e) { console.error(e); }
        }
      },
    });
  },
});
