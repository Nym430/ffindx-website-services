from flask import Blueprint, app, request, jsonify
from api.services.project_service import (
    SkillTypeService,
    ProjectApplicationService,
    ProjectDeliverableService,
    DeliverableConfirmationService,
    ProjectService,
)
from api.models.project_contribution import ProjectContribution

project_bp = Blueprint("project", __name__, url_prefix="/api")


@project_bp.route("/skill-types", methods=["GET"])
def get_skill_types():
    """
    获取所有技能类型API
    """
    try:
        skill_types = SkillTypeService.get_all_skill_types()
        return jsonify({"data": skill_types, "total": len(skill_types)}), 200
    except Exception as e:
        return jsonify({"error": f"获取技能类型失败: {str(e)}"}), 500


@project_bp.route("/skill-types", methods=["POST"])
def create_skill_type():
    """
    创建技能类型API
    请求参数:
    {
        "name": "技能类型名称",
        "description": "技能类型描述"  # 可选
    }
    """
    data = request.get_json()

    # 参数验证
    if not data.get("name"):
        return jsonify({"error": "缺少必填字段: name"}), 400

    try:
        skill_type = SkillTypeService.create_skill_type(data)
        return (
            jsonify({"message": "技能类型创建成功", "data": skill_type.to_dict()}),
            201,
        )
    except Exception as e:
        return jsonify({"error": f"创建技能类型失败: {str(e)}"}), 500


@project_bp.route("/projects", methods=["POST"])
def create_project():
    """
    创建项目API
    请求参数:
    {
        "name": "项目名称",
        "project_type": "项目类型",
        "end_time": "项目结束时间",
        "description": "项目描述",  # 可选
        "goal": "项目目标",  # 可选
        "user_id": 创建者用户ID,  # 必填
        "skill_requirements": [
            {
                "skill_type_id": 技能类型ID,
                "required_count": 数量,
                "importance": 重要程度(1-5),
                "description": "技能描述"  # 可选
            }
        ]
    }
    """
    data = request.get_json()

    # 参数验证
    required_fields = ["name", "project_type", "user_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"缺少必填字段: {field}"}), 400

    # 验证技能需求数据
    if "skill_requirements" in data:
        for i, skill in enumerate(data["skill_requirements"]):
            required_skill_fields = ["skill_type_id", "required_count", "importance"]
            for field in required_skill_fields:
                if field not in skill:
                    return (
                        jsonify({"error": f"第{i+1}个技能需求缺少必填字段: {field}"}),
                        400,
                    )

            # 验证重要程度是否在1-5范围
            if not (1 <= skill["importance"] <= 5):
                return (
                    jsonify({"error": f"第{i+1}个技能需求的重要程度必须在1-5之间"}),
                    400,
                )

            # 验证技能类型ID是否存在
            try:
                SkillTypeService.get_skill_type_by_id(skill["skill_type_id"])
            except:
                return jsonify({"error": f"第{i+1}个技能需求的技能类型ID不存在"}), 400

    # 获取创建者ID
    user_id = data.get("user_id")

    try:
        project = ProjectService.create_project(data, user_id)
        return jsonify({"message": "项目创建成功", "data": project.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"创建项目失败: {str(e)}"}), 500


@project_bp.route("/projects", methods=["GET"])
def get_project_list():
    """
    获取项目列表API，支持多种过滤条件

    请求参数 (URL查询参数):
    - name: 项目名称
    - project_types: 项目类别，多个用逗号分隔
    - status: 项目状态 (1-进行中、2-已完成)
    - recruitment_status: 招募状态 (1-开放申请、2-招募结束)
    - skill_type_ids: 所需技能ID，多个用逗号分隔
    - keyword: 关键词搜索（搜索项目描述和目标）
    """
    filters = {}

    # 获取并处理查询参数
    if request.args.get("name"):
        filters["name"] = request.args.get("name")

    if request.args.get("project_types"):
        filters["project_types"] = request.args.get("project_types").split(",")

    if request.args.get("status"):
        filters["status"] = request.args.get("status")

    if request.args.get("recruitment_status"):
        filters["recruitment_status"] = request.args.get("recruitment_status")

    if request.args.get("skill_type_ids"):
        filters["skill_type_ids"] = request.args.get("skill_type_ids").split(",")

    if request.args.get("keyword"):
        filters["keyword"] = request.args.get("keyword")

    try:
        projects = ProjectService.get_project_list(filters)
        return jsonify({"data": projects, "total": len(projects)}), 200
    except Exception as e:
        return jsonify({"error": f"获取项目列表失败: {str(e)}"}), 500


@project_bp.route("/projects/founder", methods=["GET"])
def get_founder_projects():
    """
    获取我创建的项目列表API

    请求体参数:
    - user_id: 用户ID (必需)

    请求参数 (URL查询参数):
    - name: 项目名称
    - project_types: 项目类别，多个用逗号分隔
    - status: 项目状态 (1-进行中、2-已完成)
    - recruitment_status: 招募状态 (1-开放申请、2-招募结束)
    - skill_type_ids: 所需技能ID，多个用逗号分隔
    - keyword: 关键词搜索（搜索项目描述和目标）
    """
    # 从请求体获取 user_id
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "缺少必需的 user_id 参数"}), 400

    # 首先创建基础过滤条件，包含 user_id
    filters = {"user_id": user_id}

    # 获取并处理其他查询参数
    if request.args.get("name"):
        filters["name"] = request.args.get("name")

    if request.args.get("project_types"):
        filters["project_types"] = request.args.get("project_types").split(",")

    if request.args.get("status"):
        filters["status"] = request.args.get("status")

    if request.args.get("recruitment_status"):
        filters["recruitment_status"] = request.args.get("recruitment_status")

    if request.args.get("skill_type_ids"):
        filters["skill_type_ids"] = request.args.get("skill_type_ids").split(",")

    if request.args.get("keyword"):
        filters["keyword"] = request.args.get("keyword")

    try:
        projects = ProjectService.get_founder_project_list(filters)
        return jsonify({"data": projects, "total": len(projects)}), 200
    except Exception as e:
        return jsonify({"error": f"获取项目列表失败: {str(e)}"}), 500


