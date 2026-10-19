// pages/admin/notice-edit.js
const app = getApp();
const { api, uploadFile } = require('../../utils/request.js');
const { resolveUrl } = require('../../utils/util.js');

Page({
  data: {
    id: null,
    isEdit: false,
    loading: false,
    saving: false,
    uploading: false,
    categories: [],
    catIndex: 0,
    cover_image_full: '',
    form: {
      title: '',
      content: '',
      summary: '',
      category_id: null,
      cover_image: '',
      is_top: 0,
      status: 1,
    },
  },

  onLoad(options) {
    if (!app.requireAdmin()) return;
    const id = options.id ? parseInt(options.id) : null;
    this.setData({ id, isEdit: !!id });
    this.loadCategories();
    if (id) {
      wx.setNavigationBarTitle({ title: '编辑公告' });
      this.loadDetail(id);
    } else {
      wx.setNavigationBarTitle({ title: '发布公告' });
    }
  },

  async loadCategories() {
    try {
      const list = await api.categoryList({ include_disabled: true }) || [];
      this.setData({
        categories: list,
        'form.category_id': this.data.form.category_id || (list[0] ? list[0].id : null),
        catIndex: 0,
      });
    } catch (e) { console.error(e); }
  },

  async loadDetail(id) {
    this.setData({ loading: true });
    try {
      const data = await api.noticeDetail(id);
      if (data) {
        const idx = Math.max(0, this.data.categories.findIndex(c => c.id === data.category_id));
        this.setData({
          form: {
            title: data.title || '',
            content: data.content || '',
            summary: data.summary || '',
            category_id: data.category_id,
            cover_image: data.cover_image || '',
            is_top: data.is_top || 0,
            status: data.status !== undefined ? data.status : 1,
          },
          cover_image_full: resolveUrl(data.cover_image),
          catIndex: idx,
        });
      }
    } catch (e) { console.error(e); }
    finally { this.setData({ loading: false }); }
  },

  onField(e) {
    const field = e.currentTarget.dataset.field;
    this.setData({ [`form.${field}`]: e.detail.value });
  },

  onCatChange(e) {
    const idx = parseInt(e.detail.value);
    this.setData({
      catIndex: idx,
      'form.category_id': this.data.categories[idx] ? this.data.categories[idx].id : null,
    });
  },

  toggleTop(e) {
    this.setData({ 'form.is_top': e.detail.value ? 1 : 0 });
  },

  toggleStatus(e) {
    this.setData({ 'form.status': e.detail.value ? 1 : 0 });
  },

  chooseCoverImage() {
    if (this.data.uploading) return;
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: async (res) => {
        const tempPath = res.tempFilePaths[0];
        this.setData({ uploading: true });
        wx.showLoading({ title: '上传中...', mask: true });
        try {
          const url = await uploadFile(tempPath);
          this.setData({
            'form.cover_image': url,
            cover_image_full: resolveUrl(url),
          });
          wx.showToast({ title: '上传成功', icon: 'success' });
        } catch (e) {
          console.error(e);
        } finally {
          wx.hideLoading();
          this.setData({ uploading: false });
        }
      },
    });
  },

  removeCoverImage() {
    this.setData({ 'form.cover_image': '', cover_image_full: '' });
  },

  previewCoverImage() {
    const url = this.data.cover_image_full;
    if (!url) return;
    wx.previewImage({ urls: [url], current: url });
  },

  validate() {
    const f = this.data.form;
    if (!f.title || !f.title.trim()) {
      wx.showToast({ title: '请输入标题', icon: 'none' });
      return false;
    }
    if (f.title.length > 200) {
      wx.showToast({ title: '标题不能超过200字', icon: 'none' });
      return false;
    }
    if (!f.content || !f.content.trim()) {
      wx.showToast({ title: '请输入内容', icon: 'none' });
      return false;
    }
    if (!f.category_id) {
      wx.showToast({ title: '请选择分类', icon: 'none' });
      return false;
    }
    return true;
  },

  async save() {
    if (!this.validate() || this.data.saving) return;
    this.setData({ saving: true });
    try {
      const payload = Object.assign({}, this.data.form, {
        title: this.data.form.title.trim(),
        content: this.data.form.content.trim(),
        summary: this.data.form.summary ? this.data.form.summary.trim() : null,
      });
      if (this.data.isEdit) {
        await api.noticeUpdate(this.data.id, payload);
        wx.showToast({ title: '修改成功', icon: 'success' });
      } else {
        await api.noticeCreate(payload);
        wx.showToast({ title: '发布成功', icon: 'success' });
      }
      setTimeout(() => {
        const pages = getCurrentPages();
        if (pages.length > 1) {
          wx.navigateBack();
        } else {
          wx.redirectTo({ url: '/pages/admin/notice-list' });
        }
      }, 800);
    } catch (e) { console.error(e); }
    finally { this.setData({ saving: false }); }
  },

  saveDraft() {
    if (!this.data.form.title || !this.data.form.title.trim()) {
      wx.showToast({ title: '标题不能空', icon: 'none' });
      return;
    }
    this.setData({ 'form.status': 0 });
    this.save();
  },

  preview() {
    if (!this.validate()) return;
    wx.showModal({
      title: '预览提示',
      content: '正式发布后即可在前台查看。是否确认发布？',
      success: (res) => { if (res.confirm) this.save(); },
    });
  },
});
