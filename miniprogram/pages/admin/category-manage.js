// pages/admin/category-manage.js
const app = getApp();
const { api } = require('../../utils/request.js');

Page({
  data: {
    list: [],
    loading: false,
    showEdit: false,
    editMode: 'create', // create / edit
    editId: null,
    // 常用 emoji 快捷选择（毕设演示用，点一下就填入，不用键盘按 Win+.）
    commonEmojis: ['🏫', '🎓', '🎤', '📚', '🎉', '🎁', '💰', '💼', '📝', '🏆', '🔧', '📅', '📢', '⚠️', '💡', '❤️', '⭐', '🏀'],
    form: {
      name: '',
      icon: '',
      sort_order: 0,
      status: 1,
    },
  },

  onLoad() { if (!app.requireAdmin()) return; },

  noOp() { /* 空函数，用于 catchtap 明确拦截冒泡 */ },

  pickIcon(e) {
    const icon = e.currentTarget.dataset.icon;
    this.setData({ 'form.icon': icon });
  },

  onShow() {
    if (app.isAdmin()) this.loadList();
  },

  async loadList() {
    this.setData({ loading: true });
    try {
      const list = await api.categoryList({ include_disabled: true }) || [];
      this.setData({ list });
    } catch (e) { console.error(e); }
    finally { this.setData({ loading: false }); }
  },

  openCreate() {
    this.setData({
      showEdit: true,
      editMode: 'create',
      editId: null,
      form: { name: '', icon: '', sort_order: 0, status: 1 },
    });
  },

  openEdit(e) {
    const id = e.currentTarget.dataset.id;
    const cat = this.data.list.find(c => c.id === id);
    if (!cat) return;
    this.setData({
      showEdit: true,
      editMode: 'edit',
      editId: id,
      form: {
        name: cat.name || '',
        icon: cat.icon || '',
        sort_order: cat.sort_order || 0,
        status: cat.status || 0,
      },
    });
  },

  closeEdit() { this.setData({ showEdit: false }); },

  onField(e) {
    const field = e.currentTarget.dataset.field;
    let v = e.detail.value;
    if (field === 'sort_order') v = parseInt(v) || 0;
    this.setData({ [`form.${field}`]: v });
  },

  toggleStatus(e) {
    const id = e.currentTarget.dataset.id;
    const cat = this.data.list.find(c => c.id === id);
    if (!cat) return;
    const newStatus = cat.status === 1 ? 0 : 1;
    wx.showModal({
      title: '提示',
      content: newStatus === 1 ? '确定启用该分类？' : '确定禁用该分类？禁用后前台将不显示。',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.categoryUpdate(id, { status: newStatus });
            wx.showToast({ title: '操作成功', icon: 'success' });
            this.loadList();
          } catch (e) { console.error(e); }
        }
      },
    });
  },

  async submitForm() {
    const f = this.data.form;
    if (!f.name || !f.name.trim()) {
      wx.showToast({ title: '请输入分类名称', icon: 'none' });
      return;
    }
    const payload = {
      name: f.name.trim(),
      icon: f.icon || null,
      sort_order: parseInt(f.sort_order) || 0,
      status: f.status ? 1 : 0,
    };
    try {
      if (this.data.editMode === 'create') {
        await api.categoryCreate(payload);
        wx.showToast({ title: '创建成功', icon: 'success' });
      } else {
        await api.categoryUpdate(this.data.editId, payload);
        wx.showToast({ title: '修改成功', icon: 'success' });
      }
      this.setData({ showEdit: false });
      this.loadList();
    } catch (e) { console.error(e); }
  },

  deleteCat(e) {
    const id = e.currentTarget.dataset.id;
    const cat = this.data.list.find(c => c.id === id);
    if (!cat) return;
    wx.showModal({
      title: '删除分类',
      content: `确定删除「${cat.name}」吗？若该分类下有公告则无法删除。`,
      confirmColor: '#F56C6C',
      success: async (res) => {
        if (res.confirm) {
          try {
            await api.categoryDelete(id);
            wx.showToast({ title: '已删除', icon: 'success' });
            this.loadList();
          } catch (e) { console.error(e); }
        }
      },
    });
  },

  onFormStatus(e) {
    this.setData({ 'form.status': e.detail.value ? 1 : 0 });
  },
});
