# Solem 0.23.0 · Idiomas e menu pessoal

- Novas sessões mantêm atividade e idioma após confirmação de gravação. No site, fonte, conteúdo e título também ficam como contexto; contagens e duração são de uma nova sessão.
- Escuta e Série/vídeo usam tipo de conteúdo, fonte, título, quantidade, idioma do áudio e legendas. Só as duas atividades do Anki usam baralho/cards. Leitura, conversação, escrita e aula têm rótulos próprios e fonte opcional.
- Campos extras `fonte_idioma` e `tipo_conteudo` ficam no JSON já existente da sessão. Não há migração ou regravação do histórico.
- `menu_tabs` (IDs estáveis) e `menu_done` ficam nas preferências privadas de `solem_journey_settings`. O APK usa o cliente autenticado, escopo por proprietário e revisão otimista. Não há mudança de RLS, credenciais ou tabelas.
- Contas genéricas recebem uma seleção inicial opcional. Contas existentes mantêm o menu anterior até escolherem outra configuração. Visão geral e configurações de personalização permanecem acessíveis.
- Site: Metas e aparência → Minhas abas. APK: Personalizar → Minhas abas. As escolhas compartilhadas sincronizam ao carregar/atualizar; abas exclusivas de uma plataforma são preservadas quando se salva na outra.
- Ocultar uma aba altera somente a navegação, não as metas, o XP nem os registros. Atalhos de missões continuam podendo abrir uma área oculta sem alterar sua seleção permanente.

## Validação

- 68 testes Python focados, incluindo criação/edição de idiomas, manutenção da seleção, contagem sem duplicação, escolha/restauração de abas, isolamento das preferências e todas as páginas com histórico preenchido e vazio.
- 147 testes JVM, sem falhas; build debug concluído e assinatura compatível com o APK anterior.
- Conferência visual local com dados fictícios, sem gravações em contas reais.
- O APK requer validação final em aparelho físico; os testes JVM não substituem a interação no Android.
