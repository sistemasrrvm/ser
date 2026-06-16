"""Envio de e-mails HTML no fluxo de relatórios (#248)."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Literal, Optional

import aiosmtplib
from sqlmodel import Session, select

from ..core.colored_logging import log_error, log_info
from ..core.report_permissions import SUPORTE_ROLE_NAMES
from ..models import ManutCliente, ManutEquipamento, Report, User
from ..models.role import Role
from .email_config import get_email_runtime_config, is_email_configured

logger = logging.getLogger("ser_app")

ReportEmailEvent = Literal["finalizar", "solicitar_correcao", "aprovar"]

STATUS_LABELS = {
    "rascunho": "Em Elaboração",
    "em_revisao": "Em Revisão",
    "em_correcao": "Em Correção",
    "aprovado": "Aprovado",
    "cancelado": "Cancelado",
}


@dataclass
class EmailSendLogger:
    """Registra passos do envio SMTP (servidor + resposta da API de teste)."""

    steps: list[str] = field(default_factory=list)

    def add(self, message: str) -> None:
        self.steps.append(message)
        log_info(f"[EMAIL] {message}")
        logger.info("[EMAIL] %s", message)

    def fail(self, message: str) -> None:
        self.steps.append(f"ERRO: {message}")
        log_error(f"[EMAIL] {message}")
        logger.error("[EMAIL] %s", message)


@dataclass
class EmailTestResult:
    success: bool
    message: str
    subject: str = ""
    destinatario: str = ""
    log: list[str] = field(default_factory=list)


@dataclass
class EmailContext:
    report_numero: str
    report_id: int
    status_label: str
    tipo_inspecao: str
    data_inspecao: str
    cliente_nome: str
    equipamento_tag: str
    equipamento_nome: str
    tecnico_nome: str
    actor_nome: str
    acao_titulo: str
    acao_mensagem: str
    cta_label: str
    report_url: str
    correcao_descricao: str = ""


def _normalize_email(email: Optional[str]) -> Optional[str]:
    if not email:
        return None
    value = email.strip().lower()
    return value if value and "@" in value else None


def get_suporte_recipient_emails(session: Session) -> list[str]:
    """Usuários Suporte/Revisor ativos com e-mail (level 50–99 ou nome conhecido)."""
    stmt = (
        select(User)
        .join(Role, User.role_id == Role.id)
        .where(User.is_active == True)  # noqa: E712
    )
    users = session.exec(stmt).all()
    emails: list[str] = []
    for user in users:
        if not user.role:
            continue
        name = user.role.name.strip().lower()
        level = user.role.level
        is_suporte = name in SUPORTE_ROLE_NAMES or (50 <= level < 100)
        if not is_suporte:
            continue
        addr = _normalize_email(user.email)
        if addr:
            emails.append(addr)
    return list(dict.fromkeys(emails))


def get_tecnico_recipient_email(session: Session, report: Report) -> Optional[str]:
    tecnico = session.get(User, report.tecnico_id)
    if not tecnico or not tecnico.is_active:
        return None
    return _normalize_email(tecnico.email)


def resolve_recipients(
    session: Session,
    event: ReportEmailEvent,
    report: Report,
    actor: User,
) -> list[str]:
    emails: list[str] = []
    if event == "finalizar":
        emails.extend(get_suporte_recipient_emails(session))
    elif event == "solicitar_correcao":
        addr = get_tecnico_recipient_email(session, report)
        if addr:
            emails.append(addr)
        actor_addr = _normalize_email(actor.email)
        if actor_addr and actor_addr not in emails:
            emails.append(actor_addr)
    elif event == "aprovar":
        addr = get_tecnico_recipient_email(session, report)
        if addr:
            emails.append(addr)
        for suporte in get_suporte_recipient_emails(session):
            if suporte not in emails:
                emails.append(suporte)
    return list(dict.fromkeys(emails))


def build_report_email_context(
    session: Session,
    report: Report,
    event: ReportEmailEvent,
    actor: User,
    *,
    correcao_descricao: str = "",
) -> EmailContext:
    cfg = get_email_runtime_config(session)
    cliente = session.get(ManutCliente, report.cliente_id) if report.cliente_id else None
    equipamento = (
        session.get(ManutEquipamento, report.equipamento_id) if report.equipamento_id else None
    )
    tecnico = session.get(User, report.tecnico_id)
    data_inspecao = ""
    if report.data_inspecao:
        data_inspecao = report.data_inspecao.strftime("%d/%m/%Y")

    report_url = f"{cfg.frontend_base_url}/relatorios/{report.id}/preencher"

    if event == "finalizar":
        acao_titulo = "Aguardando revisão"
        acao_mensagem = (
            f"O relatório {report.numero} foi finalizado e aguarda sua revisão. "
            "Acesse o SER e analise o documento."
        )
        cta_label = "Revisar relatório"
    elif event == "solicitar_correcao":
        acao_titulo = "Correções solicitadas"
        acao_mensagem = (
            f"Foram solicitadas correções no relatório {report.numero}. "
            "Ajuste o relatório conforme a descrição abaixo e finalize novamente."
        )
        cta_label = "Corrigir relatório"
    else:
        acao_titulo = "Relatório aprovado"
        acao_mensagem = (
            f"O relatório {report.numero} foi aprovado e está disponível para exportação PDF."
        )
        cta_label = "Abrir relatório"

    return EmailContext(
        report_numero=report.numero,
        report_id=report.id,
        status_label=STATUS_LABELS.get(report.status, report.status),
        tipo_inspecao=report.tipo_inspecao or "—",
        data_inspecao=data_inspecao or "—",
        cliente_nome=(cliente.CLI_NOME if cliente and cliente.CLI_NOME else "—"),
        equipamento_tag=(equipamento.EQP_TAG if equipamento else "—"),
        equipamento_nome=(equipamento.EQP_NOME if equipamento and equipamento.EQP_NOME else "—"),
        tecnico_nome=(tecnico.full_name if tecnico else "—"),
        actor_nome=actor.full_name,
        acao_titulo=acao_titulo,
        acao_mensagem=acao_mensagem,
        cta_label=cta_label,
        report_url=report_url,
        correcao_descricao=correcao_descricao,
    )


def build_subject(event: ReportEmailEvent, numero: str) -> str:
    if event == "finalizar":
        return f"[SER] Relatório {numero} — Aguardando revisão"
    if event == "solicitar_correcao":
        return f"[SER] Relatório {numero} — Correções solicitadas"
    return f"[SER] Relatório {numero} — Aprovado"


def render_email_html(ctx: EmailContext) -> str:
    esc = html.escape
    correcao_block = ""
    if ctx.correcao_descricao:
        correcao_block = f"""
        <tr>
          <td style="padding:12px 0;border-top:1px solid #e5e7eb;">
            <p style="margin:0 0 6px;font-size:13px;color:#6b7280;text-transform:uppercase;letter-spacing:.04em;">Descrição da correção</p>
            <p style="margin:0;font-size:15px;color:#111827;white-space:pre-wrap;">{esc(ctx.correcao_descricao)}</p>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Segoe UI,Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f3f4f6;padding:24px 12px;">
    <tr><td align="center">
      <table role="presentation" width="600" cellspacing="0" cellpadding="0" style="max-width:600px;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.08);">
        <tr>
          <td style="background:#56991f;padding:20px 28px;">
            <p style="margin:0;font-size:12px;color:#e8f5d9;letter-spacing:.06em;text-transform:uppercase;">SER</p>
            <h1 style="margin:6px 0 0;font-size:22px;color:#ffffff;font-weight:600;">{esc(ctx.acao_titulo)}</h1>
          </td>
        </tr>
        <tr>
          <td style="padding:28px;">
            <p style="margin:0 0 16px;font-size:16px;color:#374151;line-height:1.6;">{esc(ctx.acao_mensagem)}</p>
            <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f9fafb;border-radius:8px;padding:16px;">
              <tr><td style="padding:8px 16px;">
                <p style="margin:0 0 12px;font-size:13px;color:#6b7280;text-transform:uppercase;letter-spacing:.04em;">Detalhes</p>
                <p style="margin:0 0 6px;font-size:14px;color:#111827;"><strong>Número:</strong> {esc(ctx.report_numero)}</p>
                <p style="margin:0 0 6px;font-size:14px;color:#111827;"><strong>Status:</strong> {esc(ctx.status_label)}</p>
                <p style="margin:0 0 6px;font-size:14px;color:#111827;"><strong>Cliente:</strong> {esc(ctx.cliente_nome)}</p>
                <p style="margin:0 0 6px;font-size:14px;color:#111827;"><strong>Equipamento:</strong> {esc(ctx.equipamento_tag)} — {esc(ctx.equipamento_nome)}</p>
                <p style="margin:0 0 6px;font-size:14px;color:#111827;"><strong>Técnico:</strong> {esc(ctx.tecnico_nome)}</p>
                <p style="margin:0;font-size:14px;color:#111827;"><strong>Ação por:</strong> {esc(ctx.actor_nome)}</p>
              </td></tr>
            </table>
            {correcao_block}
            <p style="margin:24px 0 0;text-align:center;">
              <a href="{esc(ctx.report_url)}" style="display:inline-block;background:#56991f;color:#ffffff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:600;font-size:15px;">{esc(ctx.cta_label)}</a>
            </p>
          </td>
        </tr>
        <tr>
          <td style="padding:16px 28px;background:#f9fafb;border-top:1px solid #e5e7eb;">
            <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">SER — Sistema de Emissão de Relatórios</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


