// pages/admin/notice-list.js
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
    onlyMine: true,
    statusFilter: 'all', // all / published / draft
  },

  onLoad() {
    if (!app.requireAdmin()) return;
  },

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

  toggleMine() {
    this.setData({ onlyMine: !this.data.onlyMine, page: 1, noMore: false });
    this.loadList(true);
  },

  filterStatus(e) {
    const s = e.currentTarget.dataset.status;
    if (s === this.data.statusFilter) return;
    this.setData({ statusFilter: s, page: 1, noMore: false });
    this.loadList(true);
  },

  async loadList(refresh) {
    if (this.data.loading) return;
    const page = refresh ? 1 : this.data.page;
    this.setData({ loading: true });
    try {
      let res;
      if (this.data.onlyMine) {
        res = await api.myPublished({ page, page_size: this.data.pageSize });
      } else {
        const params = { page, page_size: this.data.pageSize };
        if (this.data.statusFilter === 'published') params.status = 1;
        else if (this.data.statusFilter === 'draft') params.status = 0;
        res = await api.noticeList(params);
      }
      let items = (res.items || []).map(n => Object.assign({}, n, {
        timeText: friendlyTime(n.created_at),
        statusText: n.status === 1 ? '已发布' : '草稿',
      }));
      if (this.data.statusFilter !== 'all' && this.data.statusFilter !== 'published' && this.data.statusFilter !== 'draft') {
        // noop
      }
      if (this.data.statusFilter === 'published') {
        items = items.filter(n => n.status === 1);
      } else if (this.data.statusFilter === 'draft') {
        items = items.filter(n => n.status === 0);
      }
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

  goDetail(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/detail/detail?id=${id}` });
  },

  editNotice(e) {
    const id = e.currentTarget.dataset.id;
    wx.navigateTo({ url: `/pages/admin/notice-edit?id=${id}` });
  },

  deleteNotice(e) {
    const id = e.currentTarget.dataset.id;
    const title = e.currentTarget.dataset.title;
    wx.showModal({
      title: '删除公告',
      content: `确定删除《${title}》吗？此操作不可恢复。`,
      confirmColor: '#F56C6C',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.noticeDelete(id);
            wx.showToast({ title: '已删除', icon: 'success' });
            this.setData({ page: 1, noMore: false });
            this.loadList(true);
          } catch (e) { console.error(e); }
        }
      },
    });
  },

  goNew() {
    wx.navigateTo({ url: '/pages/admin/notice-edit' });
  },
});
