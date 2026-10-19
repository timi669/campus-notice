-- ============================================
-- 简易校园公告资讯小程序 - 数据库初始化脚本
-- ============================================

CREATE DATABASE IF NOT EXISTS campus_notice DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE campus_notice;

-- 用户表
DROP TABLE IF EXISTS `user`;
CREATE TABLE `user` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户ID',
  `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
  `password` VARCHAR(255) NOT NULL COMMENT '密码(哈希)',
  `nickname` VARCHAR(50) DEFAULT NULL COMMENT '昵称',
  `avatar` VARCHAR(255) DEFAULT NULL COMMENT '头像URL',
  `role` ENUM('student','admin') NOT NULL DEFAULT 'student' COMMENT '角色: student-学生, admin-管理员',
  `openid` VARCHAR(100) DEFAULT NULL COMMENT '微信openid',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_username` (`username`),
  INDEX `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 公告分类表
DROP TABLE IF EXISTS `category`;
CREATE TABLE `category` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '分类ID',
  `name` VARCHAR(50) NOT NULL COMMENT '分类名称',
  `icon` VARCHAR(255) DEFAULT NULL COMMENT '分类图标',
  `sort_order` INT NOT NULL DEFAULT 0 COMMENT '排序值，越小越靠前',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1-启用, 0-禁用',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_status` (`status`),
  INDEX `idx_sort` (`sort_order`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公告分类表';

-- 公告表
DROP TABLE IF EXISTS `notice`;
CREATE TABLE `notice` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '公告ID',
  `title` VARCHAR(200) NOT NULL COMMENT '公告标题',
  `content` TEXT NOT NULL COMMENT '公告内容',
  `summary` VARCHAR(500) DEFAULT NULL COMMENT '摘要',
  `category_id` INT NOT NULL COMMENT '分类ID',
  `author_id` INT NOT NULL COMMENT '发布者ID',
  `cover_image` VARCHAR(255) DEFAULT NULL COMMENT '封面图URL',
  `views_count` INT NOT NULL DEFAULT 0 COMMENT '浏览次数',
  `is_top` TINYINT NOT NULL DEFAULT 0 COMMENT '是否置顶: 1-是, 0-否',
  `status` TINYINT NOT NULL DEFAULT 1 COMMENT '状态: 1-发布, 0-草稿',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  INDEX `idx_category` (`category_id`),
  INDEX `idx_author` (`author_id`),
  INDEX `idx_status` (`status`),
  INDEX `idx_top` (`is_top`),
  INDEX `idx_created` (`created_at`),
  FULLTEXT KEY `ft_title_content` (`title`, `content`) WITH PARSER ngram,
  CONSTRAINT `fk_notice_category` FOREIGN KEY (`category_id`) REFERENCES `category`(`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_notice_author` FOREIGN KEY (`author_id`) REFERENCES `user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='公告表';

-- 收藏表
DROP TABLE IF EXISTS `favorite`;
CREATE TABLE `favorite` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '收藏ID',
  `user_id` INT NOT NULL COMMENT '用户ID',
  `notice_id` INT NOT NULL COMMENT '公告ID',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '收藏时间',
  UNIQUE KEY `uk_user_notice` (`user_id`, `notice_id`),
  INDEX `idx_user` (`user_id`),
  INDEX `idx_notice` (`notice_id`),
  CONSTRAINT `fk_favorite_user` FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_favorite_notice` FOREIGN KEY (`notice_id`) REFERENCES `notice`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='收藏表';

-- 站内通知表
DROP TABLE IF EXISTS `notification`;
CREATE TABLE `notification` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '通知ID',
  `user_id` INT NOT NULL COMMENT '接收用户ID',
  `title` VARCHAR(200) NOT NULL COMMENT '通知标题',
  `content` TEXT DEFAULT NULL COMMENT '通知内容',
  `notice_id` INT DEFAULT NULL COMMENT '关联公告ID',
  `type` VARCHAR(20) NOT NULL DEFAULT 'system' COMMENT '通知类型: system/notice',
  `is_read` TINYINT NOT NULL DEFAULT 0 COMMENT '是否已读: 1-是 0-否',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_notice_id` (`notice_id`),
  INDEX `idx_is_read` (`is_read`),
  INDEX `idx_user_read` (`user_id`, `is_read`),
  CONSTRAINT `fk_notification_user` FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_notification_notice` FOREIGN KEY (`notice_id`) REFERENCES `notice`(`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='站内通知表';

-- 操作日志表
DROP TABLE IF EXISTS `operation_log`;
CREATE TABLE `operation_log` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
  `user_id` INT NOT NULL COMMENT '操作用户ID',
  `username` VARCHAR(50) NOT NULL COMMENT '操作用户名',
  `action` VARCHAR(50) NOT NULL COMMENT '操作类型: create/update/delete/login等',
  `target_type` VARCHAR(50) DEFAULT NULL COMMENT '操作对象类型: notice/user/category等',
  `target_id` INT DEFAULT NULL COMMENT '操作对象ID',
  `detail` TEXT DEFAULT NULL COMMENT '操作详情',
  `ip` VARCHAR(50) DEFAULT NULL COMMENT '操作IP',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_action` (`action`),
  INDEX `idx_user_time` (`user_id`, `created_at`),
  INDEX `idx_action_time` (`action`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='操作日志表';

-- 搜索日志表（用于统计热门搜索词）
DROP TABLE IF EXISTS `search_log`;
CREATE TABLE `search_log` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '日志ID',
  `keyword` VARCHAR(200) NOT NULL COMMENT '搜索关键词',
  `user_id` INT DEFAULT NULL COMMENT '搜索用户ID（未登录为NULL）',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '搜索时间',
  INDEX `idx_keyword` (`keyword`),
  INDEX `idx_keyword_time` (`keyword`, `created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='搜索日志表';

-- ============================================
-- 初始化测试数据
-- ============================================

-- 默认管理员账号由后端启动时自动创建: admin / 123456
-- 此处不插入 admin，避免密码哈希与后端不一致导致登录失败

-- 初始分类
INSERT INTO `category` (`name`, `icon`, `sort_order`) VALUES
('学校通知', '📢', 1),
('学术讲座', '🎓', 2),
('社团活动', '🎪', 3),
('考试信息', '📝', 4),
('就业招聘', '💼', 5),
('校园生活', '🏫', 6),
('奖助学金', '💰', 7),
('教务公告', '📚', 8);

-- 示例公告 (author_id=1 对应管理员)
INSERT INTO `notice` (`title`, `content`, `summary`, `category_id`, `author_id`, `is_top`, `status`) VALUES
('关于2026年国庆节放假安排的通知', '各学院、各部门：根据国务院办公厅关于2026年部分节假日安排的通知精神，结合学校实际，现将我校2026年国庆节放假安排通知如下：10月1日至10月7日放假调休，共7天。请各单位做好值班安排和安全保障工作。祝全校师生节日快乐！', '10月1日至10月7日放假调休，共7天，请各单位做好值班安排。', 1, 1, 1, 1),

('【学术讲座】人工智能与大模型技术前沿', '主讲人：张明教授，清华大学计算机系。时间：2026年10月15日（周四）14:30-16:30。地点：图书馆报告厅。内容简介：本次讲座将围绕大语言模型的最新进展、多模态AI的发展趋势以及AI在教育领域的应用前景展开探讨。欢迎广大师生踊跃参加。', '张明教授主讲人工智能前沿讲座，10月15日图书馆报告厅。', 2, 1, 0, 1),

('大学生创新创业大赛报名通知', '为激发大学生创新创业热情，学校决定举办第十届大学生创新创业大赛。报名时间：即日起至10月31日。参赛对象：全体在校本科生、研究生。参赛类别：创新类、创业类、公益类。详情请登录教务处网站查看。', '第十届双创大赛启动，报名截止10月31日，分创新/创业/公益三类。', 3, 1, 0, 1),

('2026-2027学年第一学期期中考试安排', '各学院：本学期期中考试定于10月27日至11月2日进行，请各学院及时通知任课教师和学生，做好考试安排与复习准备。具体考场安排见教务处后续通知。', '期中考试10月27日至11月2日进行，请注意考场安排。', 4, 1, 0, 1),

('秋季校园招聘会邀请函', '学校就业指导中心将于11月5日举办2027届毕业生秋季校园招聘会。邀请各知名企业进校招聘，届时将提供超过500个优质岗位。请毕业生携带简历积极参加。', '11月5日秋季招聘会，提供500+优质岗位，请毕业生积极参与。', 5, 1, 0, 1),

('关于学生宿舍安全用电的温馨提示', '各位同学：近期检查发现部分宿舍存在违规使用大功率电器的情况，存在消防安全隐患。请同学们自觉遵守宿舍管理规定，不使用大功率电器，离开宿舍时关闭电源。安全无小事，防患于未然。', '请勿使用大功率电器，离开宿舍请关闭电源，注意消防安全。', 6, 1, 0, 1),

('2026年度国家奖学金评审工作启动', '各学院：2026年度国家奖学金评审工作即日起开始，申请条件、评审程序和材料报送要求详见学生处网站通知。请符合条件的同学于10月20日前提交申请材料。', '国家奖学金评审启动，申请截止10月20日，详见学生处通知。', 7, 1, 0, 1),

('关于选课系统开放的通知', '2026-2027学年第二学期选修课选课系统将于10月10日上午9:00开放，请同学们登录教务系统进行选课。选课截止时间为10月15日24:00，请务必在规定时间内完成。', '选课系统10月10日9:00开放，截止10月15日24:00，请及时完成选课。', 8, 1, 0, 1);