@project_bp.route("/projects/participant", methods=["GET"])
def get_participant_projects():
    """
    获取我参与的项目列表API

    请求体参数:
    - user_id: 用户ID (必需)

    请求参数 (URL查询参数):
    - name: 项目名称
    - project_types: 项目类别，多个用逗号分隔
    - status: 项目状态 (1-进行中、2-已完成)
    - recruitment_status: 招募状态 (1-开放申请、2-招募结束)
    - skill_type_ids: 所需技能ID，多个用逗号分隔
    - keyword: 关键词搜索（搜索项目描述和目标）
    """
    # 从请求体获取 user_id
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "缺少必需的 user_id 参数"}), 400

    # 首先创建基础过滤条件，包含 user_id
    filters = {"user_id": user_id}

    # 获取并处理其他查询参数
    if request.args.get("name"):
        filters["name"] = request.args.get("name")

    if request.args.get("project_types"):
        filters["project_types"] = request.args.get("project_types").split(",")

    if request.args.get("status"):
        filters["status"] = request.args.get("status")

    if request.args.get("recruitment_status"):
        filters["recruitment_status"] = request.args.get("recruitment_status")

    if request.args.get("skill_type_ids"):
        filters["skill_type_ids"] = request.args.get("skill_type_ids").split(",")

    if request.args.get("keyword"):
        filters["keyword"] = request.args.get("keyword")

    try:
        projects = ProjectService.get_participant_project_list(filters)
        return jsonify({"data": projects, "total": len(projects)}), 200
    except Exception as e:
        return jsonify({"error": f"获取项目列表失败: {str(e)}"}), 500


@project_bp.route("/projects/<int:project_id>", methods=["GET"])
def get_project_detail(project_id):
    """
    获取项目详情API

    路径参数:
    - project_id: 项目ID
    """
    try:
        project = ProjectService.get_project_detail(project_id)
        return jsonify({"data": project}), 200
    except Exception as e:
        return jsonify({"error": f"获取项目详情失败: {str(e)}"}), 500


