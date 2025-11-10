import os

from datetime import datetime
from sqlalchemy import create_engine, delete, select, func, MetaData
from sqlalchemy.exc import DataError
from dotenv import load_dotenv

def convert_to_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None

def save_to_db(cases_dict: dict, documents_dict: dict):
    """
    Функция принимает словари с делами и связанными документами и 
    записывает их в уже созданную базу данных
    """
    
    load_dotenv()
    DATABASE_URL = os.environ.get('DATABASE_URL')# .env файл в формате postgresql://user:pass@localhost/mydb
    
    engine = create_engine(DATABASE_URL, echo=True)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    cases = metadata.tables['cases']
    participants = metadata.tables['participants'] 
    case_participant = metadata.tables['case_participant']
    documents = metadata.tables['documents']
    
    cases_data = cases_dict['cases']
    documents_data = documents_dict['documents']
    
    with engine.begin() as conn:
        # Записываем дело
        for case in cases_data:
            existing_case = conn.execute(
                cases.select().where(cases.c.text_id == case['case_id'])
            ).first()
            
            if existing_case:
                case_id = existing_case.id
            else:
                try:
                    result = conn.execute(
                        cases.insert().values(
                            text_id=case['case_id'],
                            raw_id=case['raw_id'],
                            title=case['case_name'],
                            open_date=convert_to_date(case['case_date']),
                            closing_date=convert_to_date(case['closing_date']),
                            url=case['case_url'],
                            procedure_type=case['procedure_type'],
                            department=case['department'],
                            activity_sphere=case['activity_sphere'],
                            review_stage=case['review_stage'],
                            registration_date=convert_to_date(case['registration_date']),
                            initiation_date=convert_to_date(case['initiation_date'])
                        ).returning(cases.c.id)
                    )
                    case_id = result.scalar()
                
                    # Записываем участников
                    for participant in case['participants']:
                        if not participant.get('inn'):
                            continue
                        
                        existing_participant = conn.execute(
                            participants.select().where(participants.c.inn == participant['inn'])
                        ).first()
                        
                        if existing_participant:
                            participant_id = existing_participant.id
                        else:
                            result = conn.execute(
                                participants.insert().values(
                                    raw_name=participant['raw_name'],
                                    norm_name=participant['norm_name'],
                                    org_form=participant['org_form'],
                                    inn=participant['inn'],
                                    ogrn=participant['ogrn']
                                ).returning(participants.c.id)
                            )
                            participant_id = result.scalar()
                            
                            existing_link = conn.execute(
                            case_participant.select().where(
                                (case_participant.c.case_id == case_id) &
                                (case_participant.c.participant_id == participant_id)
                            )
                        ).first()
                            
                        # Записываем данные в связующую таблицу
                        if not existing_link:
                            conn.execute(case_participant.insert().values(
                                case_id=case_id,
                                participant_id=participant_id, 
                                participant_role=participant['role']
                            ))
                except DataError:
                    print(f'DataError - {case}')

        # Записываем связанные дела
        for doc in documents_data:
            existing_document = conn.execute(
                documents.select().where(documents.c.doc_id == doc['document_id'])  # ← participants.select()
            ).first()
            
            if not existing_document:
                case_result = conn.execute(
                    cases.select().where(cases.c.text_id == doc['case_id'])
                ).first()
        
                if case_result:
                    result = conn.execute(
                        documents.insert().values(
                            case_id=case_result.id,
                            doc_id=doc['document_id'],
                            raw_doc_id=doc['raw_doc_id'],
                            title=doc['title'],
                            publish_date=convert_to_date(doc['document_date']),
                            url=doc['url'],
                            full_text=doc['document_text'],
                            text_length=doc['text_length'],
                            doc_type=doc['document_type']
                        ).returning(documents.c.id)
                    )

def clear_all_tables():
    load_dotenv()
    DATABASE_URL = os.environ.get('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    
    with engine.begin() as conn:
        # Важен порядок из-за foreign keys!
        conn.execute(delete(metadata.tables['case_participant']))
        conn.execute(delete(metadata.tables['documents']))
        conn.execute(delete(metadata.tables['participants']))
        conn.execute(delete(metadata.tables['cases']))

def count_cases():
    load_dotenv()
    DATABASE_URL = os.environ.get('DATABASE_URL')
    engine = create_engine(DATABASE_URL)
    
    metadata = MetaData()
    metadata.reflect(bind=engine)
    cases = metadata.tables['cases']
    
    with engine.connect() as conn:
        result = conn.execute(select(func.count()).select_from(cases))
        count = result.scalar()
        
        return count