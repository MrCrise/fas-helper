from sqlalchemy import Column, Integer, String, Date, Text, ForeignKey, Boolean, DateTime, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Participant(Base):
    __tablename__ = 'participants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    raw_name = Column(Text)
    norm_name = Column(Text)
    org_form = Column(Text)
    inn = Column(Text)
    ogrn = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class Case(Base):
    __tablename__ = 'cases'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text_id = Column(Text)
    raw_id = Column(Text)
    title = Column(Text, nullable=False)
    open_date = Column(Date)
    closing_date = Column(Date)
    url = Column(Text)
    procedure_type = Column(Text)
    department = Column(Text)
    activity_sphere = Column(Text)
    review_stage = Column(Text)
    registration_date = Column(Date)
    initiation_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())


class CaseParticipant(Base):
    __tablename__ = 'case_participant'

    case_id = Column(Integer, ForeignKey(
        'cases.id', ondelete='CASCADE'), primary_key=True)
    participant_id = Column(Integer, ForeignKey(
        'participants.id', ondelete='CASCADE'), primary_key=True)
    participant_role = Column(Text)
    created_at = Column(DateTime, server_default=func.now())


class Document(Base):
    __tablename__ = 'documents'

    id = Column(Integer, primary_key=True, autoincrement=True)
    case_id = Column(Text, nullable=False)
    doc_id = Column(Text, nullable=False)
    raw_doc_id = Column(Text)
    title = Column(Text)
    publish_date = Column(Date)
    url = Column(Text)
    full_text = Column(Text)
    text_length = Column(Integer, default=0)
    doc_type = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    added_to_qdrant = Column(Boolean, default=False)
    embedder_version = Column(String(40))
