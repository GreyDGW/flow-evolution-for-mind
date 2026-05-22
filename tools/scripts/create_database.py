from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, Boolean, Index, BigInteger
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Session(Base):
    __tablename__ = 'sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, index=True)
    type = Column(String(32))
    msg_id = Column(String(64), unique=True)
    parent_id = Column(String(64), index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    hostname = Column(String(128))
    agent_id = Column(String(64), index=True)

    sender_id = Column(String(64), index=True)
    sender_name = Column(String(128))

    role = Column(String(16), index=True)
    model = Column(String(64))
    api = Column(String(32))
    provider = Column(String(32))

    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
    total_tokens = Column(Integer)
    total_cost = Column(Float)

    stop_reason = Column(String(32))

    tool_name = Column(String(64))
    tool_input = Column(Text)
    tool_use_id = Column(String(64))

    is_error = Column(Integer, default=0)
    is_question = Column(Integer, default=0)
    has_code = Column(Integer, default=0)

    content_text = Column(Text)
    thinking_text = Column(Text)
    tool_call_text = Column(Text)
    content_length = Column(Integer)

    media_path = Column(String(512))
    media_type = Column(String(64))

    custom_type = Column(String(64))
    custom_data = Column(Text)

    complete_raw = Column(Text)

    __table_args__ = (
        Index('idx_session_timestamp', 'session_id', 'timestamp'),
        Index('idx_role_timestamp', 'role', 'timestamp'),
    )

class Goal(Base):
    __tablename__ = 'goals'
    id = Column(Integer, primary_key=True, autoincrement=True)
    declared_text = Column(Text)
    declared_at = Column(DateTime)
    status = Column(String(16))
    drift_score = Column(Float)
    last_mentioned = Column(DateTime)
    closed_at = Column(DateTime)
    closure_evidence = Column(Text)
    complexity_score = Column(Float)

class Closure(Base):
    __tablename__ = 'closures'
    id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id = Column(Integer)
    task_name = Column(String(256))
    plan_evidence = Column(Text)
    do_evidence = Column(Text)
    check_evidence = Column(Text)
    adjust_evidence = Column(Text)
    topology = Column(String(64))
    complexity_score = Column(Float)
    value_score = Column(Float)
    time_invested_ratio = Column(Float)
    started_at = Column(DateTime)
    closed_at = Column(DateTime)

class FlowFragment(Base):
    __tablename__ = 'flow_fragments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), index=True)
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    duration_min = Column(Float)
    rounds_count = Column(Integer)
    interruptions = Column(Integer)
    recovery_rounds = Column(Integer)
    intensity = Column(Float)
    semantic_coherence = Column(Float)
    flow_index = Column(Float)

class Concept(Base):
    __tablename__ = 'concepts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(256), unique=True)
    first_seen = Column(DateTime)
    last_seen = Column(DateTime)
    mention_count = Column(Integer, default=1)
    mastery_stage = Column(String(32))
    source_session = Column(String(64))

class ConceptRelation(Base):
    __tablename__ = 'concept_relations'
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_concept = Column(Integer)
    to_concept = Column(Integer)
    relation_type = Column(String(64))
    first_seen = Column(DateTime)
    weight = Column(Float)

class CollectState(Base):
    __tablename__ = 'collect_state'
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_path = Column(String(512), unique=True)
    last_line_offset = Column(Integer, default=0)
    last_modified = Column(BigInteger)
    updated_at = Column(DateTime)

def create_database(db_path="flow_ecosystem.db"):
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    return engine

if __name__ == "__main__":
    engine = create_database()
    print("✅ 数据库创建成功！")
    print(f"📊 创建的表: {list(Base.metadata.tables.keys())}")