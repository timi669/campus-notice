// pages/admin/banner-manage/banner-manage.js
const app = getApp();
const { api, uploadFile } = require('../../../utils/request.js');
const { resolveUrl } = require('../../../utils/util.js');

Page({
  data: {
    list: [],
    loading: false,
    showEdit: false,
    editMode: 'create', // create / edit
    editId: null,
    uploading: false,
    linkTypes: [
      { key: 'notice', label: '跳转公告' },
      { key: 'none', label: '无跳转' },
      { key: 'url', label: '外链' },
    ],
    form: {
      image: '',
      title: '',
      link_type: 'notice',
      link_value: '',
      sort_order: 0,
      status: 1,
    },
    formImageFull: '',
  },

  onLoad() { if (!app.requireAdmin()) return; },

  onShow() {
    if (app.isAdmin()) this.loadList();
  },

  noOp() {},

  async loadList() {
    this.setData({ loading: true });
    try {
      const list = await api.bannerList(true) || [];
      const items = list.map(b => Object.assign({}, b, { image_full: resolveUrl(b.image) }));
      this.setData({ list: items });
    } catch (e) { console.error(e); }
    finally { this.setData({ loading: false }); }
  },

  chooseImage() {
    wx.chooseImage({
      count: 1,
      sizeType: ['compressed'],
      sourceType: ['album', 'camera'],
      success: async (res) => {
        const filePath = res.tempFilePaths[0];
        this.setData({ uploading: true });
        try {
          const url = await uploadFile(filePath);
          this.setData({
            'form.image': url,
            formImageFull: resolveUrl(url),
          });
          wx.showToast({ title: '上传成功', icon: 'success' });
        } catch (e) {
          console.error(e);
        } finally {
          this.setData({ uploading: false });
        }
      },
    });
  },

  openCreate() {
    this.setData({
      showEdit: true,
      editMode: 'create',
      editId: null,
      form: { image: '', title: '', link_type: 'notice', link_value: '', sort_order: 0, status: 1 },
      formImageFull: '',
    });
  },

  openEdit(e) {
    const id = e.currentTarget.dataset.id;
    const b = this.data.list.find(x => x.id === id);
    if (!b) return;
    this.setData({
      showEdit: true,
      editMode: 'edit',
      editId: id,
      form: {
        image: b.image || '',
        title: b.title || '',
        link_type: b.link_type || 'none',
        link_value: b.link_value || '',
        sort_order: b.sort_order || 0,
        status: b.status || 0,
      },
      formImageFull: resolveUrl(b.image),
    });
  },

  closeEdit() { this.setData({ showEdit: false }); },

  onField(e) {
    const field = e.currentTarget.dataset.field;
    let v = e.detail.value;
    if (field === 'sort_order') v = parseInt(v) || 0;
    this.setData({ [`form.${field}`]: v });
  },

  pickLinkType(e) {
    this.setData({ 'form.link_type': e.currentTarget.dataset.key });
  },

  onFormStatus(e) {
    this.setData({ 'form.status': e.detail.value ? 1 : 0 });
  },

  async submitForm() {
    const f = this.data.form;
    if (!f.image) {
      wx.showToast({ title: '请先上传轮播图片', icon: 'none' });
      return;
    }
    const payload = {
      image: f.image,
      title: f.title.trim() || null,
      link_type: f.link_type,
      link_value: f.link_value ? String(f.link_value).trim() : null,
      sort_order: parseInt(f.sort_order) || 0,
      status: f.status ? 1 : 0,
    };
    try {
      if (this.data.editMode === 'create') {
        await api.bannerCreate(payload);
        wx.showToast({ title: '创建成功', icon: 'success' });
      } else {
        await api.bannerUpdate(this.data.editId, payload);
        wx.showToast({ title: '修改成功', icon: 'success' });
      }
      this.setData({ showEdit: false });
      this.loadList();
    } catch (e) { console.error(e); }
  },

  toggleStatus(e) {
    const id = e.currentTarget.dataset.id;
    const b = this.data.list.find(x => x.id === id);
    if (!b) return;
    const newStatus = b.status === 1 ? 0 : 1;
    wx.showModal({
      title: '提示',
      content: newStatus === 1 ? '确定启用该轮播图？' : '确定禁用该轮播图？',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.bannerUpdate(id, { status: newStatus });
            wx.showToast({ title: '操作成功', icon: 'success' });
            this.loadList();
          } catch (e) { console.error(e); }
        }
      },
    });
  },

  deleteBanner(e) {
    const id = e.currentTarget.dataset.id;
    const b = this.data.list.find(x => x.id === id);
    if (!b) return;
    wx.showModal({
      title: '删除轮播图',
      content: `确定删除「${b.title || '未命名'}」吗？`,
      confirmColor: '#F56C6C',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.bannerDelete(id);
            wx.showToast({ title: '已删除', icon: 'success' });
            this.loadList();
          } catch (e) { console.error(e); }
        }
      },
    });
  },
});