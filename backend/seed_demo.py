# -*- coding: utf-8 -*-
"""
注入答辩演示数据（可重复执行，幂等）：
- 5 个学生账号（密码统一 stu123456，含字母+数字）
- 若干真实评论
- 若干点赞
- 给定公告的浏览量
注意：只做"存在性判断后补充"，不覆盖已有数据，可安全重跑。
"""
import sys
sys.path.insert(0, ".")

from database import SessionLocal
import models.user  # noqa
import models.category  # noqa
import models.notice  # noqa
import models.favorite  # noqa
import models.notification  # noqa
import models.operation_log  # noqa
import models.search_log  # noqa
import models.comment  # noqa
import models.notice_like  # noqa
from models.user import User
from models.notice import Notice
from models.comment import Comment
from models.notice_like import NoticeLike
from utils.auth import hash_password

db = SessionLocal()

# 1) 学生账号
students = [
    ("zhangsan", "张三"),
    ("lisi", "李四"),
    ("wangwu", "王五"),
    ("zhaoliu", "赵六"),
    ("sunqi", "孙七"),
]
student_ids = {}
for uname, nick in students:
    u = db.query(User).filter(User.username == uname).first()
    if not u:
        u = User(username=uname, password=hash_password("stu123456"), nickname=nick, role="student")
        db.add(u)
        db.commit()
        db.refresh(u)
    student_ids[uname] = u.id
print("学生账号就绪:", {k: v for k, v in student_ids.items()})

# 2) 浏览量（相对真实）
views_map = {1: 1286, 2: 892, 3: 745, 4: 1023, 5: 560, 6: 430, 7: 385, 8: 501}
for nid, v in views_map.items():
    notice = db.query(Notice).filter(Notice.id == nid).first()
    if notice and notice.views_count < v:
        notice.views_count = v
db.commit()
print("浏览量已填充")

# 3) 评论（按 notice_id -> [(username, content), ...]）
comments_map = {
    1: [
        ("lisi", "收到，已转发给室友！"),
        ("wangwu", "太好了，国庆终于能回家了"),
        ("zhangsan", "值班安排在哪里看？"),
    ],
    2: [
        ("zhaoliu", "张明教授的讲座必须去听！"),
        ("sunqi", "有没有直播？怕抢不到现场票"),
        ("lisi", "多模态这块讲得好，期待"),
    ],
    3: [
        ("wangwu", "去年没得奖，今年再冲一次"),
        ("zhangsan", "组队求队友，本人会写代码"),
    ],
    4: [
        ("sunqi", "期中又来了……大家冲鸭"),
        ("lisi", "考场安排快点出啊"),
    ],
    5: [
        ("zhaoliu", "500 个岗位，应届生福音"),
        ("wangwu", "简历还没准备好，得抓紧了"),
    ],
    7: [
        ("zhangsan", "国奖竞争激烈，祝大家好运"),
        ("sunqi", "材料截止 20 号，别错过了"),
    ],
}
total_comments = 0
for nid, items in comments_map.items():
    for uname, content in items:
        uid = student_ids[uname]
        exists = db.query(Comment).filter(Comment.notice_id == nid, Comment.user_id == uid, Comment.content == content).first()
        if not exists:
            db.add(Comment(notice_id=nid, user_id=uid, content=content))
            total_comments += 1
db.commit()
print(f"评论注入 {total_comments} 条")

# 4) 点赞（每个学生给部分公告点赞）
like_map = {
    "zhangsan": [1, 2, 3, 4, 7],
    "lisi":     [1, 2, 3, 5, 6],
    "wangwu":   [1, 2, 3, 5, 8],
    "zhaoliu":  [1, 2, 4, 5],
    "sunqi":    [1, 2, 4, 7],
}
total_likes = 0
for uname, nids in like_map.items():
    uid = student_ids[uname]
    for nid in nids:
        exists = db.query(NoticeLike).filter(NoticeLike.notice_id == nid, NoticeLike.user_id == uid).first()
        if not exists:
            db.add(NoticeLike(notice_id=nid, user_id=uid))
            total_likes += 1
db.commit()
print(f"点赞注入 {total_likes} 条")

# 汇总
u_cnt = db.query(User).count()
c_cnt = db.query(Comment).count()
l_cnt = db.query(NoticeLike).count()
print(f"--- 完成后：user={u_cnt} comment={c_cnt} like={l_cnt} ---")
db.close()