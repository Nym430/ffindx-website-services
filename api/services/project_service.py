from app import db
from api.models.project import (
    Project,
    SkillRequirement,
    SkillType,
    ProjectApplication,
    ProjectDeliverable,
    DeliverableConfirmation,
)
from api.models.project_like import ProjectLike
from datetime import datetime
from sqlalchemy import or_, and_, func
from werkzeug.utils import secure_filename
import os
from flask import current_app

print("Loading project_service.py")


class SkillTypeService:
    @staticmethod
    def get_all_skill_types():
        """
        获取所有技能类型
        :return: 技能类型列表
        """
        skill_types = SkillType.query.all()
        return [skill_type.to_dict() for skill_type in skill_types]

    @staticmethod
    def get_skill_type_by_id(skill_type_id):
        """
        根据ID获取技能类型
        :param skill_type_id: 技能类型ID
        :return: 技能类型对象
        """
        return SkillType.query.get_or_404(skill_type_id)

    @staticmethod
    def create_skill_type(data):
        """
        创建新技能类型
        :param data: 包含技能类型信息的字典
        :return: 创建的技能类型对象
        """
        skill_type = SkillType(name=data["name"], description=data.get("description"))
        db.session.add(skill_type)
        db.session.commit()
        return skill_type


class ProjectService:
    @staticmethod
    def create_project(data, user_id):
        """
        创建新项目
        :param data: 包含项目信息的字典
        :param user_id: 创建者用户ID（必填）
        :return: 创建的项目对象
        """
        if not user_id:
            raise ValueError("创建项目必须提供用户ID")

        # 创建项目
        try:
            end_time = None
            if data.get("end_time"):
                try:
                    end_time = datetime.strptime(data["end_time"], "%Y-%m-%d %H:%M:%S")
                except ValueError:
                    raise ValueError(
                        "项目结束时间格式错误，请使用 'YYYY-MM-DD HH:MM:SS' 格式"
                    )

            project = Project(
                name=data["name"],
                project_type=data["project_type"],
                end_time=end_time,
                description=data.get("description"),
                goal=data.get("goal"),
                status=Project.STATUS_IN_PROGRESS,
                recruitment_status=Project.RECRUITMENT_OPEN,
                user_id=user_id,
            )

            # 添加技能需求
            skills_data = data.get("skill_requirements", [])
            for skill_data in skills_data:
                skill = SkillRequirement(
                    skill_type_id=skill_data["skill_type_id"],
                    required_count=skill_data["required_count"],
                    importance=skill_data["importance"],
                    description=skill_data.get("description"),
                )
                project.skill_requirements.append(skill)

            # 保存到数据库
            db.session.add(project)
            db.session.commit()

            return project
        except Exception as e:
            db.session.rollback()
            raise ValueError(f"创建项目时发生错误: {str(e)}")

    @staticmethod
    def get_project_list(filters=None):
        """
        获取项目列表，支持多种过滤条件
        :param filters: 过滤条件字典
        :return: 项目列表
        """
        query = Project.query

        if filters:
            # 项目名称筛选
            if "name" in filters and filters["name"]:
                query = query.filter(Project.name.like(f"%{filters['name']}%"))

            # 项目类别筛选（多选）
            if "project_types" in filters and filters["project_types"]:
                query = query.filter(Project.project_type.in_(filters["project_types"]))

            # 项目状态筛选
            if "status" in filters and filters["status"]:
                status_value = int(filters["status"])
                query = query.filter(Project.status == status_value)

            # 招募状态筛选
            if "recruitment_status" in filters and filters["recruitment_status"]:
                recruitment_status_value = int(filters["recruitment_status"])
                query = query.filter(
                    Project.recruitment_status == recruitment_status_value
                )

            # 所需技能筛选（多选）
            if "skill_type_ids" in filters and filters["skill_type_ids"]:
                skill_ids = [int(id) for id in filters["skill_type_ids"]]
                skill_filter = or_(
                    *[
                        SkillRequirement.skill_type_id == skill_id
                        for skill_id in skill_ids
                    ]
                )
                query = query.join(SkillRequirement).filter(skill_filter).distinct()

            # 描述关键词筛选
            if "keyword" in filters and filters["keyword"]:
                keyword = f"%{filters['keyword']}%"
                query = query.filter(
                    or_(Project.description.like(keyword), Project.goal.like(keyword))
                )

        # 返回项目列表
        projects = query.all()
        result = []
        for project in projects:
            project_dict = project.to_dict()
            # 添加点赞数
            project_dict["likes_count"] = ProjectLike.query.filter_by(
                project_id=project.id
            ).count()
            result.append(project_dict)
        return result

    @staticmethod
    def get_founder_project_list(filters=None):
        """
        获取项目列表，支持多种过滤条件
        :param filters: 过滤条件字典
        :return: 项目列表
        """
        query = Project.query

        if filters:
            # 项目创建者筛选
            if "user_id" in filters and filters["user_id"]:
                query = query.filter(Project.user_id == filters["user_id"])

            # 项目名称筛选
            if "name" in filters and filters["name"]:
                query = query.filter(Project.name.like(f"%{filters['name']}%"))

            # 项目类别筛选（多选）
            if "project_types" in filters and filters["project_types"]:
                query = query.filter(Project.project_type.in_(filters["project_types"]))

            # 项目状态筛选
            if "status" in filters and filters["status"]:
                status_value = int(filters["status"])
                query = query.filter(Project.status == status_value)

            # 招募状态筛选
            if "recruitment_status" in filters and filters["recruitment_status"]:
                recruitment_status_value = int(filters["recruitment_status"])
                query = query.filter(
                    Project.recruitment_status == recruitment_status_value
                )

            # 所需技能筛选（多选）
            if "skill_type_ids" in filters and filters["skill_type_ids"]:
                skill_ids = [int(id) for id in filters["skill_type_ids"]]
                skill_filter = or_(
                    *[
                        SkillRequirement.skill_type_id == skill_id
                        for skill_id in skill_ids
                    ]
                )
                query = query.join(SkillRequirement).filter(skill_filter).distinct()

            # 描述关键词筛选
            if "keyword" in filters and filters["keyword"]:
                keyword = f"%{filters['keyword']}%"
                query = query.filter(
                    or_(Project.description.like(keyword), Project.goal.like(keyword))
                )

        # 返回项目列表
        projects = query.all()
        result = []
        for project in projects:
            project_dict = project.to_dict()
            # 添加点赞数
            project_dict["likes_count"] = ProjectLike.query.filter_by(
                project_id=project.id
            ).count()
            result.append(project_dict)
        return result

    @staticmethod
    def get_participant_project_list(filters=None):
        """
        获取用户参与的项目列表，支持多种过滤条件
        :param filters: 过滤条件字典
        :return: 项目列表
        """
        query = Project.query

        if filters:
            # 项目参与者筛选
            if "user_id" in filters and filters["user_id"]:
                # 根据已接受的申请查询用户参与的项目
                user_id = filters["user_id"]
                # 通过子查询获取用户已接受申请的项目ID
                approved_project_ids = (
                    db.session.query(ProjectApplication.project_id)
                    .filter(
                        ProjectApplication.user_id == user_id,
                        ProjectApplication.status == ProjectApplication.STATUS_APPROVED,
                    )
                    .distinct()
                    .subquery()
                )

                # 使用子查询结果过滤项目
                query = query.filter(Project.id.in_(approved_project_ids))

            # 项目名称筛选
            if "name" in filters and filters["name"]:
                query = query.filter(Project.name.like(f"%{filters['name']}%"))

            # 项目类别筛选（多选）
            if "project_types" in filters and filters["project_types"]:
                query = query.filter(Project.project_type.in_(filters["project_types"]))

            # 项目状态筛选
            if "status" in filters and filters["status"]:
                status_value = int(filters["status"])
                query = query.filter(Project.status == status_value)

            # 招募状态筛选
            if "recruitment_status" in filters and filters["recruitment_status"]:
                recruitment_status_value = int(filters["recruitment_status"])
                query = query.filter(
                    Project.recruitment_status == recruitment_status_value
                )

            # 所需技能筛选（多选）
            if "skill_type_ids" in filters and filters["skill_type_ids"]:
                skill_ids = [int(id) for id in filters["skill_type_ids"]]
                skill_filter = or_(
                    *[
                        SkillRequirement.skill_type_id == skill_id
                        for skill_id in skill_ids
                    ]
                )
                query = query.join(SkillRequirement).filter(skill_filter).distinct()

            # 描述关键词筛选
            if "keyword" in filters and filters["keyword"]:
                keyword = f"%{filters['keyword']}%"
                query = query.filter(
                    or_(Project.description.like(keyword), Project.goal.like(keyword))
                )

        # 返回项目列表
        projects = query.all()
        return [
            {k: v for k, v in project.to_dict().items() if k != "recent_participants"}
            for project in projects
        ]

    @staticmethod
    def get_project_detail(project_id):
        """
        获取项目详情
        :param project_id: 项目ID
        :return: 项目详情
        """
        project = Project.query.get_or_404(project_id)
        project_dict = project.to_dict()
        project_dict["likes_count"] = ProjectLike.query.filter_by(
            project_id=project.id
        ).count()
        return project_dict

    @staticmethod
    def add_or_remove_project_like(project_id, user_id):
        """
        添加或移除项目点赞
        :param project_id: 项目ID
        :param user_id: 用户ID
        :return: 操作结果 (True为点赞，False为取消点赞)
        """
        existing_like = ProjectLike.query.filter_by(
            project_id=project_id, user_id=user_id
        ).first()
        if existing_like:
            db.session.delete(existing_like)
            db.session.commit()
            return False  # 已取消点赞
        else:
            new_like = ProjectLike(project_id=project_id, user_id=user_id)
            db.session.add(new_like)
            db.session.commit()
            return True  # 已点赞

    @staticmethod
    def get_top_liked_projects(limit=3):
        """
        获取点赞数最高的项目列表
        :param limit: 返回项目数量限制
        :return: 项目列表 (包含点赞数)
        """
        top_projects = (
            db.session.query(Project, func.count(ProjectLike.id).label("likes_count"))
            .outerjoin(ProjectLike)
            .group_by(Project.id)
            .order_by(func.count(ProjectLike.id).desc())
            .limit(limit)
            .all()
        )

        result = []
        for project, likes_count in top_projects:
            project_dict = project.to_dict()
            project_dict["likes_count"] = likes_count
            result.append(project_dict)
        return result

    @staticmethod
    def update_project(project_id, data, user_id):
        """
        更新项目信息
        :param project_id: 项目ID
        :param data: 包含更新信息的字典
        :param user_id: 操作者ID (必须是项目创建者)
        :return: 更新后的项目对象
        """
        # 验证项目是否存在
        project = Project.query.get_or_404(project_id)

        # 验证操作者权限
        if project.user_id != user_id:
            raise ValueError("您不是项目负责人，无权修改项目信息")

        # 更新基本信息
        if "name" in data:
            project.name = data["name"]
        if "project_type" in data:
            project.project_type = data["project_type"]
        if "end_time" in data:
            try:
                project.end_time = (
                    datetime.strptime(data["end_time"], "%Y-%m-%d %H:%M:%S")
                    if data["end_time"]
                    else None
                )
            except ValueError:
                raise ValueError(
                    "项目结束时间格式错误，请使用 'YYYY-MM-DD HH:MM:SS' 格式"
                )
        if "description" in data:
            project.description = data["description"]
        if "goal" in data:
            project.goal = data["goal"]
        if "status" in data:
            project.status = data["status"]
        if "recruitment_status" in data:
            project.recruitment_status = data["recruitment_status"]

        # 更新技能需求
        if "skill_requirements" in data:
            # 删除现有的技能需求
            SkillRequirement.query.filter_by(project_id=project_id).delete()

            # 添加新的技能需求
            for skill_data in data["skill_requirements"]:
                skill = SkillRequirement(
                    project_id=project_id,
                    skill_type_id=skill_data["skill_type_id"],
                    required_count=skill_data["required_count"],
                    importance=skill_data["importance"],
                    description=skill_data.get("description"),
                )
                project.skill_requirements.append(skill)

        db.session.commit()
        return project

    @staticmethod
    def delete_project(project_id, user_id):
        """
        删除项目
        :param project_id: 项目ID
        :param user_id: 操作者ID (必须是项目创建者)
        :return: 操作结果
        """
        # 验证项目是否存在
        project = Project.query.get_or_404(project_id)

        # 验证操作者权限
        if project.user_id != user_id:
            raise ValueError("您不是项目负责人，无权删除项目")

        # 删除项目相关的所有申请记录
        ProjectApplication.query.filter_by(project_id=project_id).delete()

        # 删除项目
        db.session.delete(project)
        db.session.commit()

        return {"success": True, "message": "项目已成功删除"}


