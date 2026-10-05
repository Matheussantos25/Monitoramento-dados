# Solem Android — 0.11.0

## Interface RPG de saúde (0.11.0)

Novo painel azul-escuro com nível/XP, elo físico, missões reais do dia, ritmo semanal e sessões recentes. Navegação inferior dá acesso direto a Jornada, Saúde, Treino e Estudo; o menu continua oferecendo toda a biblioteca, gráficos, calendário e financeiro.

Em **Personalizar**, ajuste nome, tema escuro/claro/sistema, destaque Glacial/Âmbar/Rubi, metas e missões visíveis, animações/som e seções do painel. Preferências são salvas localmente por ID de conta neste aparelho: não sincronizam com o site nem com outro celular. Restaurar preferências não apaga registros. Sua conta preservada mantém seus padrões; novas contas continuam genéricas.

Missões somam registros individuais, sem duplicar sessões pelo ID. Água e sono usam apenas o diário privado, nunca a tabela compartilhada. Falha de carregamento não vira um zero fictício. As metas são pessoais, não prescrições médicas, e não alteram regras de XP/elos nem punem dias de descanso. Promoções de nível, físico e tópicos de estudo aparecem em qualquer tela após sincronização; o primeiro carregamento cria uma referência e não celebra o histórico inteiro. O maior nível/elo celebrado fica salvo por conta no aparelho para evitar repetir efeitos após edições ou reabertura.

Saúde agora abre em um resumo com hidratação, refeições, sono, peso e fotos. Atalhos de +250/+500/+750 ml salvam registros independentes no dia selecionado. As categorias quebram em linhas no celular e o seletor de data usa o calendário nativo. Edição, fotos privadas e gráfico de peso permanecem disponíveis. Exercícios, alimentos e tópicos usam seletores inferiores com busca quando há muitas opções.

Nenhuma nova tabela ou API paga foi adicionada. Ícone próprio adaptativo, incluindo versão monocromática, acompanha o APK. No Android 13+, o GPS oferece permissão opcional de notificações para mostrar o controle Parar na tela bloqueada. Sem ela, o serviço continua, mas o controle fica no app; atualizações de notificação checam a permissão para evitar falhas.

Testes unitários cobrem metas, somas, isolamento do diário, tempo exato de estudo, validação e promoções. Para conferir visualmente no Android Studio, veja as prévias de `JourneyDashboardPreview.kt`. Compilação/testes não substituem a avaliação no aparelho real, com fonte ampliada e TalkBack.

Validação desta versão: 43 testes unitários passando, APK debug compilado, assinatura verificada e lint sem erros bloqueantes. Permanecem avisos de manutenção (incluindo dependências e EXIF legado). Não havia aparelho/emulador disponível: fluxos visuais, permissões de notificação e o GPS com tela bloqueada precisam de conferência no celular.

O reconhecimento de refeições por API foi removido. Alimentação manual, histórico e edição nutricional dos registros existentes continuam disponíveis. A função publicada retorna 410 para impedir que APKs antigos chamem o provedor pago. Consulte [status e alternativas locais](../REFEICOES-POR-FOTO.md).

Visão geral sem ficha/avatar. Navegação azul; a aba Saúde reúne diário de refeições, água, peso, sono e fotos opcionais. O treino exibe histórico/recordes, sugestão conservadora por grupo e distância GPS opcional para caminhada/corrida inclusive com a tela bloqueada, enquanto a notificação de medição estiver ativa. A aba Financeiro reúne salário (oculto até revelar), assinaturas e os investimentos existentes.

Aplicativo nativo Kotlin / Compose / Material 3. Usa o mesmo projeto Supabase do Streamlit. Treinos/estudos continuam na tabela legada `treinos`; novos dados de saúde usam `solem_health_entries` por usuário e fotos usam `solem_photos` com bucket privado. Execute as migrações antes de usar Saúde/Fotos.

## Funcionalidades

| Área | Disponível no Android |
|---|---|
| Visão geral | Painel RPG, XP, níveis, sequência, missões editáveis, elos, ritmo semanal e registros recentes |
| Treino | Todos os exercícios do catálogo web, séries, repetições, carga, descanso, isometria, cardio, distância, humor e AMRAP de 20 minutos |
| Evolução física | Filtros de período/exercício aplicados aos indicadores e gráficos, repetições, distância, cardio e isometria |
| Saúde | Resumo diário, registro rápido de água, refeições por tipo/horário, água por volume × quantidade, peso/sono uma vez ao dia, gráfico de peso privado e fotos antes/depois |
| Estudar | Questões, vídeo-aula, decks Anki, disciplinas e tópicos do edital; bússola de estudos |
| Foco | Pomodoro, cronômetro, pausa/reinício e vídeos motivacionais originais |
| Simulados | Colar JSON, validar, conferir prévia e importar os dois formatos usados pela web |
| Evolução nos estudos | Edital completo, horas, acertos, questões, Anki, tópicos fracos, gráficos por dia/disciplina/tópico e cronograma de 30 dias |
| Prompts | Biblioteca original, seleção e cópia do texto |
| Histórico | Busca, filtros, edição e exclusão com confirmação |

