# 简易校园公告资讯小程序（Python后端）

毕业设计项目：基于微信小程序 + Python FastAPI 后端的校园公告资讯管理系统。

---

## 一、项目结构

```
campus-notice/
├── backend/                      # Python FastAPI 后端
│   ├── main.py                   # 项目入口（自动建表 + 默认管理员）
│   ├── config.py                 # 配置类（从 .env 读取）
│   ├── database.py               # SQLAlchemy 数据库连接
│   ├── requirements.txt          # 依赖清单
│   ├── .env.example              # 环境变量示例
│   ├── models/                   # 数据模型
│   │   ├── user.py               # 用户表
│   │   ├── category.py           # 公告分类表
│   │   ├── notice.py             # 公告表
│   │   ├── favorite.py           # 收藏表
│   │   ├── comment.py            # 评论表
│   │   ├── notice_like.py        # 点赞表
│   │   ├── notification.py       # 站内通知表
│   │   ├── operation_log.py      # 操作日志表（审计）
│   │   └── search_log.py         # 搜索日志表（热门词统计）
│   ├── schemas/                  # Pydantic 请求/响应校验模型
│   │   ├── user.py
│   │   ├── category.py
│   │   ├── notice.py
│   │   ├── favorite.py
│   │   ├── comment.py
│   │   ├── like.py
│   │   ├── notification.py
│   │   ├── operation_log.py
│   │   └── common.py             # 通用响应结构
│   ├── routers/                  # API 路由
│   │   ├── auth.py               # 注册/登录/获取当前用户
│   │   ├── user.py               # 用户管理（管理员）+ 注销
│   │   ├── category.py           # 分类 CRUD
│   │   ├── notice.py             # 公告 CRUD+搜索+收藏+点赞+置顶+热门词
│   │   ├── comment.py            # 评论列表/发布/删除
│   │   ├── stats.py              # 数据统计概览
│   │   ├── upload.py             # 图片上传接口
│   │   ├── notification.py       # 站内通知接口
│   │   └── operation_log.py      # 操作日志查询接口
│   ├── tests/                    # pytest 单元测试（55 个用例）
│   │   ├── conftest.py           # 独立测试库 campus_notice_test + 夹具
│   │   ├── test_auth.py / test_user.py / test_category.py
│   │   ├── test_notice.py / test_comment.py / test_like.py
│   │   ├── test_notification.py / test_operation_log.py
│   │   └── pytest.ini            # 位于 backend/ 根目录
│   ├── utils/
│   │   ├── auth.py               # JWT 令牌、密码哈希、权限依赖、登录限流
│   │   ├── cache.py              # Redis 缓存工具（带内存降级）
│   │   └── operation_log.py      # 操作日志记录工具
│   ├── Dockerfile                # 后端 Docker 镜像构建
│   └── .dockerignore
│
├── nginx/
│   └── nginx.conf                # Nginx 反向代理配置
├── docker-compose.yml            # 一键编排：backend + mysql + redis + nginx
│
├── miniprogram/                  # 微信小程序前端
│   ├── app.js / app.json / app.wxss
│   ├── project.config.json
│   ├── sitemap.json
│   ├── utils/
│   │   ├── config.js             # 后端地址等配置
│   │   ├── auth.js               # 本地 token 存取、登录态判断
│   │   ├── request.js            # wx.request Promise 封装 + API 集中映射
│   │   └── util.js               # 时间格式化、防抖节流等工具
│   └── pages/
│       ├── index/                # 首页：轮播置顶+分类入口+公告列表
│       ├── category/             # 分类浏览（左栏切换+分页）
│       ├── detail/               # 公告详情（富文本+点赞+收藏+评论+转发）
│       ├── search/               # 搜索（历史/热门/分类过滤）
│       ├── login/                # 登录/注册（快捷体验按钮）
│       ├── profile/              # 个人中心+管理员入口
│       ├── favorites/            # 我的收藏
│       ├── notifications/    # 消息通知中心（未读红点、标记已读）
│       └── admin/                # 管理员后台
│           ├── index/            # 控制台：概览统计+快捷入口+热门
│           ├── notice-edit/      # 公告发布/编辑
│           ├── notice-list/      # 公告管理
│           ├── category-manage/  # 分类管理
│           ├── user-manage/      # 用户管理
│           └── stats/            # 数据统计
│
└── sql/
    └── init.sql                  # 数据库初始化脚本（可选用）
```

---

## 二、快速开始

### 2.1 环境要求

| 层级 | 要求 |
|------|------|
| 后端 | Python 3.10+、MySQL 5.7+ / 8.0+、Redis 5.0+（可选，未安装时自动降级为内存缓存） |
| 前端 | 微信开发者工具（最新稳定版） |

### 2.2 启动后端