class ProjectApplicationService:
    @staticmethod
    def apply_for_project(data, user_id):
        """
        申请加入项目
        :param data: 包含申请信息的字典
        :param user_id: 申请者用户ID
        :return: 创建的申请对象
        """
        # 验证项目是否存在
        project = Project.query.get_or_404(data["project_id"])

        # 验证是否已经申请过
        existing_application = ProjectApplication.query.filter_by(
            project_id=data["project_id"],
            user_id=user_id,
            skill_type_id=data["skill_type_id"],
            status=ProjectApplication.STATUS_PENDING,
        ).first()

        if existing_application:
            raise ValueError("您已经申请过该项目的这个技能岗位，请等待项目负责人处理")

        # 验证是否是项目创建者
        if project.user_id == user_id:
            raise ValueError("您不能申请加入自己创建的项目")

        # 验证项目是否开放申请
        if project.recruitment_status != Project.RECRUITMENT_OPEN:
            raise ValueError("该项目当前不接受申请")

        # 创建申请
        application = ProjectApplication(
            project_id=data["project_id"],
            user_id=user_id,
            skill_type_id=data["skill_type_id"],
            message=data.get("message"),
        )

        db.session.add(application)
        db.session.commit()

        return application

    @staticmethod
    def process_application(
        application_id, status, response_message=None, user_id=None
    ):
        """
        处理项目申请
        :param application_id: 申请ID
        :param status: 处理状态 (2-接受, 3-拒绝)
        :param response_message: 回复消息
        :param user_id: 处理人ID (必须是项目创建者)
        :return: 处理结果
        """
        # 验证申请是否存在
        application = ProjectApplication.query.get_or_404(application_id)

        # 验证状态
        if application.status != ProjectApplication.STATUS_PENDING:
            raise ValueError("该申请已处理，不能重复处理")

        # 验证处理人权限
        project = Project.query.get(application.project_id)
        if user_id and project.user_id != user_id:
            raise ValueError("您不是项目负责人，无权处理该申请")

        # 更新申请状态
        application.status = status
        application.response_message = response_message

        db.session.commit()

        return application

    @staticmethod
    def get_my_applications(user_id):
        """
        获取用户提交的申请列表
        :param user_id: 用户ID
        :return: 申请列表
        """
        applications = (
            ProjectApplication.query.filter_by(user_id=user_id)
            .order_by(ProjectApplication.created_at.desc())
            .all()
        )

        return [application.to_dict() for application in applications]

    @staticmethod
    def get_project_applications(project_id):
        """
        获取项目收到的申请列表（仅待处理的申请）
        :param project_id: 项目ID
        :return: 申请列表
        """
        # 验证项目是否存在
        project = Project.query.get_or_404(project_id)

        # 验证查询者权限
        if not project:
            raise ValueError("项目不存在")

        # 只获取待处理的申请
        applications = (
            ProjectApplication.query.filter_by(
                project_id=project_id, status=ProjectApplication.STATUS_PENDING
            )
            .order_by(ProjectApplication.created_at.desc())
            .all()
        )

        # 返回带有完整申请者信息的结果
        result = []
        for application in applications:
            # 获取申请信息作为基础
            app_data = application.to_dict()

            # 排除creator_info字段
            if "creator_info" in app_data:
                del app_data["creator_info"]

            # 获取申请者完整信息并合并
            if application.applicant:
                # 获取申请者数据
                applicant_data = application.applicant.to_dict()

                result.append(
                    {"applicant_data": applicant_data, "application_data": app_data}
                )
            else:
                # 如果没有找到申请者，只返回申请信息
                result.append(app_data)
        return result

    @staticmethod
    def remove_project_participant(project_id, participant_user_id, creator_id):
        """
        从项目中移除参与者
        :param project_id: 项目ID
        :param participant_user_id: 要移除的参与者用户ID
        :param creator_id: 操作者ID (必须是项目创建者)
        :return: 操作结果
        """
        # 验证项目是否存在
        project = Project.query.get_or_404(project_id)

        # 验证操作者权限
        if project.user_id != creator_id:
            raise ValueError("您不是项目负责人，无权移除参与者")

        # 验证参与者是否存在
        application = ProjectApplication.query.filter_by(
            project_id=project_id,
            user_id=participant_user_id,
            status=ProjectApplication.STATUS_APPROVED,
        ).first()

        if not application:
            raise ValueError("该用户不是项目参与者或未找到相关申请记录")

        # 删除申请记录
        db.session.delete(application)
        db.session.commit()

        return {"success": True, "message": "项目已成功移除"}


