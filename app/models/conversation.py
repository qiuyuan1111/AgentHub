# 开启前向注解延迟解析，支持字符串形式的类型注解，解决循环导入问题
from __future__ import annotations

# 标准库时间类型
from datetime import datetime
# TYPE_CHECKING 仅在类型检查阶段为True，运行时恒为False，用来隔离循环导入
from typing import TYPE_CHECKING

# SQLAlchemy 核心约束、列类型、数据库函数
from sqlalchemy import (
    DateTime,        # 时间类型，支持时区
    ForeignKey,      # 外键约束
    String,          # 定长字符串类型
    UniqueConstraint,# 联合唯一约束
    func             # 数据库函数，func.now() 对应 SQL NOW()
)

# ORM映射组件
from sqlalchemy.orm import (
    Mapped,          # SQLAlchemy2.0 类型注解包装器
    mapped_column,   # 声明数据库列
    relationship     # ORM对象关联（仅Python层，不生成数据库字段）
)

# 导入全局Base，所有数据表模型继承它
from app.database import Base


# 仅类型检查时导入Agent，运行时不会执行该import，规避循环导入
if TYPE_CHECKING:
    from app.models.agent import Agent


class Conversation(Base):
    """对话会话模型，对应数据库 conversations 表
    一条Conversation代表Agent下的一次对话会话
    一对多关系：Agent(一) → Conversation(多)
    """
    __tablename__ = "conversations"  # 数据库真实表名

    # 表级别的约束定义
    __table_args__ = (
        # 联合唯一约束：同一个agent下，不能出现重复的session_id
        # 也就是：agent_id + session_id 组合全局唯一
        UniqueConstraint(
            "agent_id",
            "session_id",
            name="uq_conversations_agent_session"  # 数据库约束名称，方便排错
        ),
    )

    # 主键自增ID
    id: Mapped[int] = mapped_column(
        primary_key=True,   # 标记为主键
        autoincrement=True  # 自增，PG对应serial序列
    )

    # 关联Agent的外键ID，多方（conversation）存放外键
    agent_id: Mapped[int] = mapped_column(
        ForeignKey(
            "agents.id",        # 关联agents表的id主键
            ondelete="CASCADE"  # 级联删除：Agent被删除，它下面所有对话一起删除
        ),
        nullable=False,         # 对话必须归属某个Agent，不能为空
        index=True              # 给agent_id建索引，按agent查对话提速
    )

    # 前端/业务侧的会话标识，由业务生成（uuid之类）
    session_id: Mapped[str] = mapped_column(
        String(128),
        nullable=False
    )

    # 对话标题，可以为空，AI自动生成或者用户自定义
    title: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True
    )

    # 创建时间：数据库层面默认值，插入时自动填充
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  # timestamptz 带时区时间
        server_default=func.now(),# 数据库DEFAULT NOW()
        nullable=False
    )

    # 更新时间：新增有初始值；ORM修改对象时自动刷新时间
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),      # ORM层钩子，原生SQL修改不会自动刷新
        nullable=False
    )

    # ORM双向关联：当前对话所属的Agent对象
    # back_populates="conversations" 去Agent模型找名字叫conversations的relationship配对
    agent: Mapped["Agent"] = relationship(
        back_populates="conversations"
    )
