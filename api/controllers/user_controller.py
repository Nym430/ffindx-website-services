from flask import Blueprint, request, jsonify
from api.services.user_service import UserService

user_bp = Blueprint("user", __name__, url_prefix="/api")


@user_bp.route("/users", methods=["POST"])
def create_user():
    """
    创建用户API
    请求参数:
    {
        "email": "用户邮箱",  # 必填
        "full_name": "用户全名",
        "gender": "性别",
        "mbti": "MBTI性格类型",
        "star_sign": "星座",
        "skills": "技能",
        "interests": "兴趣",
        "year_of_study": "学习年限",
        "major": "专业",
        "key_factors": 关键因素(字符串或对象),
        "lightning_answers": 快速回答(对象),
        "picture": "用户头像URL",
        "user_id": "Auth0用户标识"
    }
    """
    data = request.get_json()

    # 参数验证
    if "email" not in data or not data["email"]:
        return jsonify({"error": "邮箱是必填字段"}), 400

    try:
        # 创建用户
        user = UserService.create_user(data)
        return jsonify({"message": "用户创建成功", "data": user.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 200
    except Exception as e:
        return jsonify({"error": f"创建用户失败: {str(e)}"}), 500


@user_bp.route("/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    """
    获取用户详情API

    路径参数:
    - user_id: 用户ID
    """
    try:
        user = UserService.get_user_by_id(user_id)
        return jsonify({"data": user.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": f"获取用户详情失败: {str(e)}"}), 500


@user_bp.route("/users/by-auth-id", methods=["GET"])
def get_user_by_auth_id():
    """
    根据Auth0标识获取用户API

    路径参数:
    - auth_id: Auth0用户标识
    """
    try:
        auth_id = request.args.get("auth_id")
        user = UserService.get_user_by_auth_id(auth_id)
        if not user:
            return jsonify({"error": "用户不存在"}), 404
        return jsonify({"data": user.to_dict()}), 200
    except Exception as e:
        return jsonify({"error": f"获取用户详情失败: {str(e)}"}), 500


@user_bp.route("/users/by-auth-id", methods=["PUT"])
def update_user():
    """
    更新用户资料API
    路径参数:
    - auth_id: Auth0用户标识
    请求体:
    {
        "email": "用户邮箱",
        "full_name": "用户全名",
        "gender": "性别",
        "mbti": "MBTI性格类型",
        "star_sign": "星座",
        "skills": "技能",
        "interests": "兴趣",
        "year_of_study": "学习年限",
        "major": "专业",
        "key_factors": {}, # JSON格式
        "lightning_answers": {}, # JSON格式
        "fun_facts": {}, # JSON格式
        "best_working_experience": "",
        "tags": {}, # JSON格式
        "picture": "用户头像URL"
    }
    """
    data = request.get_json()

    try:
        auth_id = request.args.get("auth_id")
        user = UserService.update_user(auth_id, data)
        return jsonify({"message": "用户资料更新成功", "data": user.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"更新用户资料失败: {str(e)}"}), 500


@user_bp.route("/users", methods=["GET"])
def get_user_list():
    """
    获取用户列表API

    查询参数:
    - email: 邮箱
    - full_name: 全名
    - gender: 性别
    - mbti: MBTI性格类型
    - star_sign: 星座
    - major: 专业
    - user_id: Auth0用户标识
    """
    filters = {}

    # 获取并处理查询参数
    if request.args.get("email"):
        filters["email"] = request.args.get("email")

    if request.args.get("full_name"):
        filters["full_name"] = request.args.get("full_name")

    if request.args.get("gender"):
        filters["gender"] = request.args.get("gender")

    if request.args.get("mbti"):
        filters["mbti"] = request.args.get("mbti")

    if request.args.get("star_sign"):
        filters["star_sign"] = request.args.get("star_sign")

    if request.args.get("major"):
        filters["major"] = request.args.get("major")

    if request.args.get("user_id"):
        filters["user_id"] = request.args.get("user_id")

    try:
        users = UserService.get_user_list(filters)
        return jsonify({"data": users, "total": len(users)}), 200
    except Exception as e:
        return jsonify({"error": f"获取用户列表失败: {str(e)}"}), 500


@user_bp.route("/users/participant", methods=["GET"])
def get_participant_user_list():
    """
    获取参与者用户列表API

    查询参数:
    - project_id: 项目ID
    - email: 邮箱
    - full_name: 全名
    - gender: 性别
    - mbti: MBTI性格类型
    - star_sign: 星座
    - major: 专业
    - user_id: Auth0用户标识
    """
    filters = {}
    if request.args.get("project_id"):
        filters["project_id"] = request.args.get("project_id")
    # 获取并处理查询参数
    if request.args.get("email"):
        filters["email"] = request.args.get("email")

    if request.args.get("full_name"):
        filters["full_name"] = request.args.get("full_name")

    if request.args.get("gender"):
        filters["gender"] = request.args.get("gender")

    if request.args.get("mbti"):
        filters["mbti"] = request.args.get("mbti")

    if request.args.get("star_sign"):
        filters["star_sign"] = request.args.get("star_sign")

    if request.args.get("major"):
        filters["major"] = request.args.get("major")

    if request.args.get("user_id"):
        filters["user_id"] = request.args.get("user_id")

    try:
        users = UserService.get_participant_user_list(filters)
        return jsonify({"data": users, "total": len(users)}), 200
    except Exception as e:
        return jsonify({"error": f"获取用户列表失败: {str(e)}"}), 500