@project_bp.route("/projects/<int:project_id>/like", methods=["POST"])
def like_project(project_id):
    """
    点赞或取消点赞项目API
    路径参数:
    - project_id: 项目ID
    请求体:
    {
        "user_id": "用户ID"  # 必填
    }
    """
    data = request.get_json()
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error": "缺少必需的 user_id 参数"}), 400

    print(f"Attempting to like project {project_id} by user {user_id}")
    print(f"ProjectService type: {type(app.services.project_service.ProjectService)}")
    print(
        f"Has add_or_remove_project_like: {'add_or_remove_project_like' in dir(app.services.project_service.ProjectService)}"
    )

    try:
        liked = ProjectService.add_or_remove_project_like(project_id, user_id)
        if liked:
            return jsonify({"message": "项目点赞成功"}), 200
        else:
            return jsonify({"message": "项目取消点赞成功"}), 200
    except Exception as e:
        return jsonify({"error": f"操作失败: {str(e)}"}), 500


@project_bp.route("/projects/leaderboard", methods=["GET"])
def get_project_leaderboard():
    """
    获取项目点赞排行榜API
    """
    try:
        top_projects = ProjectService.get_top_liked_projects()
        return jsonify({"data": top_projects, "total": len(top_projects)}), 200
    except Exception as e:
        return jsonify({"error": f"获取排行榜失败: {str(e)}"}), 500


@project_bp.route("/project-applications", methods=["POST"])
def apply_for_project():
    """
    申请加入项目API
    请求参数:
    {
        "project_id": 项目ID,
        "skill_type_id": 技能类型ID,
        "message": "申请消息"  # 可选
    }
    """
    data = request.get_json()


    # 参数验证
    required_fields = ["project_id", "skill_type_id"]
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"缺少必填字段: {field}"}), 400

    if not user_id:
        return jsonify({"error": "缺少必需的 user_id 参数"}), 400

    try:
        application = ProjectApplicationService.apply_for_project(data, user_id)
        return jsonify({"message": "申请提交成功", "data": application.to_dict()}), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"提交申请失败: {str(e)}"}), 500


@project_bp.route("/project-applications/<int:application_id>/process", methods=["PUT"])
def process_application(application_id):
    """
    处理项目申请API
    路径参数:
    - application_id: 申请ID
    请求体:
    {
        "status": 处理状态 (2-接受, 3-拒绝),
        "response_message": "回复消息"  # 可选
    }
    请求参数 (URL查询参数):
    - user_id: 处理人ID (必需，必须是项目创建者)
    """
    data = request.get_json()
    user_id = request.args.get("user_id")

    # 参数验证
    if "status" not in data:
        return jsonify({"error": "缺少必填字段: status"}), 400

    if not user_id:
        return jsonify({"error": "缺少必需的 user_id 参数"}), 400

    try:
        application = ProjectApplicationService.process_application(
            application_id, data["status"], data.get("response_message"), user_id
        )
        return jsonify({"message": "申请处理成功", "data": application.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"处理申请失败: {str(e)}"}), 500


@project_bp.route("/project-applications/<int:application_id>", methods=["PUT"])
def update_application(application_id):
    """
    更新项目申请API (申请者本人)
    路径参数:
    - application_id: 申请ID
    请求体:
    {
        "message": "新的申请消息",
        "skill_type_id": 新的技能类型ID
    }
    请求参数 (URL查询参数):
    - user_id: 申请者ID (必需)
    """
    data = request.get_json()
    user_id = request.args.get("user_id")

    if not user_id:
        return jsonify({"error": "缺少必需的 user_id 参数"}), 400

    try:
        application = ProjectApplicationService.update_application(
            application_id, user_id, data
        )
        return jsonify({"message": "申请更新成功", "data": application.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"更新申请失败: {str(e)}"}), 500


@project_bp.route("/project-applications/<int:application_id>", methods=["DELETE"])
def delete_application(application_id):
    """
    删除项目申请API (申请者本人)
    路径参数:
    - application_id: 申请ID
    请求参数 (URL查询参数):
    - user_id: 申请者ID (必需)
    """
    user_id = request.args.get("user_id")


    if not user_id:
        return jsonify({"error": "缺少必需的 user_id 参数"}), 400

    try:
        result = ProjectApplicationService.delete_application(application_id, user_id)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"删除申请失败: {str(e)}"}), 500


