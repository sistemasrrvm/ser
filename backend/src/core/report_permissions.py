"""
Permissões de relatório por perfil e status (#275 / #246).
"""

from ..models.user import User
from ..models.report import Report

SUPORTE_ROLE_NAMES = frozenset({'suporte', 'suporte ao cliente', 'revisor'})
TECNICO_ROLE_NAMES = frozenset({'tecnico', 'usuario'})
ADMIN_ROLE_NAMES = frozenset({'admin', 'administrador'})


def _role_name(user: User) -> str:
    if not user.role:
        return ''
    return user.role.name.strip().lower()


def _role_level(user: User) -> int:
    return getattr(user.role, 'level', 0) if user.role else 0


def is_administrador(user: User) -> bool:
    name = _role_name(user)
    return _role_level(user) >= 100 or name in ADMIN_ROLE_NAMES


def is_suporte_puro(user: User) -> bool:
    if is_administrador(user):
        return False
    name = _role_name(user)
    level = _role_level(user)
    return name in SUPORTE_ROLE_NAMES or (50 <= level < 100)


def is_tecnico_puro(user: User) -> bool:
    if is_administrador(user) or is_suporte_puro(user):
        return False
    name = _role_name(user)
    level = _role_level(user)
    return name in TECNICO_ROLE_NAMES or (20 <= level < 50)


def _is_owner(user: User, report: Report) -> bool:
    return report.tecnico_id == user.id


def can_view_report(user: User, report: Report) -> bool:
    if is_administrador(user):
        return True
    if is_suporte_puro(user):
        return report.status != 'rascunho'
    if is_tecnico_puro(user):
        return _is_owner(user, report)
    return False


def can_edit_report(user: User, report: Report) -> bool:
    if is_suporte_puro(user):
        return report.status == 'em_revisao'
    if is_tecnico_puro(user):
        return _is_owner(user, report) and report.status in ('rascunho', 'em_correcao')
    return False


def can_delete_report(user: User, report: Report) -> bool:
    return (
        is_tecnico_puro(user)
        and _is_owner(user, report)
        and report.status == 'rascunho'
    )


def can_finalize_report(user: User, report: Report) -> bool:
    return (
        is_tecnico_puro(user)
        and _is_owner(user, report)
        and report.status in ('rascunho', 'em_correcao')
    )


def can_export_excel(user: User, report: Report) -> bool:
    if is_suporte_puro(user):
        return report.status in ('em_revisao', 'aprovado')
    return False


def can_approve_report(user: User, report: Report) -> bool:
    return is_suporte_puro(user) and report.status == 'em_revisao'


def can_request_correction(user: User, report: Report) -> bool:
    """Solicitar Correção: em_revisao → em_correcao (#246)."""
    return is_suporte_puro(user) and report.status == 'em_revisao'


def can_update_report_status(user: User, report: Report, new_status: str) -> bool:
    if is_tecnico_puro(user):
        return (
            _is_owner(user, report)
            and report.status in ('rascunho', 'em_correcao')
            and new_status == 'em_revisao'
        )
    if is_suporte_puro(user):
        return report.status == 'em_revisao' and new_status == 'aprovado'
    return False


def list_reports_exclude_rascunho_for_suporte(user: User) -> bool:
    return is_suporte_puro(user)


def list_reports_owner_only(user: User) -> bool:
    return is_tecnico_puro(user)
