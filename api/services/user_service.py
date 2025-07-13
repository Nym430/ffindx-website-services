from app import db
from api.models.project import ProjectApplication, Project, SkillType
from api.models.user import User
from sqlalchemy import or_


class UserService:
    @staticmethod
    def create_user(data):
        """
        创建新用户
        :param data: 包含用户信息的字典
        :return: 创建的用户对象
        """
        # 检查邮箱是否已存在
        existing_user = User.query.filter_by(email=data["email"]).first()
        if existing_user:
            raise ValueError(f"邮箱 {data['email']} 已被注册")

        # 创建用户
        user = User(
            email=data["email"],
            full_name=data.get("full_name"),
            gender=data.get("gender"),
            mbti=data.get("mbti"),
            star_sign=data.get("star_sign"),
            skills=data.get("skills"),
            interests=data.get("interests"),
            year_of_study=data.get("year_of_study"),
            major=data.get("major"),
            picture=data.get("picture"),
            user_id=data.get("user_id"),
        )

        # 处理关键因素
        if "key_factors" in data:
            user.set_key_factors(data["key_factors"])

        # 处理快速回答
        if "lightning_answers" in data:
            user.set_lightning_answers(data["lightning_answers"])

        # 处理趣事
        if "fun_facts" in data:
            user.set_fun_facts(data["fun_facts"])

        # 处理标签
        if "tags" in data:
            user.set_tags(data["tags"])

        # 保存到数据库
        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def get_user_by_id(user_id):
        """
        根据ID获取用户
        :param user_id: 用户ID
        :return: 用户对象
        """
        return User.query.get_or_404(user_id)

    @staticmethod
    def update_user(user_id, data):
        """
        更新用户信息
        :param user_id: 要更新的用户ID (Auth0 user_id)
        :param data: 包含更新信息的字典
        :return: 更新后的用户对象
        """
        user = User.query.filter_by(user_id=user_id).first()
        if not user:
            raise ValueError("用户未找到")

        if "email" in data:
            user.email = data["email"]
        if "full_name" in data:
            user.full_name = data["full_name"]
        if "gender" in data:
            user.gender = data["gender"]
        if "mbti" in data:
            user.mbti = data["mbti"]
        if "star_sign" in data:
            user.star_sign = data["star_sign"]
        if "skills" in data:
            user.skills = data["skills"]
        if "interests" in data:
            user.interests = data["interests"]
        if "year_of_study" in data:
            user.year_of_study = data["year_of_study"]
        if "major" in data:
            user.major = data["major"]
        if "picture" in data:
            user.picture = data["picture"]
        if "best_working_experience" in data:
            user.best_working_experience = data["best_working_experience"]

        if "key_factors" in data:
            user.set_key_factors(data["key_factors"])
        if "lightning_answers" in data:
            user.set_lightning_answers(data["lightning_answers"])
        if "fun_facts" in data:
            user.set_fun_facts(data["fun_facts"])
        if "tags" in data:
            user.set_tags(data["tags"])

        db.session.commit()
        return user

    @staticmethod
    def get_user_by_email(email):
        """
        根据邮箱获取用户
        :param email: 用户邮箱
        :return: 用户对象
        """
        return User.query.filter_by(email=email).first()

    @staticmethod
    def get_user_by_auth_id(auth_id):
        """
        根据Auth0标识获取用户
        :param auth_id: Auth0用户标识
        :return: 用户对象
        """
        return User.query.filter_by(user_id=auth_id).first()

    @staticmethod
    def get_user_list(filters=None):
        """
        获取用户列表，支持过滤条件
        :param filters: 过滤条件字典
        :return: 用户列表
        """
        query = User.query

        if filters:
            # 邮箱筛选
            if "email" in filters and filters["email"]:
                query = query.filter(User.email.like(f"%{filters['email']}%"))

            # 全名筛选
            if "full_name" in filters and filters["full_name"]:
                query = query.filter(User.full_name.like(f"%{filters['full_name']}%"))

            # 性别筛选
            if "gender" in filters and filters["gender"]:
                query = query.filter(User.gender == filters["gender"])

            # MBTI筛选
            if "mbti" in filters and filters["mbti"]:
                query = query.filter(User.mbti == filters["mbti"])

            # 星座筛选
            if "star_sign" in filters and filters["star_sign"]:
                query = query.filter(User.star_sign == filters["star_sign"])

            # 专业筛选
            if "major" in filters and filters["major"]:
                query = query.filter(User.major.like(f"%{filters['major']}%"))

            # Auth0标识筛选
            if "user_id" in filters and filters["user_id"]:
                query = query.filter(User.user_id == filters["user_id"])

        # 返回用户列表
        users = query.all()
        return [user.to_dict() for user in users]

    @staticmethod
    def get_participant_user_list(filters=None):
        """
        获取参与者用户列表，支持过滤条件
        :param filters: 过滤条件字典
        :return: 用户列表（包含项目名称和项目技能）
        """
        query = User.query
        project_id = None

        if filters:
            # 项目ID筛选
            if "project_id" in filters and filters["project_id"]:
                project_id = filters["project_id"]
                # 通过子查询获取项目参与者
                project_participants = (
                    db.session.query(ProjectApplication.user_id)
                    .filter(
                        ProjectApplication.project_id == project_id,
                        ProjectApplication.status == ProjectApplication.STATUS_APPROVED,
                    )
                    .distinct()
                    .subquery()
                )

                query = query.filter(User.user_id.in_(project_participants))

            # 邮箱筛选
            if "email" in filters and filters["email"]:
                query = query.filter(User.email.like(f"%{filters['email']}%"))

            # 全名筛选
            if "full_name" in filters and filters["full_name"]:
                query = query.filter(User.full_name.like(f"%{filters['full_name']}%"))

            # 性别筛选
            if "gender" in filters and filters["gender"]:
                query = query.filter(User.gender == filters["gender"])

            # MBTI筛选
            if "mbti" in filters and filters["mbti"]:
                query = query.filter(User.mbti == filters["mbti"])

            # 星座筛选
            if "star_sign" in filters and filters["star_sign"]:
                query = query.filter(User.star_sign == filters["star_sign"])

            # 专业筛选
            if "major" in filters and filters["major"]:
                query = query.filter(User.major.like(f"%{filters['major']}%"))

            # Auth0标识筛选
            if "user_id" in filters and filters["user_id"]:
                query = query.filter(User.user_id == filters["user_id"])

        # 获取用户列表
        users = query.all()
        result = []

        for user in users:
            user_data = user.to_dict()

            # 如果指定了项目ID，查询该用户在项目中的技能和项目名称
            if project_id:
                # 查询用户在该项目的申请
                application = ProjectApplication.query.filter_by(
                    project_id=project_id,
                    user_id=user.user_id,
                    status=ProjectApplication.STATUS_APPROVED,
                ).first()

                if application:
                    # 获取项目名称
                    project = Project.query.get(project_id)
                    if project:
                        user_data["project_name"] = project.name
                    else:
                        user_data["project_name"] = "未知项目"

                    # 获取技能类型名称
                    skill_type = SkillType.query.get(application.skill_type_id)
                    if skill_type:
                        user_data["project_skill"] = skill_type.name
                    else:
                        user_data["project_skill"] = "未知技能"
                else:
                    user_data["project_name"] = "未知项目"
                    user_data["project_skill"] = "未知技能"
            else:
                # 如果没有指定项目ID，这些字段设为空
                user_data["project_name"] = ""
                user_data["project_skill"] = ""

            result.append(user_data)

        return result
