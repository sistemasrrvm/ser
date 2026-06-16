"""
Schemas module
"""

from .auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
    PasswordResetRequest,
    PasswordResetResponse,
    PasswordResetConfirm,
    PasswordChangeRequest
)
from .user import (
    RoleResponse,
    RoleListResponse,
    UserResponse,
    UserCreate,
    UserUpdate,
    UserListResponse
)
from .formulario import (
    FormularioCreate,
    FormularioUpdate,
    FormularioResponse,
    FormularioListResponse
)
from .form_page import (
    FormPageCreate,
    FormPageUpdate,
    FormPageResponse,
    FormPageListResponse
)
from .form_field import (
    FormFieldCreate,
    FormFieldUpdate,
    FormFieldResponse,
    FormFieldListResponse
)
from .report import (
    ClienteResponse,
    EquipamentoResponse,
    TecnicoResponse,
    FormTemplateResponse,
    ReportCreate,
    ReportUpdate,
    ReportStatusUpdate,
    SolicitarCorrecaoRequest,
    ReportCorrecaoResponse,
    ReportCorrecaoListResponse,
    ReportResponse,
    ReportListItem,
    ReportListResponse
)
from .lookup_list import (
    LookupListCreate,
    LookupListUpdate,
    LookupListUpdateOptions,
    LookupListResponse,
    LookupListListResponse,
    LookupListOptionsResponse
)
from .manut import (
    ManutClienteResponse,
    ManutClienteListResponse,
    ManutTipoEquipamentoResponse,
    ManutTipoEquipamentoListResponse,
    ManutEquipamentoResponse,
    ManutEquipamentoListResponse,
    SyncStatusResponse
)
from .configuracao import (
    ConfiguracaoCreate,
    ConfiguracaoUpdate,
    ConfiguracaoResponse,
    ConfiguracaoListResponse
)

__all__ = [
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",
    "PasswordResetRequest",
    "PasswordResetResponse",
    "PasswordResetConfirm",
    "PasswordChangeRequest",
    "RoleResponse",
    "RoleListResponse",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "UserListResponse",
    "FormularioCreate",
    "FormularioUpdate",
    "FormularioResponse",
    "FormularioListResponse",
    "FormPageCreate",
    "FormPageUpdate",
    "FormPageResponse",
    "FormPageListResponse",
    "FormFieldCreate",
    "FormFieldUpdate",
    "FormFieldResponse",
    "FormFieldListResponse",
    "EquipamentoResponse",
    "TecnicoResponse",
    "FormTemplateResponse",
    "ReportCreate",
    "ReportUpdate",
    "ReportStatusUpdate",
    "SolicitarCorrecaoRequest",
    "ReportCorrecaoResponse",
    "ReportCorrecaoListResponse",
    "ReportResponse",
    "ReportListItem",
    "ReportListResponse",
    "LookupListCreate",
    "LookupListUpdate",
    "LookupListUpdateOptions",
    "LookupListResponse",
    "LookupListListResponse",
    "LookupListOptionsResponse",
    "ManutClienteResponse",
    "ManutClienteListResponse",
    "ManutTipoEquipamentoResponse",
    "ManutTipoEquipamentoListResponse",
    "ManutEquipamentoResponse",
    "ManutEquipamentoListResponse",
    "SyncStatusResponse",
    "ConfiguracaoCreate",
    "ConfiguracaoUpdate",
    "ConfiguracaoResponse",
    "ConfiguracaoListResponse",
]