@project_bp.route("/my-applications", methods=["GET"])
def get_my_applications():
    """
    获取用户提交的申请列表API

    查询参数:
    - user_id: 用户ID (必需)
    """
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "缺少必需的 user_id 参数"}), 400

    try:
        applications = ProjectApplicationService.get_my_applications(user_id)
        return jsonify({"data": applications, "total": len(applications)}), 200
    except Exception as e:
        return jsonify({"error": f"获取我的申请失败: {str(e)}"}), 500


@project_bp.route("/projects/<int:project_id>/applications", methods=["GET"])
def get_project_applications(project_id):
    """
    获取项目收到的申请列表API (仅待处理的申请)

    路径参数:
    - project_id: 项目ID
    """
    try:
        applications = ProjectApplicationService.get_project_applications(project_id)
        return jsonify({"data": applications, "total": len(applications)}), 200
    except Exception as e:
        return jsonify({"error": f"获取项目申请失败: {str(e)}"}), 500


@project_bp.route("/projects/participants", methods=["DELETE"])
def remove_project_participant():
    """
    从项目中移除参与者API
    请求体:
    {
        "project_id": 项目ID,
        "participant_user_id": 要移除的参与者用户ID,
        "creator_id": 操作者ID (必须是项目创建者)
    }
    """
    data = request.get_json()
    project_id = data.get("project_id")
    participant_user_id = data.get("participant_user_id")
    creator_id = data.get("creator_id")

    if not all([project_id, participant_user_id, creator_id]):
        return jsonify({"error": "缺少必需的参数"}), 400

    try:
        result = ProjectApplicationService.remove_project_participant(
            project_id, participant_user_id, creator_id
        )
        return jsonify({"message": result["message"]}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"移除参与者失败: {str(e)}"}), 500


@project_bp.route("/projects/<int:project_id>", methods=["PUT"])
def update_project(project_id):
    """
    更新项目信息API
    路径参数:
    - project_id: 项目ID
    请求体:
    {
        "name": "项目名称",
        "project_type": "项目类型",
        "end_time": "项目结束时间",
        "description": "项目描述",  # 可选
        "goal": "项目目标",  # 可选
        "status": 项目状态 (1-进行中、2-已完成),
        "recruitment_status": 招募状态 (1-开放申请、2-招募结束),
        "skill_requirements": [
            {
                "skill_type_id": 技能类型ID,
                "required_count": 数量,
                "importance": 重要程度(1-5),
                "description": "技能描述"  # 可选
            }
        ]
    }
    请求参数 (URL查询参数):
    - user_id: 操作者ID (必需，必须是项目创建者)
    """
    data = request.get_json()


    if not user_id:
        return jsonify({"error": "缺少必需的 user_id 参数"}), 400

    try:
        project = ProjectService.update_project(project_id, data, user_id)
        return jsonify({"message": "项目更新成功", "data": project.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"更新项目失败: {str(e)}"}), 500


@project_bp.route("/projects", methods=["DELETE"])
def delete_project():
    """
    删除项目API
    请求体:
    {
        "project_id": 项目ID,
        "user_id": 操作者ID (必需，必须是项目创建者)
    }
    """
    data = request.get_json()
    project_id = data.get("project_id")
    user_id = data.get("user_id")

    if not all([project_id, user_id]):
        return jsonify({"error": "缺少必需的参数"}), 400

    try:
        result = ProjectService.delete_project(project_id, user_id)
        return jsonify({"message": result["message"]}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"删除项目失败: {str(e)}"}), 500


@project_bp.route("/projects/deliverables", methods=["GET"])
def get_project_deliverables():
    """
    获取项目交付物列表API

    查询参数:
    - project_id: 项目ID (必需)
    """
    project_id = request.args.get("project_id")
    if not project_id:
        return jsonify({"error": "缺少必需的 project_id 参数"}), 400

    try:
        deliverables = ProjectDeliverableService.get_deliverables_by_project(project_id)
        return jsonify({"data": deliverables, "total": len(deliverables)}), 200
    except Exception as e:
        return jsonify({"error": f"获取交付物列表失败: {str(e)}"}), 500


