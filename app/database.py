from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker
)

from app.config import DATABASE_URL


# =========================
# 1. Engine：数据库连接引擎（全局单例）
# =========================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True   # ✅ 重点：连接池心跳检测
)


# =========================
# 2. Session Factory：会话工厂，用来造 Session
# =========================
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False
)
# expire_on_commit=False 是 FastAPI 里高频配置，后面单独讲


# =========================
# 3. ORM Base：所有数据表模型的父类
# =========================
class Base(DeclarativeBase):
    pass
# 你后续写的 Model 都继承这个 Base
# 例：class Document(Base): ...
# Base.metadata.create_all(engine) 就是建表


# =========================
# 4. FastAPI 依赖函数 get_db
# =========================
def get_db() -> Generator[Session, None, None]:
    # 从工厂拿到一个数据库会话
    db = SessionLocal()
    try:
        # 把会话交给路由函数使用（yield 是生成器依赖的核心）
        yield db
    finally:
        # 路由执行完毕、无论是否抛异常，一定会执行 close()
        db.close()

# 函数作用：创建所有数据表
def create_tables() -> None:
    # 导入 app.models 包
    # 重点：不是为了使用里面的变量，而是【触发模型类加载】
    # 只有 import 之后，User 这类继承 Base 的模型才会被注册到 Base.metadata 里面
    # 如果不 import，Base.metadata 是空的，执行 create_all 什么表都不会生成
    import app.models

    # Base.metadata：元数据容器，收集了所有继承Base的表结构信息
    # create_all：SQLAlchemy提供的建表方法
    # 特性：只会创建【数据库里不存在】的表；已经存在的表不会覆盖、不会更新、不会删除数据
    # bind=engine：指定用 engine（数据库连接引擎）去执行建表SQL
    Base.metadata.create_all(
        bind=engine
    )