Os gráficos são visuais nativos adaptados ao celular, não cópias interativas do Plotly. Os 10 catálogos foram extraídos diretamente de `app.py`, incluindo tópicos com vírgulas. `tools/sync_web_assets.py` permite regenerá-los junto aos prompts, vídeos e exemplos de teste quando a web mudar.

## Localização após a transferência

- Projeto: `E:\Android\Monitoramento-dados\android-app`
- Cache: `E:\Android\GradleCache`
- SDK: `E:\Android\Sdk`

Os caminhos antigos do projeto, `.gradle` e SDK no C: são junções para o E:, não cópias duplicadas. Não apague o conteúdo dessas junções: ele é o conteúdo real no E:. Mantenha o disco E: disponível.

Abra a pasta acima no Android Studio. Use o **Java incluído no Android Studio (jbr)** nas configurações de Gradle. Nesta máquina o Android Studio já estava instalado em `E:\Nova pasta`; a compilação em linha de comando com o outro Java instalado falhou na configuração dos scripts, mas o Java do Studio funciona.

## Configurar a conexão

O arquivo local `local.properties` continua fora do Git. Exemplo (substitua os valores, sem aspas):

```properties
sdk.dir=E:/Android/Sdk
SUPABASE_URL=https://SEU-PROJETO.supabase.co
SUPABASE_PUBLISHABLE_KEY=SUA_CHAVE_PUBLICAVEL_OU_ANON
```

Nunca use `service_role` ou uma chave `sb_secret_`. A chave cliente pode ser extraída do APK; a autorização continua sendo responsabilidade das policies do Supabase. O app exige login pelo Supabase Auth antes da navegação. Erros de sessão/rede são apresentados sem expor credenciais.

No SQL Editor do **mesmo** projeto, execute uma vez `../supabase/migrations/20260923_health_diary.sql`, `../supabase/migrations/20260923_health_photos.sql` e `../supabase/migrations/20260927_finance.sql`. As migrações foram aplicadas ao projeto `frxgrkgljsepykhutskq`. O bucket de fotos é privado; a foto é recodificada em JPEG sem EXIF (inclusive GPS). Não há reconhecimento facial ou avaliação automatizada de músculos. O GPS de caminhada/corrida é opt-in: inicia com o app aberto, continua com a tela bloqueada via serviço em primeiro plano e notificação persistente. Pare antes de salvar. O serviço não grava coordenadas ou trajeto; só a distância em km é usada no registro.

A tabela legada `treinos` tem policy pública `ALL true` apesar de RLS habilitada. **Não registre novos dados pessoais nela.** A aba Saúde nova usa apenas a tabela privada. Histórico antigo de alimentação/peso não é migrado automaticamente porque não há dono atribuível com segurança. Treinos/estudos e XP legado ainda dependem da tabela compartilhada; uma migração de propriedade é recomendada antes de uso multiusuário.

As cópias privadas de prompts também requerem `../supabase/migrations/20260928_private_prompts.sql`, aplicada depois da migração financeira. Ela já foi aplicada ao projeto de produção em 28/09/2026. As páginas, PDFs e itens financeiros excluídos permanecem recuperáveis na lixeira; os treinos e estudos legados ainda têm exclusão permanente com confirmação.

## Relógios do treino (0.9.8)

Exercício isolado inclui cronômetro com pausa/retomada e temporizador. O temporizador acompanha o campo de descanso entre séries quando disponível; nos demais exercícios, ajuste seu próprio intervalo. Alterar o intervalo reinicia a contagem. Inicie manualmente cada descanso. Para isometria ou cardio, **Usar tempo no registro** preenche a medida correspondente, sem salvar automaticamente.

O serviço GPS agora mede também a duração com o relógio monotônico do Android, inclusive enquanto a tela estiver bloqueada. Ao parar pelo app ou pela notificação, distância e duração são transferidas ao formulário quando a tela estiver ativa. Minutos são arredondados para cima para compatibilidade com a coluna inteira; segundos exatos ficam em `dados_extras.tempo_treino_segundos` se a duração automática não for alterada. Nenhuma coordenada é persistida e nenhuma migração adicional é necessária. Compilação e testes automatizados não substituem um teste de percurso no aparelho real, especialmente com economia de bateria.

