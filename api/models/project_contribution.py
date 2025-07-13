from app import db
from datetime import datetime


class ProjectContribution(db.Model):
    """项目贡献与评价模型"""

    __tablename__ = "project_contributions"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(
        db.Integer, db.ForeignKey("projects.id"), nullable=False, comment="项目ID"
    )
    user_id = db.Column(
        db.String(100),
        db.ForeignKey("users.user_id"),
        nullable=False,
        comment="贡献者Auth0用户标识",
    )
    role = db.Column(db.String(100), nullable=True, comment="在项目中的角色")
    stars_earned = db.Column(db.Integer, nullable=True, comment="获得的星级评价 (1-5)")
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    # 建立与项目和用户的一对多关系
    project = db.relationship("Project", backref="contributions", lazy=True)
    contributor = db.relationship(
        "User", backref="contributions", foreign_keys=[user_id]
    )

    def to_dict(self):
        """转换为字典"""
        project_info = None
        if self.project:
            project_info = {
                "id": self.project.id,
                "name": self.project.name,
                "project_type": self.project.project_type,
                "status": self.project.status,
                "end_time": (
                    self.project.end_time.strftime("%Y-%m-%d %H:%M:%S")
                    if self.project.end_time
                    else None
                ),
                "created_at": (
                    self.project.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    if self.project.created_at
                    else None
                ),
            }

        contributor_info = None
        if self.contributor:
            contributor_info = {
                "user_id": self.contributor.user_id,
                "full_name": self.contributor.full_name,
                "picture": self.contributor.picture,
            }

        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "role": self.role,
            "stars_earned": self.stars_earned,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "project_info": project_info,
            "contributor_info": contributor_info,
        }
