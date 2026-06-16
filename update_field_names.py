#!/usr/bin/env python3
"""
Script para atualizar referências a campos FormPage e FormField para português
"""

import os
import re

# Mapeamento de substituições
FIELD_MAPPINGS = [
    # FormField - ao acessar propriedades de objetos (não em FormFieldCreate)
    (r'(\bfield|separator|f)\.(label)\b', r'\1.rotulo'),
    (r'(\bfield|separator|f)\.(type)\b', r'\1.tipo'),
    (r'(\bfield|separator|f)\.(config)\b', r'\1.configuracao'),

    # FormPage - ao acessar propriedades de objetos (não em FormPageCreate)
    (r'(\bpage|p)\.(label)\b', r'\1.nome'),
    (r'(\bpage|p)\.(show_when_rule_id)\b', r'\1.regra_exibicao_id'),
]

# FormFieldCreate e FormPageCreate - propriedades internas
CREATE_MAPPINGS = [
    (r'\blabel:', r'rotulo:'),
    (r'\btype:', r'tipo:'),
    (r'\bconfig:', r'configuracao:'),
    (r'\bshow_when_rule_id:', r'regra_exibicao_id:'),
]

# Arquivos a serem atualizados
FILES_TO_UPDATE = [
    'D:/REPOSITORIO_GIT/laudonr13/frontend/src/app/components/FormPage/FormSeparatorModal.tsx',
    'D:/REPOSITORIO_GIT/laudonr13/frontend/src/app/components/FormPage/FormFieldList.tsx',
    'D:/REPOSITORIO_GIT/laudonr13/frontend/src/app/components/FormPage/FormFieldModal.tsx',
    'D:/REPOSITORIO_GIT/laudonr13/frontend/src/app/components/FormTemplate/FormPageList.tsx',
    'D:/REPOSITORIO_GIT/laudonr13/frontend/src/app/components/FormTemplate/FormPageModal.tsx',
    'D:/REPOSITORIO_GIT/laudonr13/frontend/src/app/components/FormPage/FormPageInfo.tsx',
    'D:/REPOSITORIO_GIT/laudonr13/frontend/src/app/routes/FormPageEditPage.tsx',
    'D:/REPOSITORIO_GIT/laudonr13/frontend/src/app/components/FormTemplate/SortablePageItem.tsx',
    'D:/REPOSITORIO_GIT/laudonr13/frontend/src/app/routes/ReportWizardPage.tsx',
]

def update_file(filepath):
    """Atualiza um arquivo com as substituições"""
    print(f"Atualizando: {filepath}")

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Aplicar substituições de propriedades de objetos
    for pattern, replacement in FIELD_MAPPINGS:
        content = re.sub(pattern, replacement, content)

    # Aplicar substituições em objetos de criação
    for pattern, replacement in CREATE_MAPPINGS:
        content = re.sub(pattern, replacement, content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] Atualizado com sucesso")
        return True
    else:
        print(f"  [--] Nenhuma alteracao necessaria")
        return False

def main():
    """Função principal"""
    print("=" * 60)
    print("ATUALIZAÇÃO DE NOMES DE CAMPOS PARA PORTUGUÊS")
    print("=" * 60)
    print()

    updated_count = 0
    for filepath in FILES_TO_UPDATE:
        if os.path.exists(filepath):
            if update_file(filepath):
                updated_count += 1
        else:
            print(f"AVISO: Arquivo não encontrado: {filepath}")

    print()
    print("=" * 60)
    print(f"Resumo: {updated_count} arquivo(s) atualizado(s)")
    print("=" * 60)

if __name__ == '__main__':
    main()
