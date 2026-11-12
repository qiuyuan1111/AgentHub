from sqlalchemy import (
    create_engine,
    select
)

from sqlalchemy.orm import Session

from app.database import Base
from app.models import (
    Agent,
    Conversation,
    User
)


def test_agent_can_have_conversations():

    test_engine = create_engine(
        "sqlite:///:memory:"
    )

    Base.metadata.create_all(
        test_engine
    )

    with Session(test_engine) as session:

        user = User(
            email="owner@example.com",
            name="Owner"
        )

        agent = Agent(
            name="Customer Support",
            description="客服 Agent",
            system_prompt="你是一个客服助手。",
            owner=user
        )

        conversation = Conversation(
            session_id="session-001",
            title="退款咨询",
            agent=agent
        )

        session.add(user)
        session.add(agent)
        session.add(conversation)

        session.commit()

        saved_conversation = session.scalar(
            select(Conversation).where(
                Conversation.session_id == "session-001"
            )
        )

        assert saved_conversation is not None

        assert saved_conversation.agent.id == agent.id

        assert saved_conversation.agent.name == "Customer Support"

        assert len(agent.conversations) == 1


        assert agent.conversations[0].session_id == "session-001"