@project_bp.route("/projects/deliverables", methods=["POST"])
def upload_project_deliverable():
    """
    上传项目交付物API
    表单数据:
    - project_id: 项目ID
    - uploader_id: 上传者用户ID
    - file: 上传的文件 (如果file_url为空)
    - file_url: 外部文件URL (如果文件为空)
    - file_type: 文件类型
    - file_name: 文件名
    - file_size: 文件大小
    - link_url: 外部链接 (如果file_url为空)
    """
    project_id = request.form.get("project_id")
    uploader_id = request.form.get("uploader_id")
    file = request.files.get("file")
    file_url = request.form.get("file_url")
    file_type = request.form.get("file_type")
    file_name = request.form.get("file_name")
    file_size = request.form.get("file_size")
    link_url = request.form.get("link_url")

    if not all([project_id, uploader_id]) or (
        not file and not file_url and not link_url
    ):
        return jsonify({"error": "缺少必需的参数或文件/URL"}), 400

    try:
        deliverable = ProjectDeliverableService.create_deliverable(
            int(project_id),
            {
                "file_url": file_url,
                "file_type": file_type,
                "file_name": file_name,
                "file_size": file_size,
                "link_url": link_url,
            },
            uploader_id,
            file,
        )
        return (
            jsonify({"message": "交付物上传成功", "data": deliverable.to_dict()}),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"上传交付物失败: {str(e)}"}), 500


@project_bp.route("/deliverables", methods=["DELETE"])
def delete_project_deliverable():
    """
    删除项目交付物API
    请求体:
    {
        "deliverable_id": 交付物ID,
        "uploader_id": 上传者用户ID (必需)
    }
    """
    data = request.get_json()
    deliverable_id = data.get("deliverable_id")
    uploader_id = data.get("uploader_id")

    if not all([deliverable_id, uploader_id]):
        return jsonify({"error": "缺少必需的参数"}), 400

    try:
        result = ProjectDeliverableService.delete_deliverable(
            deliverable_id, uploader_id
        )
        return jsonify({"message": result["message"]}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"删除交付物失败: {str(e)}"}), 500


@project_bp.route("/deliverables/status", methods=["PUT"])
def update_deliverable_status():
    """
    更新交付物状态API
    请求体:
    {
        "deliverable_id": 交付物ID,
        "status": 状态 (0-草稿，1-已提交，2-已审核),
        "reviewer_id": 审核人ID (如果状态为已审核)
    }
    """
    data = request.get_json()
    deliverable_id = data.get("deliverable_id")
    status = data.get("status")
    reviewer_id = data.get("reviewer_id")

    if not all([deliverable_id, status is not None]):
        return jsonify({"error": "缺少必需的参数"}), 400

    try:
        deliverable = ProjectDeliverableService.update_status(
            deliverable_id, status, reviewer_id
        )
        return (
            jsonify({"message": "交付物状态更新成功", "data": deliverable.to_dict()}),
            200,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"更新交付物状态失败: {str(e)}"}), 500


@project_bp.route("/projects/complete", methods=["POST"])
def complete_project():
    """
    完成项目API
    请求体:
    {
        "project_id": 项目ID
    }
    """
    data = request.get_json()
    project_id = data.get("project_id")

    if not project_id:
        return jsonify({"error": "缺少必需的 project_id 参数"}), 400

    try:
        ProjectDeliverableService.check_and_complete_project(project_id)
        return jsonify({"message": "项目已成功标记为完成"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"完成项目失败: {str(e)}"}), 500


@project_bp.route("/deliverables/confirm", methods=["POST"])
def confirm_deliverable():
    """
    确认交付物API
    请求体:
    {
        "deliverable_id": 交付物ID,
        "user_id": 确认者用户ID
    }
    """
    data = request.get_json()
    deliverable_id = data.get("deliverable_id")
    user_id = data.get("user_id")

    if not all([deliverable_id, user_id]):
        return jsonify({"error": "缺少必需的参数"}), 400

    try:
        confirmation = DeliverableConfirmationService.confirm_deliverable(
            deliverable_id, user_id
        )
        return (
            jsonify({"message": "交付物确认成功", "data": confirmation.to_dict()}),
            200,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"确认交付物失败: {str(e)}"}), 500