class ProjectDeliverableService:
    @staticmethod
    def get_deliverable_by_id(deliverable_id):
        """
        根据ID获取交付物
        :param deliverable_id: 交付物ID
        :return: 交付物对象
        """
        return ProjectDeliverable.query.get_or_404(deliverable_id)

    @staticmethod
    def create_deliverable(project_id, data, uploader_id, file=None):
        """
        创建新交付物
        :param project_id: 项目ID
        :param data: 包含交付物信息的字典
        :param uploader_id: 上传者用户ID
        :param file: 文件对象（可选，用于文件上传）
        :return: 创建的交付物对象
        """
        if file:
            # 处理文件上传
            filename = secure_filename(file.filename)
            # 确保目录存在
            upload_folder = os.path.join(
                current_app.root_path, "static", "deliverables", str(project_id)
            )
            os.makedirs(upload_folder, exist_ok=True)
            file_path = os.path.join(upload_folder, filename)
            file.save(file_path)
            file_url = f"/api/static/deliverables/{project_id}/{filename}"
            file_size = os.path.getsize(file_path)  # 获取文件大小
        else:
            file_url = data.get("file_url")
            file_size = data.get("file_size")

        deliverable = ProjectDeliverable(
            project_id=project_id,
            uploader_id=uploader_id,
            file_url=file_url,
            file_type=data.get("file_type"),
            file_name=data.get("file_name")
            or filename,  # 如果没有提供file_name，使用上传的文件名
            file_size=file_size,
            link_url=data.get("link_url"),
            status=data.get("status", 0),
        )

        db.session.add(deliverable)
        db.session.commit()
        return deliverable

    @staticmethod
    def get_deliverables_by_project(project_id):
        """
        获取项目下的所有交付物
        :param project_id: 项目ID
        :return: 交付物列表
        """
        deliverables = (
            ProjectDeliverable.query.filter_by(project_id=project_id)
            .order_by(ProjectDeliverable.created_at.desc())
            .all()
        )
        return [d.to_dict() for d in deliverables]

    @staticmethod
    def delete_deliverable(deliverable_id, uploader_id):
        """
        删除交付物
        :param deliverable_id: 交付物ID
        :param uploader_id: 上传者ID
        :return: 操作结果
        """
        deliverable = ProjectDeliverable.query.get_or_404(deliverable_id)
        if deliverable.uploader_id != uploader_id:
            raise ValueError("您不是上传者，无权删除该交付物")

        # 删除物理文件
        if deliverable.file_url and "/api/static/deliverables/" in deliverable.file_url:
            # 从URL中解析出相对路径
            relative_path = deliverable.file_url.split("/api/static/")[1]
            file_path = os.path.join(current_app.root_path, "static", relative_path)
            if os.path.exists(file_path):
                os.remove(file_path)
                # 尝试删除空目录
                dir_path = os.path.dirname(file_path)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)

        db.session.delete(deliverable)
        db.session.commit()
        return {"success": True, "message": "交付物删除成功"}

    @staticmethod
    def update_status(deliverable_id, status, reviewer_id=None):
        """
        更新交付物状态
        :param deliverable_id: 交付物ID
        :param status: 状态
        :param reviewer_id: 审核人ID (可选)
        :return: 更新后的交付物对象
        """
        deliverable = ProjectDeliverable.query.get_or_404(deliverable_id)
        deliverable.status = status
        db.session.commit()
        return deliverable

    @staticmethod
    def check_and_complete_project(project_id):
        """
        将项目标记为完成
        :param project_id: 项目ID
        """
        project = Project.query.get_or_404(project_id)
        if project.status == Project.STATUS_COMPLETED:  # 如果项目已经完成，则不重复处理
            return

        # # 获取所有已提交的交付物
        # submitted_deliverables = ProjectDeliverable.query.filter_by(
        #     project_id=project_id,
        #     status=ProjectDeliverable.STATUS_SUBMITTED
        # ).all()

        # # 获取所有已审核的交付物
        # reviewed_deliverables = ProjectDeliverable.query.filter_by(
        #     project_id=project_id,
        #     status=ProjectDeliverable.STATUS_REVIEWED
        # ).all()

        # # 如果所有已提交的交付物都已审核通过，则标记项目为完成
        # if len(submitted_deliverables) > 0 and len(submitted_deliverables) == len(reviewed_deliverables):
        project.status = Project.STATUS_COMPLETED
        db.session.commit()


