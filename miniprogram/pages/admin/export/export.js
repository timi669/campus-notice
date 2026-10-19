// pages/admin/export/export.js
const app = getApp();
const { exportCsv } = require('../../../utils/request.js');

Page({
  data: {
    exporting: false,
    lastResult: null, // { title, lines, chars }
    tips: [
      '点击下方按钮导出对应 CSV 数据',
      '导出内容会自动复制到剪贴板',
      '在 Excel / WPS 中粘贴即可整理成表格',
    ],
  },

  onLoad() { if (!app.requireAdmin()) return; },

  exportUsers() {
    this.doExport('用户列表', '/api/users/export.csv');
  },

  exportNotices() {
    this.doExport('公告列表', '/api/notices/export.csv');
  },

  async doExport(title, path) {
    if (this.data.exporting) return;
    this.setData({ exporting: true });
    wx.showLoading({ title: '导出中...', mask: true });
    try {
      const csv = await exportCsv(path);
      const lines = csv ? csv.split('\n').filter(l => l.trim()).length : 0;
      this.setData({
        lastResult: { title, lines, chars: csv ? csv.length : 0 },
      });
      wx.setClipboardData({
        data: csv || '',
        success: () => wx.showToast({ title: '已复制到剪贴板', icon: 'success' }),
      });
    } catch (e) {
      console.error(e);
    } finally {
      wx.hideLoading();
      this.setData({ exporting: false });
    }
  },
});