from app import db
from datetime import datetime


class ProjectLike(db.Model):
    """项目点赞模型"""

    __tablename__ = "project_likes"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    user_id = db.Column(
        db.String(100),
        db.ForeignKey("users.user_id"),
        nullable=False,
        comment="点赞用户Auth0标识",
    )
    created_at = db.Column(db.DateTime, default=datetime.now)

    # 建立与项目和用户的一对多关系
    project = db.relationship("Project", backref="likes", lazy=True)
    user = db.relationship("User", backref="likes", foreign_keys=[user_id])

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }
