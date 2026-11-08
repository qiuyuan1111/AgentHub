# 从 sqlalchemy 核心导入
# create_engine：创建数据库引擎，负责连接数据库
# select：2.0 风格查询构造器，用来拼装 SELECT SQL
from sqlalchemy import (
    create_engine,
    select
)

# Session：数据库会话，所有增删改查都通过 Session 完成
from sqlalchemy.orm import Session

# Base：ORM基类，所有模型都继承它，metadata存表结构信息
from app.database import Base
# User：我们写好的用户ORM模型
from app.models import User


# 测试函数：验证 User 可以正常存入数据库，并且可以查询出来
def test_user_can_be_saved_and_loaded():

    # 创建一个内存 SQLite 引擎
    # sqlite:///:memory: 代表内存数据库：数据全部放在内存，程序结束数据直接消失，不会生成文件
    # 非常适合单元测试，速度快、不用清理脏数据
    test_engine = create_engine(
        "sqlite:///:memory:"
    )

    # 在这个测试引擎上，创建所有继承 Base 的数据表（users表）
    Base.metadata.create_all(
        test_engine
    )

    # with Session(test_engine) as session:
    # with上下文管理器：代码块结束自动关闭会话，不用手动 session.close()
    with Session(test_engine) as session:

        # 在内存构造User对象，只给email、name
        user = User(
            email="test@example.com",
            name="Test User"
        )

        # add：把对象加入会话待提交队列，此时还没发给数据库
        session.add(user)
        # commit：提交事务，执行INSERT，写入内存数据库
        session.commit()

        # 拼装查询语句：SELECT * FROM users WHERE email = 'test@example.com'
        # scalar：预期查询单条记录，查到返回User对象，查不到返回None
        saved_user = session.scalar(
            select(User).where(
                User.email
                == "test@example.com"
            )
        )

        # 下面四条 assert 断言：测试用的校验，不满足条件直接抛 AssertionError，测试失败
        assert saved_user is not None          # 断言：一定查到了用户，不能是None
        assert saved_user.email == "test@example.com" # 断言：邮箱和存入的一致
        assert saved_user.name == "Test User"         # 断言：姓名和存入的一致
        assert saved_user.id is not None              # 断言：自增id成功生成，不为空