1. **创建数据库**（推荐 MySQL 8.0）

   ```sql
   CREATE DATABASE campus_notice DEFAULT CHARACTER SET utf8mb4;
   ```
   > 说明：后端启动时会**自动创建所有数据表**，并创建默认管理员账号，
   > 无需手动执行 `init.sql`（`init.sql` 是额外的可选脚本，含预设分类与示例公告）。

2. **创建虚拟环境并安装依赖**

   ```bash
   cd backend
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate

   pip install -r requirements.txt
   ```

3. **配置环境变量**

   ```bash
   copy .env.example .env    # Windows
   # cp .env.example .env    # macOS/Linux
   ```
   然后编辑 `.env`，填入本机的 MySQL 账号密码与数据库名。
   > 如本机已安装 Redis，可填写 `REDIS_HOST` 等配置；未安装则保持默认，系统会自动降级为内存缓存，不影响运行。

4. **启动后端服务**

   ```bash
   python main.py
   ```
   服务默认监听 `0.0.0.0:8000`。

5. **访问在线接口文档（Swagger）**

   浏览器打开：
   - Swagger UI: http://localhost:8000/docs
   - ReDoc:      http://localhost:8000/redoc

6. **默认账号**（首次启动自动创建）

   | 用户名 | 密码 | 角色 |
   |--------|------|------|
   | admin | 123456 | 管理员 |

### 2.3 启动小程序

1. 打开**微信开发者工具** → 导入项目 → 选择 `campus-notice/miniprogram` 目录。
2. 如无 AppID，可勾选**"不使用云服务，使用测试号"**。
3. 修改 `miniprogram/utils/config.js` 中 `baseUrl` 为后端地址：
   ```js
   dev: {
     baseUrl: 'http://localhost:8000',  // 真机调试时改为电脑局域网IP
   }
   ```
4. 开发者工具中：详情 → 本地设置 → 勾选 **"不校验合法域名、TLS版本、HTTPS证书"**。
5. 点击"编译"即可预览。

> 如需真机调试：将 `baseUrl` 改为后端电脑的局域网 IP（如 `http://192.168.1.100:8000`），
> 并确保手机与后端电脑在同一 WiFi。

### 2.4 TabBar 图标（可选）

小程序底部 tabBar 需要 8 张 PNG 图标（4 个功能 × 正常/选中态），尺寸建议 81×81 px。
请将图标放置到以下路径（首次使用前可自行制作或下载免费图标）：

```
miniprogram/assets/icons/
├── home.png          category.png        search.png        user.png
└── home-active.png   category-active.png search-active.png user-active.png
```

> 没有图标也可以**正常运行**（仅控制台会警告，毕设演示时建议补齐以获得最佳视觉效果）。

### 2.5 Docker 一键部署（推荐用于答辩演示）

项目根目录提供了 `docker-compose.yml`，可一键启动完整环境（后端 + MySQL + Redis + Nginx）。

```bash
# 在项目根目录执行
docker-compose up -d --build
```

启动后：
- 后端 API：http://localhost:8000 （也可通过 Nginx 访问 http://localhost）
- Swagger 文档：http://localhost:8000/docs
- MySQL：localhost:3306（root / 123456）
- Redis：localhost:6379

> 首次启动 MySQL 会自动执行 `sql/init.sql` 创建库表和测试数据；后端启动后会自动创建默认管理员 `admin / 123456`。
>
> 如需修改默认密码或数据库配置，编辑 `docker-compose.yml` 中对应服务的 `environment` 即可。

---

## 三、核心功能清单

### 3.1 学生端（普通用户）

| 功能 | 说明 |
|------|------|
| 注册/登录 | 用户名+密码注册，JWT 鉴权，401 自动跳转登录 |
| 首页 | 置顶公告轮播 + 8 分类快捷入口 + 最新/最热切换 + 无限分页 |
| 分类浏览 | 左栏列表 + 右栏公告，按分类过滤，分页下拉加载 |
| 公告详情 | 富文本、浏览量自增、点赞/取消（实时计数）、收藏/取消、评论区（发表/删除）、复制分享、微信转发 |
| 搜索 | 关键词历史记录 + 热门词 + 分类过滤 + 最新/最热排序 |
| 我的收藏 | 收藏列表 + 取消收藏 + 跳详情 |
| 评论互动 | 公告详情页发表评论、删除自己的评论；管理员可删除任意评论 |
| 点赞 | 公告点赞/取消，详情页与列表展示点赞数 |
| 消息通知 | 管理员发布公告时自动推送站内通知，未读红点提示，支持标记已读 |
| 个人中心 | 头像/昵称展示、修改昵称、修改密码（需校验旧密码）、退出登录 |

### 3.2 管理员端

