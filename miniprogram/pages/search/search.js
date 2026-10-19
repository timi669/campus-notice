// pages/search/search.js
const { api } = require('../../utils/request.js');
const { friendlyTime, debounce } = require('../../utils/util.js');
const config = require('../../utils/config.js');

Page({
  data: {
    keyword: '',
    history: [],
    hotKeywords: ['国庆', '考试', '招聘', '奖学金', '讲座', '社团'],
    noticeList: [],
    page: 1,
    pageSize: config.pageSize,
    total: 0,
    totalPages: 0,
    loading: false,
    noMore: false,
    searched: false,
    categoryId: null,
    sort: 'latest',
    categories: [],
  },

  onLoad() {
    const history = wx.getStorageSync('searchHistory') || [];
    const categories = wx.getStorageSync('categories') || [];
    this.setData({
      history: history.slice(0, 10),
      categories: [{ id: null, name: '全部' }].concat(categories),
    });
    this.loadCategories();
    this.loadHotKeywords();
  },

  async loadHotKeywords() {
    try {
      const list = await api.hotKeywords(10);
      if (Array.isArray(list) && list.length > 0) {
        this.setData({ hotKeywords: list });
      }
      // 接口返回空时保留默认热门词
    } catch (e) {
      console.error('加载热门搜索词失败:', e);
    }
  },

  onShow() {
    if (typeof this.getTabBar === 'function' && this.getTabBar()) {
      this.getTabBar().setData({ selected: 2 });
    }
  },

  async loadCategories() {
    try {
      const list = await api.categoryList();
      this.setData({ categories: [{ id: null, name: '全部' }].concat(list || []) });
    } catch (e) {
      console.error(e);
    }
  },

  onKeywordInput(e) {
    this.setData({ keyword: e.detail.value });
  },

  onSearchConfirm(e) {
    const kw = (e.detail && e.detail.value) || this.data.keyword;
    this.doSearch(kw);
  },

  tapKeyword(e) {
    const kw = e.currentTarget.dataset.kw;
    this.setData({ keyword: kw });
    this.doSearch(kw);
  },

  clearKeyword() {
    this.setData({ keyword: '', noticeList: [], searched: false, total: 0, page: 1, noMore: false });
  },

  clearHistory() {
    wx.removeStorageSync('searchHistory');
    this.setData({ history: [] });
  },

  selectCategory(e) {
    const id = e.currentTarget.dataset.id;
    this.setData({ categoryId: id || null, page: 1, noMore: false });
    if (this.data.searched) this.loadNoticeList(true);
  },

  switchSort(e) {
    const sort = e.currentTarget.dataset.sort;
    if (sort === this.data.sort) return;
    this.setData({ sort, page: 1, noMore: false });
    if (this.data.searched) this.loadNoticeList(true);
  },

  doSearch(kw) {
    kw = (kw || '').trim();
    if (!kw) {
      wx.showToast({ title: '请输入关键词', icon: 'none' });
      return;
    }
    const history = this.data.history.filter(h => h !== kw);
    history.unshift(kw);
    const top10 = history.slice(0, 10);
    wx.setStorageSync('searchHistory', top10);
    this.setData({ keyword: kw, history: top10, page: 1, noMore: false, searched: true });
    this.loadNoticeList(true);
  },

  onReachBottom() {
    if (!this.data.noMore && !this.data.loading && this.data.searched) this.loadNoticeList(false);
  },

  async loadNoticeList(refresh) {
    if (this.data.loading) return;
    const page = refresh ? 1 : this.data.page;
    this.setData({ loading: true });
    try {
      const params = {
        page,
        page_size: this.data.pageSize,
        keyword: this.data.keyword,
        sort: this.data.sort,
      };
      if (this.data.categoryId) params.category_id = this.data.categoryId;
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
