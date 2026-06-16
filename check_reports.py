import sys
import os

# Adicionar diretório src ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

from sqlmodel import Session, create_engine, select
from src.models.report import Report
from src.core.config import settings

engine = create_engine(settings.DATABASE_URL)
session = Session(engine)

reports = session.exec(select(Report)).all()

print(f'\n📊 Total de relatórios: {len(reports)}\n')

if reports:
    for r in reports:
        print(f'ID: {r.id}')
        print(f'Número: {r.numero}')
        print(f'Status: {r.status}')
        print(f'Cliente ID: {r.cliente_id}')
        print(f'Template ID: {r.form_template_id}')
        print(f'Técnico ID: {r.tecnico_id}')
        print('-' * 50)
else:
    print('❌ Nenhum relatório encontrado no banco de dados!')

session.close()