| 功能 | 说明 |
|------|------|
| 控制台首页 | 统计数据卡片（用户/公告/分类/浏览量）+ 快捷入口 + 最新+热门 Top5 |
| 发布公告 | 标题/摘要/正文/分类/**封面图上传** + 置顶/草稿 开关，字数实时计数 |
| 编辑公告 | 复用发布页，回填数据后保存修改 |
| 公告管理 | 全部/已发布/草稿、只看我筛选、编辑/删除操作、浮动 + 按钮 |
| 分类管理 | 新建/编辑/禁用/删除，支持 emoji 图标，排序值控制顺序 |
| 用户管理 | 关键词搜索、角色过滤、管理员升降级、删除用户（非本人） |
| 数据统计 | KPI 卡片 + 分类公告分布进度条 + 热门 Top5 + 最新动态 |

---

## 四、后端接口一览（可直接用于毕业论文）

> 所有接口 Base URL：`http://localhost:8000`；除注册登录外，其余均需 `Authorization: Bearer <token>`。

### 认证模块 `/api/auth`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/register` | 用户注册（默认 student 角色） | 否 |
| POST | `/login` | 用户名+密码登录，返回 token 与用户信息 | 否 |
| GET  | `/me` | 获取当前登录用户信息 | 是 |

### 用户模块 `/api/users`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET  | `/me` | 我的信息 | 任意用户 |
| PUT  | `/me` | 修改我的昵称/头像 | 任意用户 |
| PUT  | `/me/password` | 修改密码（需校验旧密码） | 任意用户 |
| GET  | `/` | 用户列表（支持 keyword、role 过滤、分页） | 管理员 |
| GET  | `/{id}` | 用户详情 | 管理员 |
| PUT  | `/{id}/role` | 修改角色(student/admin) | 管理员 |
| DELETE | `/{id}` | 删除用户（禁止删除自己） | 管理员 |

### 分类模块 `/api/categories`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET  | `/` | 分类列表（默认仅启用，含公告数） | 否 |
| GET  | `/{id}` | 分类详情 | 否 |
| POST | `/` | 新建分类 | 管理员 |
| PUT  | `/{id}` | 修改分类 | 管理员 |
| DELETE | `/{id}` | 删除分类（含公告时禁止） | 管理员 |

### 公告模块 `/api/notices`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET  | `/` | 分页列表（分类、关键词、最新/最热） | 可选 |
| GET  | `/top` | 置顶公告列表 | 否 |
| GET  | `/{id}` | 公告详情（浏览量+1、未登录也可看） | 可选 |
| POST | `/` | 发布公告 | 管理员 |
| PUT  | `/{id}` | 编辑公告 | 管理员 |
| DELETE | `/{id}` | 删除公告 | 管理员 |
| POST | `/{id}/favorite` | 收藏/取消 切换 | 任意已登录 |
| POST | `/{id}/like` | 点赞/取消 切换（返回最新 like_count） | 任意已登录 |
| GET  | `/my/favorites` | 我的收藏列表 | 任意已登录 |
| GET  | `/my/published` | 我发布的公告（管理员） | 管理员 |

### 评论模块 `/api/comments`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET  | `/` | 某公告评论列表（`?notice_id=`、分页） | 否 |
| POST | `/` | 发布评论（body: `notice_id` + `content`） | 任意已登录 |
| DELETE | `/{id}` | 删除评论（评论者本人或管理员） | 任意已登录 |

### 统计模块 `/api/stats`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET  | `/` | 概览统计：各计数 + 最新/热门 + 分类分布 | 管理员 |

### 文件上传模块 `/api/upload`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| POST | `/` | 上传图片（jpg/png/gif/webp/bmp，≤5MB），返回可访问 URL | 任意已登录 |

### 站内通知模块 `/api/notifications`
| 方法 | 路径 | 说明 | 鉴权 |
|------|------|------|------|
| GET  | `/` | 我的通知列表（支持 is_read 过滤、分页） | 任意已登录 |
| GET  | `/unread-count` | 未读通知数量 | 任意已登录 |
| PUT  | `/{id}/read` | 标记单条通知已读 | 任意已登录 |
| PUT  | `/read-all` | 标记全部通知已读 | 任意已登录 |

---

## 五、技术栈与关键设计

### 5.1 后端技术栈
- **Web 框架：** FastAPI 0.115（异步类型、自动生成 Swagger、Pydantic 校验）
- **ORM：** SQLAlchemy 2.0（Declarative Base + 关系映射、外键约束、索引）
- **数据库驱动：** PyMySQL
- **缓存：** Redis（redis-py），不可用时自动降级为内存缓存
- **鉴权：** python-jose（JWT）+ passlib（pbkdf2_sha256 密码哈希）
- **配置管理：** pydantic-settings + .env
- **CORS：** 内置中间件，开发默认放开跨域
- **部署：** Docker + docker-compose + Nginx 反向代理
- **测试：** pytest 9 + httpx（FastAPI TestClient），55 个用例全通过

### 5.2 前端技术栈
- 微信小程序原生框架（WXML / WXSS / JS）
- 封装 Promise 风格请求层、集中 API 映射
- 自定义全局样式（卡片、按钮、标签、骨架屏等）
- TabBar 四页 + 多个二级页面
- 骨架屏、加载状态、空态、Toast 提示

### 5.3 关键设计点
1. **密码安全：** 一律存 `pbkdf2_sha256` 哈希，不会保存明文；修改密码需校验旧密码
2. **角色权限：** 基于 FastAPI Dependencies 的分层：`get_current_user` → `require_admin`
3. **收藏/点赞联合唯一：** 数据库层 `UNIQUE(user_id, notice_id)` 保证不重复收藏/点赞
4. **消息推送：** 管理员发布公告时自动给所有用户创建站内通知，支持未读计数与标记已读
5. **Redis 缓存：** 置顶公告、分类列表、统计概览三个热点接口接入缓存，带 TTL 与失效机制；Redis 不可用时自动降级内存缓存
6. **全文检索：** 搜索优先使用 MySQL FULLTEXT（ngram 分词），索引不存在时自动降级为 LIKE
7. **浏览量原子更新：** 使用 SQL `UPDATE ... SET views_count = views_count + 1` 避免并发竞态
8. **密码强度：** 注册与改密时强制 6-50 位且包含字母和数字
9. **前后端约定：** 统一响应 `{ code, message, data }`，0 表示成功
10. **单元测试：** pytest + TestClient，使用独立测试库 `campus_notice_test`，覆盖认证/公告/评论/点赞/通知/日志/权限共 55 个用例

---

## 六、毕设答辩小贴士

1. **Swagger 截图：** `http://localhost:8000/docs` 可以直接作为论文中 API 接口章节截图。
2. **功能演示流程建议：**
   - 注册学生账号 → 浏览首页 → 分类 → 详情 → 点赞 → 评论 → 收藏 → 搜索
   - 登录 admin → 控制台 → 发公告（选分类+置顶+上传封面图）→ 返回前台确认
   - 切回学生账号 → 个人中心查看消息通知红点 → 进入通知中心 → 标记已读
   - 分类管理 → 新增分类；用户管理 → 把刚注册的学生升为管理员再降回
3. **论文数据模型部分：** 可直接参考 `backend/models/*.py` 画出 ER 图（9 张表：user/category/notice/favorite/comment/notice_like/notification/operation_log/search_log）。
4. **性能优化亮点：** 论文中可对比 LIKE 与 FULLTEXT 全文检索的性能差异；Redis 缓存对热点接口的加速效果。
5. **部署加分：** 有条件的同学可以把后端部署到云服务器（腾讯云/阿里云），小程序端改为 HTTPS 域名并在公众平台配置 request 合法域名；或直接用 `docker-compose` 在服务器一键部署。

---

## 七、常见问题 FAQ

**Q: 启动报 `ModuleNotFoundError: No module named 'xxx'`？**
A: 请确认已激活虚拟环境并执行了 `pip install -r requirements.txt`。

**Q: 数据库连接失败？**
A: 检查 `.env` 中的账号密码、确认 MySQL 已启动、数据库 `campus_notice` 已创建。

**Q: 小程序请求失败显示 `request:fail url not in domain list`？**
A: 开发者工具 → 详情 → 本地设置 → 勾选"不校验合法域名..."。

**Q: 想改默认管理员密码？**
A: 首次启动后登录 admin 账号，个人中心 → 修改密码；或删掉数据库中 admin 用户后重启后端自动重建。

**Q: 如何快速构造演示数据？**
A: 任选其一：
   - 手动执行 `sql/init.sql`（内含 8 分类和 8 篇示例公告；init.sql 不再插入 admin，admin 由后端启动时自动创建，密码 123456）
   - 或登录 admin 在小程序后台直接手动新建几条即可。

**Q: Redis 没装会报错吗？**
A: 不会。`utils/cache.py` 会在启动时检测 Redis，连接失败则自动降级为内存缓存（带 TTL），所有功能正常运行。只是缓存数据不跨进程持久化。

**Q: 搜索用 LIKE 还是全文检索？**
A: 启动时自动检测 `notice` 表是否有 FULLTEXT 索引。若执行过 `init.sql` 则有索引，使用 `MATCH AGAINST` 全文检索；否则降级为 `LIKE`。日志中会打印 `[Search]` 提示当前模式。

**Q: 怎么跑单元测试？**
A: 进入 `backend/` 目录，确保 MySQL 已启动，执行 `venv\Scripts\python.exe -m pytest`（macOS/Linux 用 `venv/bin/python -m pytest`）。测试会自动创建独立库 `campus_notice_test`，**不会影响**正式库 `campus_notice`。

祝毕业设计顺利，答辩一次过！🎓