async def send_email_message(
    session: Session,
    to_emails: list[str],
    subject: str,
    html_body: str,
    send_log: Optional[EmailSendLogger] = None,
) -> None:
    log = send_log or EmailSendLogger()

    if not to_emails:
        raise ValueError("Nenhum destinatário informado")

    cfg = get_email_runtime_config(session)
    log.add(f"Configuração carregada — host={cfg.smtp_host}, porta={cfg.smtp_port}, ssl={cfg.smtp_use_ssl}, enabled={cfg.enabled}")

    if not cfg.enabled:
        raise ValueError("Envio de e-mail desabilitado nas configurações")

    if not cfg.smtp_host or not cfg.smtp_user or not cfg.smtp_password:
        raise ValueError("SMTP incompleto: host, usuário ou senha ausentes")

    log.add(f"Remetente: {cfg.from_name} <{cfg.from_email}>")
    log.add(f"Destinatário(s): {', '.join(to_emails)}")
    log.add(f"Assunto: {subject}")

    message = MIMEMultipart("alternative")
    message["From"] = f"{cfg.from_name} <{cfg.from_email}>"
    message["To"] = ", ".join(to_emails)
    message["Subject"] = subject
    message.attach(MIMEText(html_body, "html", "utf-8"))
    log.add(f"Mensagem HTML montada ({len(html_body)} bytes)")

    smtp = aiosmtplib.SMTP(
        hostname=cfg.smtp_host,
        port=cfg.smtp_port,
        use_tls=cfg.smtp_use_ssl,
        timeout=30,
    )

    try:
        log.add(f"Conectando a {cfg.smtp_host}:{cfg.smtp_port}...")
        await smtp.connect()
        log.add("Conexão SMTP estabelecida")

        if cfg.smtp_use_ssl:
            log.add("Canal SSL ativo (porta 465)")
        else:
            log.add("Iniciando STARTTLS...")
            await smtp.starttls()
            log.add("STARTTLS concluído")

        log.add(f"Autenticando usuário {cfg.smtp_user}...")
        await smtp.login(cfg.smtp_user, cfg.smtp_password)
        log.add("Autenticação SMTP OK")

        log.add("Enviando mensagem ao servidor...")
        errors, smtp_response = await smtp.send_message(message)
        if errors:
            raise ValueError(f"Destinatário recusado pelo servidor SMTP: {errors}")
        log.add(f"Servidor SMTP aceitou o envio ({smtp_response})")
    finally:
        try:
            await smtp.quit()
            log.add("Conexão SMTP encerrada")
        except Exception:
            pass


