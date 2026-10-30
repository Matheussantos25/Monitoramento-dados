# Solem 0.19 — orientação, conforto e ritmo

Esta versão amplia o Streamlit e o Android existentes. Não migra tabelas,
não altera refeições, treinos, XP, metas já salvas ou regras de autorização.

## Revisão e decisões

- A primeira visita tinha muitas áreas e nenhum caminho guiado. Agora há um guia
  opcional em cinco etapas, com personagem vetorial local e movimento curto ao
  avançar. Não há vídeo de abertura, bloqueio temporizado, flash ou som do guia.
  O usuário pode concluir, recolher e reabrir. Na web a conclusão fica nas
  preferências privadas; no Android fica por conta e aparelho.
- As conquistas e as técnicas tinham preferências de movimento dispersas. O
  modo tranquilo desativa movimento decorativo e sons de conquista. Na web
  também alcança os componentes de técnica e calendário. A preferência do
  sistema por movimento reduzido continua respeitada. Contraste reforçado,
  texto maior e foco visível complementam os estados descritos por texto/números.
- O painel ganha gráfico dos últimos sete dias, com sessões reais, valores
  legíveis e alternativa textual. Não confunde quantidade de repetições com
  sessões; não inclui registros futuros/vazios nem duplica o mesmo ID.
- Conta nova deixa de mostrar o atalho de publicações. Elos ficam recolhidos
  inicialmente para priorizar as ações do dia.
- Mídia de treino passa a ser escolhida pelo usuário. Nenhuma nova reprodução
  começa automaticamente. Não há download de conteúdo de plataformas nem API paga.

## Mídia e privacidade

Web: arquivos de áudio/vídeo de até 30 MB ficam na sessão Streamlit (processados
pelo servidor da aplicação para reprodução, sem persistência no banco). Até oito
links favoritos HTTPS são salvos em `solem_journey_settings.preferences.media`,
com RLS já existente e revisão otimista. Só aceita YouTube, Spotify e SoundCloud;
abre o serviço por ação explícita. Não busca URLs arbitrárias no servidor.

Android: seletor de documentos do sistema, sem permissão de leitura geral do
armazenamento. Salva URI persistente e nome por conta/aparelho, sem copiar arquivo
para o servidor. Áudio/vídeo local pausa ao sair da tela/bloquear o aparelho.
Links abrem o serviço externo; a reprodução em segundo plano depende desse
serviço. Remover favorito não apaga o arquivo original. Não há sincronização
de favoritos entre site e APK nesta versão, e a interface explica o escopo.

As preferências novas têm valores padrão compatíveis. Salvar guia ou mídia usa
as preferências já carregadas e o controle de revisão existente. Nenhuma operação
cria registros de saúde/treino. Não se guarda token, senha ou localização na mídia.

## Validação e limites

- Testes Python: preferências antigas, isolamento entre contas, destinos de links,
  deduplicação dos gráficos e fluxo Streamlit de guia, acessibilidade e favoritos.
  A suíte completa também cobre os fluxos legados.
- Testes JVM: URLs, preferências, sessões/dias e regressões existentes. APK compila
  com a assinatura de atualização já usada.
- Revisão visual web: viewport estreito, navegação do guia, versão desktop e
  controles acessíveis. Dados de demonstração identificados, sem tocar na conta real.
- Ainda é necessária validação de TalkBack, ampliação de fonte e reprodução em
  aparelho físico. Compilação e testes JVM não substituem essa verificação.
- Não é uma certificação WCAG nem garantia de ausência de gatilhos para epilepsia.
  Arquivos e vídeos externos escolhidos pelo usuário podem conter flashes. O modo
  tranquilo não modifica esses vídeos. Não há promessa de adesão diária compulsória.

Referências para os critérios adotados:
- https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide
- https://www.w3.org/TR/WCAG22/ (uso de cor, contraste, foco e movimento)
