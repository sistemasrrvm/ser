#!/usr/bin/env python3
"""
Script para atualizar roles e usuário admin
Atualiza os perfis do sistema para: Tecnico, Suporte, Administrador
Atualiza o usuário admin para usar o perfil Administrador
"""

import sys
import os
from pathlib import Path

# Adicionar o diretório backend/src ao path
backend_src_dir = Path(__file__).parent.parent / 'backend' / 'src'
sys.path.insert(0, str(backend_src_dir))

from sqlmodel import Session, select
from core.database import engine
from models import Role, User


def update_roles_and_admin():
    """
    Atualiza os roles do sistema e o usuário admin
    """
    print("=" * 60)
    print("Atualizando Roles e Usuário Admin")
    print("=" * 60)
    
    with Session(engine) as session:
        try:
            # 1. Criar/atualizar roles
            print("\n[1/3] Criando/atualizando roles...")
            
            roles_data = [
                {
                    'name': 'Tecnico',
                    'level': 20,
                    'description': 'Técnico - Dashboard e Relatórios'
                },
                {
                    'name': 'Suporte',
                    'level': 50,
                    'description': 'Suporte - Dashboard, Relatórios, Clientes, Equipamentos'
                },
                {
                    'name': 'Administrador',
                    'level': 100,
                    'description': 'Administrador - Acesso total ao sistema'
                }
            ]
            
            for role_data in roles_data:
                # Verificar se o role já existe
                statement = select(Role).where(Role.name == role_data['name'])
                role = session.exec(statement).first()
                
                if role:
                    # Atualizar role existente
                    role.level = role_data['level']
                    role.description = role_data['description']
                    print(f"  ✓ Atualizado: {role_data['name']} (nível {role_data['level']})")
                else:
                    # Criar novo role
                    role = Role(**role_data)
                    session.add(role)
                    print(f"  ✓ Criado: {role_data['name']} (nível {role_data['level']})")
            
            session.commit()
            print("  ✅ Roles criados/atualizados com sucesso!")
            
            # 2. Buscar o role Administrador
            print("\n[2/3] Buscando role Administrador...")
            statement = select(Role).where(Role.name == 'Administrador')
            admin_role = session.exec(statement).first()
            
            if not admin_role:
                raise Exception("Role 'Administrador' não encontrado após criação!")
            
            print(f"  ✓ Role Administrador encontrado (ID: {admin_role.id})")
            
            # 3. Atualizar usuário admin
            print("\n[3/3] Atualizando usuário admin...")
            statement = select(User).where(User.username == 'admin')
            admin_user = session.exec(statement).first()
            
            if not admin_user:
                raise Exception("Usuário 'admin' não encontrado!")
            
            if admin_user.role_id != admin_role.id:
                old_role_id = admin_user.role_id
                admin_user.role_id = admin_role.id
                session.add(admin_user)
                session.commit()
                print(f"  ✓ Usuário admin atualizado (role_id: {old_role_id} -> {admin_role.id})")
            else:
                print(f"  ✓ Usuário admin já estava com o role correto (role_id: {admin_role.id})")
            
            # 4. Verificar resultado
            print("\n" + "=" * 60)
            print("RESULTADO DA ATUALIZAÇÃO")
            print("=" * 60)
            
            # Recarregar usuário admin com role atualizado
            session.refresh(admin_user)
            
            # Buscar role do usuário admin
            admin_role_from_user = session.exec(
                select(Role).where(Role.id == admin_user.role_id)
            ).first()
            
            if admin_user and admin_role_from_user:
                print(f"\n👤 Usuário Admin:")
                print(f"   ID: {admin_user.id}")
                print(f"   Username: {admin_user.username}")
                print(f"   Nome: {admin_user.full_name}")
                print(f"   Email: {admin_user.email}")
                print(f"   Role ID: {admin_user.role_id}")
                print(f"   Role: {admin_role_from_user.name} (nível {admin_role_from_user.level})")
                print(f"   Descrição: {admin_role_from_user.description}")
                print(f"   Ativo: {'Sim' if admin_user.is_active else 'Não'}")
            
            # Mostrar todos os roles
            print(f"\n📋 Roles Disponíveis:")
            roles = session.exec(select(Role).order_by(Role.level.desc())).all()
            for role in roles:
                print(f"   - {role.name} (nível {role.level}): {role.description}")
            
            print("\n" + "=" * 60)
            print("✅ Atualização concluída com sucesso!")
            print("=" * 60)
            
            return True
            
        except Exception as e:
            session.rollback()
            print(f"\n❌ Erro durante a atualização: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = update_roles_and_admin()
    sys.exit(0 if success else 1)

