// pages/admin/index.js
const app = getApp();
const { api } = require('../../utils/request.js');

Page({
  data: {
    loading: true,
    stats: {
      user_count: 0,
      student_count: 0,
      admin_count: 0,
      notice_count: 0,
      draft_count: 0,
      category_count: 0,
      favorite_count: 0,
      views_sum: 0,
    },
    recent_notices: [],
    hot_notices: [],
    category_stats: [],
  },

  onLoad() {
    if (!app.requireAdmin()) return;
  },

  onShow() {
    if (app.isAdmin()) this.loadData();
  },

  async loadData() {
    this.setData({ loading: true });
    try {
      const data = await api.overview();
      if (data) {
        this.setData({
          stats: {
            user_count: data.user_count || 0,
            student_count: data.student_count || 0,
            admin_count: data.admin_count || 0,
            notice_count: data.notice_count || 0,
            draft_count: data.draft_count || 0,
            category_count: data.category_count || 0,
            favorite_count: data.favorite_count || 0,
            views_sum: data.views_sum || 0,
          },
          recent_notices: data.recent_notices || [],
          hot_notices: data.hot_notices || [],
          category_stats: data.category_stats || [],
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
      this.setData({ loading: false });
    }
  },

  go(e) {
    const path = e.currentTarget.dataset.path;
    if (!path) return;
    wx.navigateTo({ url: path });
  },

  goNotice(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  },
});
