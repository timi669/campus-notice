// pages/admin/stats.js
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
      comment_count: 0,
      like_count: 0,
      views_sum: 0,
    },
    category_stats: [],
    recent_notices: [],
    hot_notices: [],
    catMax: 0,
  },

  onLoad() { if (!app.requireAdmin()) return; },

  onShow() {
    if (app.isAdmin()) this.loadData();
  },

  async loadData() {
    this.setData({ loading: true });
    try {
      const data = await api.overview() || {};
      let catMax = 1;
      (data.category_stats || []).forEach(c => { if ((c.notice_count || 0) > catMax) catMax = c.notice_count; });
      this.setData({
        stats: {
          user_count: data.user_count || 0,
          student_count: data.student_count || 0,
          admin_count: data.admin_count || 0,
          notice_count: data.notice_count || 0,
          draft_count: data.draft_count || 0,
          category_count: data.category_count || 0,
          favorite_count: data.favorite_count || 0,
          comment_count: data.comment_count || 0,
          like_count: data.like_count || 0,
          views_sum: data.views_sum || 0,
        },
        category_stats: (data.category_stats || []).map(c => ({
          id: c.id,
          name: c.name,
          notice_count: c.notice_count || 0,
          percent: Math.round(((c.notice_count || 0) / catMax) * 100),
        })),
        recent_notices: data.recent_notices || [],
        hot_notices: data.hot_notices || [],
        catMax,
      });
    } catch (e) { console.error(e); }
    finally { this.setData({ loading: false }); }
  },

  goNotice(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  },
});