class DeliverableConfirmationService:
    @staticmethod
    def confirm_deliverable(deliverable_id, user_id):
        """
        贡献者确认交付物
        :param deliverable_id: 交付物ID
        :param user_id: 确认者用户ID
        :return: 交付物确认对象
        """
        deliverable = ProjectDeliverable.query.get_or_404(deliverable_id)

        # 检查是否已确认
        existing_confirmation = DeliverableConfirmation.query.filter_by(
            deliverable_id=deliverable_id, user_id=user_id
        ).first()

        if existing_confirmation:
            raise ValueError("您已确认过该交付物")

        confirmation = DeliverableConfirmation(
            project_id=deliverable.project_id,
            deliverable_id=deliverable_id,
            user_id=user_id,
        )
        db.session.add(confirmation)
        db.session.commit()
        return confirmation

    @staticmethod
    def get_deliverable_confirm_status(deliverable_id, user_id):
        """
        查询某用户对某交付物的确认状态
        :param deliverable_id: 交付物ID
        :param user_id: 用户ID
        :return: 确认状态字典
        """
        confirmation = DeliverableConfirmation.query.filter_by(
            deliverable_id=deliverable_id, user_id=user_id
        ).first()
        return {"confirmed": True if confirmation else False}

    @staticmethod
    def get_project_confirm_status(project_id, user_id):
        """
        查询某用户对整个项目交付物的确认状态
        :param project_id: 项目ID
        :param user_id: 用户ID
        :return: 确认状态字典
        """
        # 获取用户在项目中的所有已批准的申请（即用户是该项目的参与者）
        approved_applications = ProjectApplication.query.filter_by(
            project_id=project_id,
            user_id=user_id,
            status=ProjectApplication.STATUS_APPROVED,
        ).all()

        if not approved_applications:  # 如果用户不是该项目的参与者，则无法确认交付物
            return {
                "total_deliverables": 0,
                "confirmed_deliverables": 0,
                "all_confirmed": False,
            }

        # 获取项目的所有交付物
        all_deliverables = ProjectDeliverable.query.filter_by(
            project_id=project_id
        ).all()
        total_deliverables = len(all_deliverables)

        confirmed_deliverables_count = 0
        for deliverable in all_deliverables:
            confirmation = DeliverableConfirmation.query.filter_by(
                deliverable_id=deliverable.id, user_id=user_id
            ).first()
            if confirmation and confirmation.confirmed:
                confirmed_deliverables_count += 1

        return {
            "total_deliverables": total_deliverables,
            "confirmed_deliverables": confirmed_deliverables_count,
            "all_confirmed": total_deliverables > 0
            and total_deliverables == confirmed_deliverables_count,
        }

    @staticmethod
    def check_and_complete_project_by_confirmation(project_id):
        """
        检查项目所有参与者是否都已确认所有交付物，如果是则标记项目为完成
        :param project_id: 项目ID
        """
        project = Project.query.get_or_404(project_id)
        if project.status == Project.STATUS_COMPLETED:  # 如果项目已经完成，则不重复处理
            return

        # 获取所有已批准的参与者
        approved_participants = ProjectApplication.query.filter_by(
            project_id=project_id, status=ProjectApplication.STATUS_APPROVED
        ).all()

        # 如果没有参与者，则项目不能通过确认来完成
        if not approved_participants:
            return

        all_participants_confirmed_all_deliverables = True
        for participant_app in approved_participants:
            participant_user_id = participant_app.user_id
            status = DeliverableConfirmationService.get_project_confirm_status(
                project_id, participant_user_id
            )
            if not status["all_confirmed"]:
                all_participants_confirmed_all_deliverables = False
                break

        if all_participants_confirmed_all_deliverables:
            project.status = Project.STATUS_COMPLETED
            db.session.commit()
