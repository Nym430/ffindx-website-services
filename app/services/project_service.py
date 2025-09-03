from app import db
from app.models.project import Project, SkillRequirement, SkillType, ProjectApplication
from datetime import datetime
from sqlalchemy import or_, and_

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
        skill_type = SkillType(
            name=data['name'],
            description=data.get('description')
        )
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
        project = Project(
            name=data['name'],
            project_type=data['project_type'],
            end_time=datetime.strptime(data['end_time'], '%Y-%m-%d %H:%M:%S'),
            description=data.get('description'),
            goal=data.get('goal'),
            status=Project.STATUS_IN_PROGRESS,
            recruitment_status=Project.RECRUITMENT_OPEN,
            user_id=user_id
        )
        
        # 添加技能需求
        skills_data = data.get('skill_requirements', [])
        for skill_data in skills_data:
            skill = SkillRequirement(
                skill_type_id=skill_data['skill_type_id'],
                required_count=skill_data['required_count'],
                importance=skill_data['importance'],
                description=skill_data.get('description')
            )
            project.skill_requirements.append(skill)
        
        # 保存到数据库
        db.session.add(project)
        db.session.commit()
        
        return project
    
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
            if 'name' in filters and filters['name']:
                query = query.filter(Project.name.like(f"%{filters['name']}%"))
            
            # 项目类别筛选（多选）
            if 'project_types' in filters and filters['project_types']:
                query = query.filter(Project.project_type.in_(filters['project_types']))
            
            # 项目状态筛选
            if 'status' in filters and filters['status']:
                status_value = int(filters['status'])
                query = query.filter(Project.status == status_value)
            
            # 招募状态筛选
            if 'recruitment_status' in filters and filters['recruitment_status']:
                recruitment_status_value = int(filters['recruitment_status'])
                query = query.filter(Project.recruitment_status == recruitment_status_value)
            
            # 所需技能筛选（多选）
            if 'skill_type_ids' in filters and filters['skill_type_ids']:
                skill_ids = [int(id) for id in filters['skill_type_ids']]
                skill_filter = or_(*[SkillRequirement.skill_type_id == skill_id for skill_id in skill_ids])
                query = query.join(SkillRequirement).filter(skill_filter).distinct()
            
            # 描述关键词筛选
            if 'keyword' in filters and filters['keyword']:
                keyword = f"%{filters['keyword']}%"
                query = query.filter(or_(
                    Project.description.like(keyword),
                    Project.goal.like(keyword)
                ))
                
        # 返回项目列表
        projects = query.all()
        return [project.to_dict() for project in projects]
    
    @staticmethod
    def get_project_detail(project_id):
        """
        获取项目详情
        :param project_id: 项目ID
        :return: 项目详情
        """
        project = Project.query.get_or_404(project_id)
        return project.to_dict()


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
        project = Project.query.get_or_404(data['project_id'])
        
        # 验证是否已经申请过
        existing_application = ProjectApplication.query.filter_by(
            project_id=data['project_id'],
            user_id=user_id,
            skill_type_id=data['skill_type_id'],
            status=ProjectApplication.STATUS_PENDING
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
            project_id=data['project_id'],
            user_id=user_id,
            skill_type_id=data['skill_type_id'],
            message=data.get('message')
        )
        
        db.session.add(application)
        db.session.commit()
        
        return application
    
    @staticmethod
    def process_application(application_id, status, response_message=None, user_id=None):
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
        applications = ProjectApplication.query.filter_by(user_id=user_id).order_by(
            ProjectApplication.created_at.desc()
        ).all()
        
        return [application.to_dict() for application in applications]
    
    @staticmethod
    def get_project_applications(project_id, user_id=None):
        """
        获取项目收到的申请列表
        :param project_id: 项目ID
        :param user_id: 当前用户ID (用于验证是否为项目创建者)
        :return: 申请列表
        """
        # 验证项目是否存在
        project = Project.query.get_or_404(project_id)
        
        # 验证查询者权限
        if user_id and project.user_id != user_id:
            raise ValueError("您不是项目负责人，无权查看申请列表")
        
        applications = ProjectApplication.query.filter_by(project_id=project_id).order_by(
            ProjectApplication.created_at.desc()
        ).all()
        
        return [application.to_dict() for application in applications]

    @staticmethod
    def delete_application(application_id, user_id):
        """
        删除项目申请
        :param application_id: 申请ID
        :param user_id: 用户ID
        """
        application = ProjectApplication.query.get_or_404(application_id)
        
        if application.user_id != user_id:
            raise ValueError("您无权删除此申请")
            
        db.session.delete(application)
        db.session.commit()

    @staticmethod
    def update_application(application_id, user_id, data):
        """
        更新项目申请
        :param application_id: 申请ID
        :param user_id: 用户ID
        :param data: 更新的数据
        """
        application = ProjectApplication.query.get_or_404(application_id)
        
        if application.user_id != user_id:
            raise ValueError("您无权编辑此申请")
            
        if 'message' in data:
            application.message = data['message']
        if 'skill_type_id' in data:
            application.skill_type_id = data['skill_type_id']
            
        db.session.commit()
        return application 