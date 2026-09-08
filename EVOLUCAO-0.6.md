# Solem 0.6 — navegação e biblioteca

- Menu vertical no site; menu lateral no Android, acessível pelo botão de menu.
- Login separado da biblioteca. Anotações, Resumos, PDFs, Mapas mentais, Cronograma e Investimentos têm destinos próprios.
- No site, busca e lista de páginas à esquerda; editor à direita. No celular, abrir uma página coloca o editor em foco.
- Anotações e resumos oferecem edição Markdown e leitura formatada, sem WebView.
- Salvamento explícito: no site, salve antes de trocar de modo ou página. A leitura mostra a última versão salva.
- Arquivamento e controle de conflitos existentes foram preservados.

Esta atualização não altera tabelas nem regras de acesso. Os módulos pessoais continuam dependendo da migração `supabase/migrations/20260907_personal_workspace.sql` no mesmo Supabase e de uma conta autenticada. Não há confirmação da execução dessa migração no ambiente de produção.

O APK de teste é debug, versão 0.6.0, código 6. A distribuição release exige configurar o keystore conforme o README Android. Instale sobre o APK anterior se a assinatura for a mesma; não desinstale sem antes salvar qualquer conteúdo pendente.

Esta é uma biblioteca com editor Markdown, não um editor de blocos completo: autosave, backlinks e edição colaborativa não fazem parte desta versão.
