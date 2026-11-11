from sqlalchemy import (
    create_engine,
    select
)

from sqlalchemy.orm import Session

from app.database import Base
from app.models import (
    Agent,
    User
)


def test_user_can_have_agents():

    test_engine = create_engine(
        "sqlite:///:memory:"
    )

    Base.metadata.create_all(
        test_engine
    )

    with Session(test_engine) as session:

        user = User(
            email="owner@example.com",
            name="Agent Owner"
        )

        agent = Agent(
            name="Customer Support",
            description="客服 Agent",
            system_prompt="你是一个专业的客服助手。",
            owner=user
        )

        session.add(user)
        session.add(agent)

        session.commit()

        saved_agent = session.scalar(
            select(Agent).where(
                Agent.name== "Customer Support"
            )
        )

        assert saved_agent is not None

        assert saved_agent.owner.id == user.id

        assert saved_agent.owner.email == "owner@example.com"


        assert len(user.agents) == 1

        assert user.agents[0].name == "Customer Support"
