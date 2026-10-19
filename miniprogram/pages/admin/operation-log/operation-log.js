// pages/admin/operation-log/operation-log.js
const app = getApp();
const { api } = require('../../../utils/request.js');
const config = require('../../../utils/config.js');

const ACTION_LABELS = {
  login: '登录',
  create: '新增',
  update: '修改',
  delete: '删除',
  update_role: '改角色',
  export: '导出',
};

Page({
  data: {
    list: [],
    page: 1,
    pageSize: config.pageSize,
    total: 0,
    totalPages: 0,
    loading: false,
    noMore: false,
    actionFilter: 'all',
    actionTabs: [
      { key: 'all', label: '全部' },
      { key: 'login', label: '登录' },
      { key: 'create', label: '新增' },
      { key: 'update', label: '修改' },
      { key: 'delete', label: '删除' },
      { key: 'export', label: '导出' },
    ],
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

  filterAction(e) {
    const key = e.currentTarget.dataset.key;
    this.setData({ actionFilter: key, page: 1, noMore: false });
    this.loadList(true);
  },

  async loadList(refresh) {
    if (this.data.loading) return;
    const page = refresh ? 1 : this.data.page;
    this.setData({ loading: true });
    try {
      const params = { page, page_size: this.data.pageSize };
      if (this.data.actionFilter !== 'all') params.action = this.data.actionFilter;
      const res = await api.operationLogList(params) || {};
      let items = res.items || [];
      items = items.map(it => Object.assign({}, it, {
        actionText: ACTION_LABELS[it.action] || it.action,
        actionClass: 'act-' + (it.action || 'other'),
        timeText: (it.created_at || '').replace('T', ' ').slice(0, 19),
      }));
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
});