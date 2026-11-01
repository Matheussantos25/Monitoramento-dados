# Solem 0.20 — Idiomas

Site e APK ganham a área **Idiomas**, disponível também em contas novas. A aba Estudar e os registros anteriores permanecem. Não há migração nem alteração de refeições ou estudos salvos.

Cada sessão registra idioma (incluindo personalizado), data, horário e tempo efetivo. Atividades: revisão no Anki, criação de cards, série/vídeo, leitura, conversação, escuta, escrita e aula/prática. Cards revisados e adicionados são métricas distintas. Mídia inclui título, quantidade, áudio e modo de legenda. Para vários episódios, o usuário informa o total realmente assistido: dois de 25 minutos somam 50; a quantidade não multiplica esse tempo novamente.

O painel exibe tempo do dia, tempo de revisão, cards e episódios, com filtro de idioma e gráfico de sete dias. O histórico permite editar a sessão pelo mesmo ID. O registro do Anki é manual, sem integração ou API paga.

Persistência: usa o cliente autenticado e a tabela de atividades já autorizada para cada conta, com `grupo_muscular=Estudos` e `dados_extras.language_schema=1`. `duracao_min` contém o tempo uma única vez; `repeticoes`, questões e `tempo_video` permanecem zero. A prática participa da regra existente de XP diário de estudo; os cards não contam como questões. Os formulários antigos de estudo não editam esses registros; o editor específico preserva seus campos.

Correção adicional: horários de novos registros simples de alimentação e água mantêm a escolha enquanto o relógio avança, em vez de mudar a identidade do campo no envio. A correção não altera registros existentes.

Validação: testes de totais, idiomas, edição sem duplicação, isolamento da navegação de contas novas, preservação do histórico, mudanças de tipo, tempo de mídia sem duplicação e regressão do horário de refeição. APK compilado e testes JVM. Teste visual web com dados fictícios; testes no aparelho físico continuam necessários para avaliar teclado e tamanho de fonte em cada dispositivo.