@project_bp.route("/deliverables/confirm-status", methods=["GET"])
def get_deliverable_confirm_status():
    """
    获取交付物确认状态API
    查询参数:
    - deliverable_id: 交付物ID (必需)
    - user_id: 用户ID (必需)
    """
    deliverable_id = request.args.get("deliverable_id")
    user_id = request.args.get("user_id")

    if not all([deliverable_id, user_id]):
        return jsonify({"error": "缺少必需的参数"}), 400

    try:
        status = DeliverableConfirmationService.get_deliverable_confirm_status(
            deliverable_id, user_id
        )
        return jsonify({"data": status}), 200
    except Exception as e:
        return jsonify({"error": f"获取交付物确认状态失败: {str(e)}"}), 500


@project_bp.route("/projects/confirm-status", methods=["GET"])
def get_project_confirm_status():
    """
    获取项目整体确认状态API
    查询参数:
    - project_id: 项目ID (必需)
    - user_id: 用户ID (必需)
    """
    project_id = request.args.get("project_id")
    user_id = request.args.get("user_id")

    if not all([project_id, user_id]):
        return jsonify({"error": "缺少必需的参数"}), 400

    try:
        status = DeliverableConfirmationService.get_project_confirm_status(
            project_id, user_id
        )
        return jsonify({"data": status}), 200
    except Exception as e:
        return jsonify({"error": f"获取项目确认状态失败: {str(e)}"}), 500


@project_bp.route("/projects/complete-by-confirmation", methods=["POST"])
def complete_project_by_confirmation():
    """
    通过交付物确认完成项目API
    请求体:
    {
        "project_id": 项目ID
    }
    """
    data = request.get_json()
    project_id = data.get("project_id")

    if not project_id:
        return jsonify({"error": "缺少必需的 project_id 参数"}), 400

    try:
        DeliverableConfirmationService.check_and_complete_project_by_confirmation(
            project_id
        )
        return jsonify({"message": "项目已成功标记为完成 (通过确认)"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"完成项目失败: {str(e)}"}), 500


@project_bp.route("/projects/my-all", methods=["GET"])
def get_my_all_projects():
    """
    获取我创建的和参与的所有项目API，按创建时间倒序排序

    请求参数 (URL查询参数):
    - user_id: 用户ID (必需)
    """
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "缺少必需的 user_id 参数"}), 400

    try:
        # 获取我创建的项目
        founder_filters = {"user_id": user_id}
        founder_projects = ProjectService.get_founder_project_list(founder_filters)

        # 获取我参与的项目
        participant_filters = {"user_id": user_id}
        participant_projects = ProjectService.get_participant_project_list(
            participant_filters
        )

        # 合并项目列表并按创建时间倒序排序
        all_projects = founder_projects + participant_projects
        all_projects.sort(key=lambda x: x["created_at"], reverse=True)

        # 格式化返回数据
        formatted_projects = []
        for project in all_projects:
            # 获取项目贡献记录
            contribution = ProjectContribution.query.filter_by(
                project_id=project["id"], user_id=user_id
            ).first()

            # 获取技能类型
            skill_type = None
            if project["skill_requirements"]:
                # 获取第一个技能需求的技能类型名称
                skill_type = project["skill_requirements"][0]["skill_type_name"]

            formatted_project = {
                "name": project["name"],
                "created_by": {
                    "user_id": project["creator_info"]["user_id"],
                    "full_name": project["creator_info"]["full_name"],
                    "picture": project["creator_info"]["picture"],
                },
                "period": {
                    "start": project["created_at"],
                    "end": project["end_time"] if project["end_time"] else "Current",
                },
                "contribute_for": skill_type
                or "UI/UX Design",  # 如果没有技能需求，默认显示 UI/UX Design
                "stars": {
                    "earned": project["status"] == 2,  # 如果项目完成，显示已获得星级
                    "count": (
                        contribution.stars_earned
                        if contribution and contribution.stars_earned
                        else 0
                    ),
                },
                "project_id": project["id"],
                "status": project["status"],
            }
            formatted_projects.append(formatted_project)

        return (
            jsonify({"data": formatted_projects, "total": len(formatted_projects)}),
            200,
        )
    except Exception as e:
        return jsonify({"error": f"获取项目列表失败: {str(e)}"}), 500
