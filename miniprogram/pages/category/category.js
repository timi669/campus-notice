// pages/category/category.js
const app = getApp();
const { api } = require('../../utils/request.js');
const { friendlyTime } = require('../../utils/util.js');
const config = require('../../utils/config.js');

Page({
  data: {
    categories: [],
    currentId: null,
    currentName: '全部',
    noticeList: [],
    page: 1,
    pageSize: config.pageSize,
    total: 0,
    totalPages: 0,
    loading: false,
    noMore: false,
  },

  onLoad(options) {
    if (options.id) {
      this.setData({ currentId: parseInt(options.id) || null });
    }
    this.loadCategories();
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 1 });
    }
  },

  onPullDownRefresh() {
    this.setData({ page: 1, noMore: false });
    Promise.all([this.loadCategories(true), this.loadNoticeList(true)]).then(() => wx.stopPullDownRefresh());
  },

  onReachBottom() {
    if (!this.data.noMore && !this.data.loading) this.loadNoticeList(false);
  },

  async loadCategories(silent) {
    try {
      const list = await api.categoryList();
      const categories = [{ id: null, name: '全部', icon: '📋', notice_count: 0 }].concat(list || []);
      let currentName = '全部';
      if (this.data.currentId) {
        const hit = categories.find(c => c.id === this.data.currentId);
        if (hit) currentName = hit.name;
      }
      this.setData({ categories, currentName });
      this.loadNoticeList(true);
    } catch (e) {
      if (!silent) console.error(e);
    }
  },

  selectCategory(e) {
    const id = e.currentTarget.dataset.id;
    if (id === this.data.currentId) return;
    const cat = this.data.categories.find(c => c.id === id);
    this.setData({
      currentId: id || null,
      currentName: cat ? cat.name : '全部',
      page: 1,
      noMore: false,
    });
    this.loadNoticeList(true);
  },

  async loadNoticeList(refresh) {
    if (this.data.loading) return;
    const page = refresh ? 1 : this.data.page;
    this.setData({ loading: true });
    try {
      const params = { page, page_size: this.data.pageSize };
      if (this.data.currentId) params.category_id = this.data.currentId;
      const res = await api.noticeList(params);
      const items = (res.items || []).map(n => Object.assign({}, n, { timeText: friendlyTime(n.created_at) }));
      const newList = refresh ? items : this.data.noticeList.concat(items);
      const totalPages = res.total_pages || 0;
      this.setData({
        noticeList: newList,
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
});
