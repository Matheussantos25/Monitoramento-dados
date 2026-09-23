# Solem Android — 0.9

Visão geral sem ficha/avatar. Navegação azul; a aba Saúde reúne diário de refeições, água, peso, sono e fotos opcionais. O treino exibe histórico/recordes, sugestão conservadora por grupo e distância GPS opcional para caminhada/corrida com a tela aberta.

Aplicativo nativo Kotlin / Compose / Material 3. Usa o mesmo projeto Supabase do Streamlit. Treinos/estudos continuam na tabela legada `treinos`; novos dados de saúde usam `solem_health_entries` por usuário e fotos usam `solem_photos` com bucket privado. Execute as migrações antes de usar Saúde/Fotos.

## Funcionalidades

| Área | Disponível no Android |
|---|---|
| Visão geral | XP, níveis, sequência, marcos, resumo semanal e registros recentes |
| Treino | Todos os exercícios do catálogo web, séries, repetições, carga, descanso, isometria, cardio, distância, humor e AMRAP de 20 minutos |
| Evolução física | Filtros de período/exercício, repetições, cardio, isometria e curva do peso |
| Saúde | Refeições por tipo/horário, água por volume × quantidade, peso/sono uma vez ao dia e fotos privadas antes/depois |
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

No SQL Editor do **mesmo** projeto, execute uma vez `../supabase/migrations/20260923_health_diary.sql` e `../supabase/migrations/20260923_health_photos.sql`. As duas migrações foram aplicadas ao projeto `frxgrkgljsepykhutskq` em 23/09/2026. O bucket de fotos é privado; a foto é recodificada em JPEG sem EXIF (inclusive GPS). Não há reconhecimento facial ou avaliação automatizada de músculos. O GPS de caminhada/corrida é opt-in, só enquanto a tela está aberta e salva apenas distância em km.

A tabela legada `treinos` tem policy pública `ALL true` apesar de RLS habilitada. **Não registre novos dados pessoais nela.** A aba Saúde nova usa apenas a tabela privada. Histórico antigo de alimentação/peso não é migrado automaticamente porque não há dono atribuível com segurança. Treinos/estudos e XP legado ainda dependem da tabela compartilhada; uma migração de propriedade é recomendada antes de uso multiusuário.

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
