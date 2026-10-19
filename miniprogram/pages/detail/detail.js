// pages/detail/detail.js
const app = getApp();
const { api } = require('../../utils/request.js');
const { formatTime, resolveUrl } = require('../../utils/util.js');

Page({
  data: {
    id: null,
    detail: null,
    loading: true,
    contentHtml: '',
    comments: [],
    commentsTotal: 0,
    commentLoading: false,
    commentText: '',
    submitting: false,
    currentUserId: null,
    currentUserRole: '',
  },

  onLoad(options) {
    const id = parseInt(options.id);
    this.setData({ id });
    this.loadDetail();
    this.loadComments();
  },

  async loadDetail() {
    this.setData({ loading: true });
    try {
      const data = await api.noticeDetail(this.data.id);
      if (data) {
        const content = data.content || '';
        let html = content
          .replace(/\n/g, '<br/>')
          .replace(/\t/g, '&nbsp;&nbsp;&nbsp;&nbsp;');
        this.setData({
          detail: Object.assign({}, data, {
            timeText: formatTime(data.created_at),
            updateText: data.updated_at && data.updated_at !== data.created_at ? formatTime(data.updated_at) : '',
            cover_image_full: resolveUrl(data.cover_image),
          }),
          contentHtml: `<div style="line-height:1.8;font-size:30rpx;color:#333;padding:10rpx 0;">${html}</div>`,
        });
      }
    } catch (e) {
      console.error(e);
      wx.showToast({ title: '加载失败', icon: 'none' });
    } finally {
      this.setData({ loading: false });
    }
  },

  async toggleFavorite() {
    if (!app.requireLogin()) return;
    try {
      const res = await api.toggleFavorite(this.data.id);
      const detail = this.data.detail;
      detail.is_favorited = res.favorited;
      this.setData({ detail });
      wx.showToast({ title: res.favorited ? '已收藏' : '已取消', icon: 'success' });
    } catch (e) {
      console.error(e);
    }
  },

  async toggleLike() {
    if (!app.requireLogin()) return;
    try {
      const res = await api.toggleLike(this.data.id);
      const detail = this.data.detail;
      detail.is_liked = res.liked;
      detail.like_count = res.like_count;
      this.setData({ detail });
      wx.showToast({ title: res.liked ? '已点赞' : '已取消', icon: 'success' });
    } catch (e) {
      console.error(e);
    }
  },

  async loadComments() {
    this.setData({ commentLoading: true });
    try {
      const data = await api.commentList(this.data.id);
      const userInfo = app.globalData.userInfo || {};
      const items = (data.items || []).map((c) => ({
        ...c,
        timeText: formatTime(c.created_at),
      }));
      this.setData({
        comments: items,
        commentsTotal: data.total || 0,
        currentUserId: userInfo.id,
        currentUserRole: userInfo.role || '',
      });
    } catch (e) {
      console.error(e);
    } finally {
      this.setData({ commentLoading: false });
    }
  },

  onCommentInput(e) {
    this.setData({ commentText: e.detail.value });
  },

  async submitComment() {
    if (!app.requireLogin()) return;
    const content = (this.data.commentText || '').trim();
    if (!content) {
      wx.showToast({ title: '请输入评论内容', icon: 'none' });
      return;
    }
    if (this.data.submitting) return;
    this.setData({ submitting: true });
    try {
      await api.commentCreate(this.data.id, content);
      wx.showToast({ title: '评论成功', icon: 'success' });
      this.setData({ commentText: '' });
      this.loadComments();
    } catch (e) {
      console.error(e);
    } finally {
      this.setData({ submitting: false });
    }
  },

  async deleteComment(e) {
    const id = e.currentTarget.dataset.id;
    if (!id) return;
    wx.showModal({
      title: '提示',
      content: '确定删除这条评论吗？',
      success: async (res) => {
        if (!res.confirm) return;
        try {
          await api.commentDelete(id);
          wx.showToast({ title: '已删除', icon: 'success' });
          this.loadComments();
        } catch (err) {
          console.error(err);
        }
      },
    });
  },

  share() {
    wx.setClipboardData({
      data: this.data.detail ? this.data.detail.title : '',
      success: () => wx.showToast({ title: '标题已复制', icon: 'success' }),
    });
  },

  previewCover() {
    const url = this.data.detail && this.data.detail.cover_image_full;
    if (url) {
      wx.previewImage({ urls: [url] });
    }
  },

  onShareAppMessage() {
    const d = this.data.detail || {};
    return {
      title: d.title || '校园公告资讯',
      path: `/pages/detail/detail?id=${this.data.id}`,
    };
  },

  onShareTimeline() {
    const d = this.data.detail || {};
    return { title: d.title || '校园公告资讯' };
  },
});
