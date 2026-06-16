# Ticket #268 — Bloquear edição após envio para revisão

**Tipo:** Melhoria / Correção  
**Data:** 2026-05-19  

> Cópia espelhada em `t:\tickets\268\ticket-268-espec.md`

Documento completo no caminho acima do drive T:.

**Resumo:** Após finalizar (`em_revisao`), técnico ainda edita porque backend aceita PUT e frontend só esconde botões Finalizar/Salvar, mantendo campos editáveis e auto-save.

**Correção:** Matriz papel × status no backend + `canEditReport()` no frontend + modo somente leitura no wizard.

**Veredito:** Pronto para desenvolvimento (confirmar se Suporte deve editar em `em_revisao`).
