// pages/index/index.js
const app = getApp();
const { api } = require('../../utils/request.js');
const { friendlyTime, debounce, resolveUrl } = require('../../utils/util.js');
const config = require('../../utils/config.js');

Page({
  data: {
    banner: [],
    categories: [],
    topNotices: [],
    noticeList: [],
    page: 1,
    pageSize: config.pageSize,
    total: 0,
    totalPages: 0,
    loading: false,
    noMore: false,
    categoryId: null,
    keyword: '',
    tab: 'latest',
  },

  onLoad() {
    this.loadCategories();
    this.loadBanners();
    this.loadTopNotices();
    this.loadNoticeList(true);
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 0 });
    }
  },

  onPullDownRefresh() {
    this.setData({ page: 1, noMore: false });
    Promise.all([
      this.loadCategories(true),
      this.loadBanners(true),
      this.loadTopNotices(true),
      this.loadNoticeList(true),
    ]).then(() => wx.stopPullDownRefresh());
  },

  onReachBottom() {
    if (!this.data.noMore && !this.data.loading) {
      this.loadNoticeList(false);
    }
  },

  async loadCategories(silent) {
    try {
      const list = await api.categoryList();
      this.setData({ categories: list || [] });
      wx.setStorageSync('categories', list || []);
    } catch (e) {
      if (!silent) console.error('loadCategories', e);
    }
  },

  async loadBanners(silent) {
    try {
      const list = await api.bannerList(false);
      const banner = (list || []).map(b => ({
        id: b.id,
        title: b.title || '',
        image_full: resolveUrl(b.image),
        link_type: b.link_type,
        link_value: b.link_value,
      }));
      this.setData({ banner });
    } catch (e) {
      if (!silent) console.error('loadBanners', e);
    }
  },

  async loadTopNotices(silent) {
    try {
      const list = await api.topNotices(5);
      this.setData({ topNotices: list || [] });
    } catch (e) {
      if (!silent) console.error('loadTopNotices', e);
    }
  },

  async loadNoticeList(refresh) {
    if (this.data.loading) return;
    const page = refresh ? 1 : this.data.page;
    this.setData({ loading: true });
    try {
      const params = {
        page,
        page_size: this.data.pageSize,
        sort: this.data.tab,
      };
      if (this.data.categoryId) params.category_id = this.data.categoryId;
      if (this.data.keyword) params.keyword = this.data.keyword;

      const res = await api.noticeList(params);
      const items = (res.items || []).map(n => Object.assign({}, n, {
        timeText: friendlyTime(n.created_at),
        cover_image_full: resolveUrl(n.cover_image),
      }));
      let newList = items;
      let total = res.total || 0;
      if (!refresh) {
        newList = this.data.noticeList.concat(items);
      }
      const totalPages = res.total_pages || 0;
      this.setData({
        noticeList: newList,
        total,
        totalPages,
        page: page + 1,
        noMore: page >= totalPages,
      });
    } catch (e) {
      console.error('loadNoticeList', e);
    } finally {
      this.setData({ loading: false });
    }
  },

  switchTab(e) {
    const tab = e.currentTarget.dataset.tab;
    if (tab === this.data.tab) return;
    this.setData({ tab, page: 1, noMore: false });
    this.loadNoticeList(true);
  },

  onCategoryTap(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/category/category?id=${id}` });
  },

  goDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  },

  goBanner(e) {
    const b = this.data.banner[e.currentTarget.dataset.index];
    if (!b) return;
    if (b.link_type === 'notice' && b.link_value) {
      wx.navigateTo({ url: `/pages/detail/detail?id=${b.link_value}` });
    } else if (b.link_type === 'url' && b.link_value) {
      wx.setClipboardData({
        data: b.link_value,
        success: () => wx.showToast({ title: '链接已复制', icon: 'none' }),
      });
    }
  },

  goSearch() {
    wx.switchTab({ url: '/pages/search/search' });
  },

  goCategoryPage() {
    wx.switchTab({ url: '/pages/category/category' });
  },

  onKeywordInput: debounce(function (e) {
    const keyword = e.detail.value;
    this.setData({ keyword, page: 1, noMore: false });
    this.loadNoticeList(true);
  }, 500),
});