async def notify_report_event(
    session: Session,
    report: Report,
    event: ReportEmailEvent,
    actor: User,
    *,
    correcao_descricao: str = "",
) -> None:
    """Dispara e-mail do fluxo. Falhas são logadas e não propagadas."""
    if not is_email_configured(session):
        logger.warning("[EMAIL] SMTP não configurado — notificação ignorada (evento=%s)", event)
        return

    recipients = resolve_recipients(session, event, report, actor)
    if not recipients:
        logger.warning(
            "[EMAIL] Nenhum destinatário para evento=%s report=%s",
            event,
            report.numero,
        )
        return

    ctx = build_report_email_context(
        session,
        report,
        event,
        actor,
        correcao_descricao=correcao_descricao,
    )
    subject = build_subject(event, report.numero)
    html_body = render_email_html(ctx)

    try:
        await send_email_message(session, recipients, subject, html_body)
        logger.info(
            "[EMAIL] Enviado evento=%s report=%s para %s",
            event,
            report.numero,
            ", ".join(recipients),
        )
    except Exception as exc:
        logger.error(
            "[EMAIL] Falha ao enviar evento=%s report=%s: %s",
            event,
            report.numero,
            exc,
        )


async def send_test_report_email(
    session: Session,
    report_id: int,
    event: ReportEmailEvent,
    destinatario_teste: str,
) -> EmailTestResult:
    send_log = EmailSendLogger()
    send_log.add(f"Início do teste — relatório_id={report_id}, evento={event}")

    if not is_email_configured(session):
        send_log.fail("SMTP não configurado ou desabilitado — salve host, usuário, senha e remetente")
        return EmailTestResult(
            success=False,
            message="SMTP não configurado. Preencha e salve a aba E-mail antes de testar.",
            log=send_log.steps,
        )

    report = session.get(Report, report_id)
    if not report:
        send_log.fail(f"Relatório {report_id} não encontrado")
        return EmailTestResult(
            success=False,
            message=f"Relatório {report_id} não encontrado",
            log=send_log.steps,
        )
    send_log.add(f"Relatório encontrado: {report.numero} (status={report.status})")

    cfg = get_email_runtime_config(session)
    send_log.add(f"Remetente (From): {cfg.from_name} <{cfg.from_email}>")

    actor = session.get(User, report.tecnico_id) or session.exec(select(User).limit(1)).first()
    if not actor:
        send_log.fail("Nenhum usuário disponível para simular o ator do evento no template")
        return EmailTestResult(
            success=False,
            message="Nenhum usuário disponível para simular o ator do evento no template",
            log=send_log.steps,
        )

    dest = _normalize_email(destinatario_teste)
    if not dest:
        send_log.fail(f"E-mail de teste inválido: {destinatario_teste!r}")
        return EmailTestResult(
            success=False,
            message="E-mail de teste inválido",
            log=send_log.steps,
        )

    ctx = build_report_email_context(
        session,
        report,
        event,
        actor,
        correcao_descricao="[Teste] Descrição simulada de correção solicitada pelo revisor.",
    )
    subject = f"[SER TESTE] {build_subject(event, report.numero)}"
    html_body = render_email_html(ctx)
    send_log.add("Template HTML renderizado com dados reais do relatório")

    try:
        await send_email_message(session, [dest], subject, html_body, send_log=send_log)
    except Exception as exc:
        send_log.fail(str(exc))
        return EmailTestResult(
            success=False,
            message=f"Falha ao enviar e-mail de teste: {exc}",
            subject=subject,
            destinatario=dest,
            log=send_log.steps,
        )

    send_log.add("Teste concluído — verifique a caixa de entrada (e spam) do destinatário")
    return EmailTestResult(
        success=True,
        message=f"E-mail de teste enviado para {dest}",
        subject=subject,
        destinatario=dest,
        log=send_log.steps,
    )
