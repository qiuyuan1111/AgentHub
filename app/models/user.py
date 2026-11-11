from __future__ import annotations
from typing import TYPE_CHECKING
# 导入标准库 datetime 模块里的两个对象
# datetime：用来构造、表示日期时间对象
# timezone：时区对象，这里使用 timezone.utc 代表UTC零时区
from datetime import (
    datetime,
    timezone
)

# 从 sqlalchemy 核心包导入数据库字段类型
# DateTime：数据库时间类型
# String：数据库字符串类型，对应 MySQL 的 VARCHAR
from sqlalchemy import (
    DateTime,
    String,
    func
)

# sqlalchemy.orm 是ORM相关模块，2.0新版声明式写法
# Mapped：类型标记，告诉SQLAlchemy和IDE这是一个ORM映射字段，同时提供类型提示
# mapped_column：用来定义数据表列，等价老版本 Column，是2.0推荐写法
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

if TYPE_CHECKING:
    from app.models.agent import Agent

# 从 app.database 导入 Base 基类
# Base 是声明式基类，继承 Base 的类都会被识别为一张数据库表模型
# 后续 Base.metadata.create_all(engine) 会扫描所有继承Base的模型自动建表
from app.database import Base


# User 类：ORM模型类，一张用户表
class User(Base):
    # __tablename__：ORM内置魔法属性，指定这个类映射到数据库里真实的表名
    # 规范：类名大驼峰 User，数据库表名小写复数 users
    __tablename__ = "users"

    # id 字段：用户主键ID
    # Mapped[int]：Python侧类型是int
    id: Mapped[int] = mapped_column(
        primary_key=True,   # primary_key=True：设置该列为主键，主键唯一标识一行数据
        autoincrement=True  # autoincrement=True：自增，插入数据不指定id时数据库自动递增生成
    )

    # email 字段：用户邮箱
    # Mapped[str]：Python侧类型是字符串
    email: Mapped[str] = mapped_column(
        String(255),        # 数据库字段类型 VARCHAR(255)，最长255字符
        unique=True,        # unique=True：唯一约束，整张表email不能重复，底层生成唯一索引
        index=True,         # index=True：建立普通索引，按email查询时加快查询速度
        nullable=False      # nullable=False：不允许为NULL，新增用户必须提供邮箱
    )

    # name 字段：用户姓名
    # Mapped[str]：Python侧类型字符串
    name: Mapped[str] = mapped_column(
        String(100),        # VARCHAR(100)，姓名最长100字符
        nullable=False      # 不允许为空，姓名必填
    )

    agents: Mapped[list["Agent"]] = relationship(
        back_populates="owner"
    )

    # created_at 字段：记录创建时间
    # Mapped[datetime]：Python侧类型是datetime时间对象
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),  # DateTime(timezone=True)：带时区标记的时间类型
        # default：ORM层默认值，插入数据不填created_at时自动填充
        # 必须用lambda包裹：每次新增记录才执行函数获取当前UTC时间
        # 如果直接写 datetime.now(timezone.utc)，只会在程序启动时计算一次固定时间
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False  # 不允许为NULL，由default自动兜底填充时间
    )


    # 记录记录最后一次更新的时间
    updated_at: Mapped[datetime] = mapped_column(
        # 数据库字段类型：带时区的时间类型
        DateTime(timezone=True),
        # server_default：数据库层面的默认值
        # 新增数据时，由数据库执行 now() 生成当前时间作为初始值
        # 该配置会反映在建表SQL中，alembic迁移可以识别
        server_default=func.now(),
        # onupdate：SQLAlchemy ORM层的更新钩子（⚠️不是数据库原生能力）
        # 当通过ORM执行update修改本条数据时，自动赋值为当前时间
        # ⚠️ 直接执行原生SQL、数据库工具修改数据时不会自动刷新
        onupdate=func.now(),
        nullable=False
    )