## Compilar e instalar

No PowerShell, dentro de `android-app`:

```powershell
.\build-apk.ps1
```

O script encontra o Java do Android Studio, gera o APK debug e executa os testes. Se necessário, passe `-JavaHome 'caminho/para/jbr'`. O APK instalável fica em `app/build/outputs/apk/debug/app-debug.apk`.

Para a variante release:

```powershell
.\build-apk.ps1 -Variant Release
```

Sem assinatura configurada, o arquivo é `app-release-unsigned.apk`, que não pode ser instalado diretamente. Para obter `app-release.apk` assinado, use **Build > Generate Signed Bundle / APK > APK**, ou configure `keystore.properties` a partir do exemplo existente. Crie o keystore apenas uma vez e mantenha arquivo e senhas fora do Git, com backup seguro. Nunca substitua a chave de assinatura de um app que você já distribuiu.

```powershell
keytool -genkeypair -v -keystore E:/Android/assinatura/solem-release.jks -alias solem -keyalg RSA -keysize 4096 -validity 10000
```

Crie primeiro a pasta de assinatura. As senhas são solicitadas interativamente; não as escreva no terminal nem no README. Para atualizar o APK instalado, mantenha a mesma assinatura e o mesmo `applicationId`. Não desinstale para contornar um conflito de assinatura sem antes conferir seus dados.

Transfira o APK para o celular, abra-o e permita a instalação pela fonte escolhida. Android mínimo: 8.0 / API 26. Nenhum emulador é necessário para gerar o APK.

## Arquitetura e regras

- Compose e Navigation Compose apresentam as áreas; ViewModel + StateFlow mantêm histórico, mensagens e gravação em andamento.
- O Repository pagina a leitura, grava na tabela existente e usa Realtime como sinal para recarregar o histórico. O transporte OkHttp suporta WebSocket. Após gravar, há uma consulta de confirmação visual independente do Realtime.
- Os metadados existentes em `dados_extras` são preservados ao editar. Registros importados de simulados permitem ajustar data/hora, mas não sobrescrever os detalhes de questões por um formulário agregado.
- AMRAP e simulados são enviados em um único lote, sem gravar parcialmente vários requests.
- Cálculos de apresentação continuam derivados do histórico; não são persistidos como contadores paralelos.
- O importador foi comparado com resultados produzidos pelas funções reais do Python. Validações críticas ainda não foram centralizadas no backend: fazer isso exige uma alteração coordenada com a web, não foi feita uma migração de banco silenciosa.

## Testes e limitações

```powershell
python tools/sync_web_assets.py
.\build-apk.ps1
```

O gerador de exemplos usa pandas, já dependência da web, e executa somente as funções puras selecionadas por AST, sem iniciar Streamlit nem acessar o Supabase. Os testes cobrem os dois formatos de simulado, arredondamento/distribuição de tempo, questões anuladas, duplicação de números, catálogo/rotação, metadados e progresso.

Limitações conhecidas:

- Sem gravação offline/fila local. Em caso de falha de confirmação, atualize o histórico antes de reenviar para evitar duplicações.
- A detecção de simulado já importado usa o histórico, como na web; não é uma restrição transacional entre dois aparelhos importando ao mesmo tempo.
- O cronômetro mantém o tempo usando o relógio monotônico enquanto sua tela permanece no fluxo. Não é um serviço de alarme em segundo plano; não garante alerta após encerrar o app ou reiniciar o aparelho.
- Sem edição individual de questões importadas, exportação interativa do Plotly ou cópia pixel a pixel da interface web.
- A sincronização depende da conexão, das permissões e da publicação Realtime existentes. Há atualização manual como alternativa.

Antes de distribuir amplamente, valide em um aparelho: leitura do histórico, criação/edição/exclusão de um registro de teste em cada área, atualização pela web, importação de um simulado de teste e áudio/vídeo. Não execute testes destrutivos sobre registros reais.
# Novas contas — 0.9.9

O APK identifica o perfil após restaurar/validar o login, pela data de cadastro do
Supabase Auth e pelo manifesto compartilhado `account_defaults.json`. Novas contas
usam catálogos amplos, prompts gerais e históricos privados em `solem_activities`.
Contas existentes continuam com os catálogos e histórico legados. O ViewModel de
treino é separado por ID de conta para não reaproveitar a lista de outro login.
Instale o novo APK para receber esta seleção; APKs antigos continuam com o catálogo
antigo. Nenhuma chave privilegiada foi adicionada.
