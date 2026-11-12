# 延迟解析所有类型注解，支持字符串形式的前向引用，解决模型双向关联的循环导入难题。
from __future__ import annotations

# 标准库时间类型
from datetime import datetime
# TYPE_CHECKING 是编译期标记，仅给类型检查器（mypy、IDE）使用，运行时值永远是 False
from typing import TYPE_CHECKING

# SQLAlchemy 列类型、约束、数据库函数
from sqlalchemy import (
    DateTime,
    ForeignKey,   # 外键约束
    String,
    Text,
    func          # 数据库内置函数，func.now() 代表数据库now()
)

# ORM映射装饰器、关系定义
from sqlalchemy.orm import (
    Mapped,          # 2.0 类型注解包装器
    mapped_column,   # 声明字段
    relationship     # ORM对象关联（不是数据库字段！仅Python层关联）
)

# 导入全局Base，所有数据表模型都继承它
from app.database import Base


# 仅类型检查阶段导入User，运行时不会导入，避免循环导入问题
if TYPE_CHECKING:
    from app.models.user import User
    from app.models.conversation import Conversation


class Agent(Base):
    """Agent智能体模型，对应数据库 agents 表"""

    # 指定数据库真实表名
    __tablename__ = "agents"

    # 主键ID
    id: Mapped[int] = mapped_column(
        primary_key=True,   # 标记为主键
        autoincrement=True  # 自增（PG对应serial/bigserial，mysql auto_increment）
    )

    # 归属用户ID，外键关联users表id
    owner_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",        # 关联目标表.列
            ondelete="CASCADE" # 级联删除：user被删除时，所属agent一起删掉
        ),
        nullable=False,         # 不允许为空，agent必须有归属用户
        index=True              # 自动建立索引，根据owner_id查询会更快
    )

    # Agent名称
    name: Mapped[str] = mapped_column(
        String(100),  # 字符串类型，最大长度100
        nullable=False
    )

    # Agent描述，允许为空
    description: Mapped[str | None] = mapped_column(
        String(500),  # 最长500字符
        nullable=True # 允许NULL
    )

    # 系统提示词，长文本，不限制长度
    system_prompt: Mapped[str] = mapped_column(
        Text,         # 长文本类型，适合存prompt
        nullable=False
    )

    # 创建时间：仅新增时数据库自动填充，不会随更新变化
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), # 带时区时间 timestamptz
        server_default=func.now(),# 数据库层面默认值，插入时自动填now()
        nullable=False
    )

    # 更新时间：插入给初始值；ORM修改对象时自动刷新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(), # ORM层钩子，⚠️原生SQL修改不会自动更新
        nullable=False
    )

    # ORM关联：owner 是User对象，不是数据库字段
    # back_populates="agents" 和 User模型里的 agents 双向关联配对
    owner: Mapped["User"] = relationship(
        back_populates="agents"
    )

    conversations: Mapped[
        list["Conversation"]
    ] = relationship(back_populates="agent")
