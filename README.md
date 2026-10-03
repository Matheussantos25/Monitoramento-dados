# Solem · Corpo & Mente

Aplicativo Streamlit para acompanhar treinos, alimentação, peso e estudos. A interface inclui uma visão geral com experiência (XP), níveis, sequência de dias ativos e atalhos para os registros.

## Executar com seu banco

Use Python 3.12 ou compatível com as dependências do projeto:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Mantenha `SUPABASE_URL` e a chave pública (`SUPABASE_PUBLISHABLE_KEY`) em `.streamlit/secrets.toml` localmente, ou em **Settings → Secrets** no Streamlit Community Cloud. Nunca adicione esse arquivo ao Git. Para ativar o diário privado de Saúde e as fotos, execute uma vez as migrações [20260923_health_diary.sql](supabase/migrations/20260923_health_diary.sql) e [20260923_health_photos.sql](supabase/migrations/20260923_health_photos.sql) no mesmo projeto Supabase.

Para a aba **Financeiro**, execute também [20260927_finance.sql](supabase/migrations/20260927_finance.sql) no mesmo projeto, uma única vez. Ela amplia a coleção privada `solem_items` com salário e assinaturas, sem apagar os investimentos e sem alterar suas políticas RLS. No projeto de produção, a migração foi aplicada em 27/09/2026.

Para as **cópias pessoais de prompts**, execute [20260928_private_prompts.sql](supabase/migrations/20260928_private_prompts.sql) depois da migração financeira. Ela só permite o novo tipo `prompt` na mesma coleção privada; não altera RLS nem os arquivos originais. Aplicada ao projeto de produção em 28/09/2026. Itens privados excluídos vão para uma lixeira recuperável; treinos e estudos legados ainda usam exclusão permanente, com confirmação.

## Experimentar sem banco

A demonstração usa somente dados fictícios e guarda alterações na sessão do navegador. Ela nunca conecta ao Supabase. Ative explicitamente a variável `SOLEM_DEMO=1`:

```powershell
# PowerShell
$env:SOLEM_DEMO = "1"
python -m streamlit run app.py
```

```sh
# macOS / Linux
SOLEM_DEMO=1 python -m streamlit run app.py
```

Não configure `SOLEM_DEMO=1` no app de produção. Para voltar ao banco no PowerShell, execute `Remove-Item Env:SOLEM_DEMO` antes de reiniciar.

## Saúde privada e dados legados

A aba Saúde permite várias refeições e registros de água por dia, mas apenas um peso e um sono por dia. Água é volume do recipiente × quantidade; os horários vêm preenchidos com a hora atual e podem ser editados. Fotos de rosto/corpo são opcionais, ficam num bucket privado por usuário e são recodificadas para remover EXIF antes do envio. A comparação usa datas escolhidas pelo usuário. Não há análise automática de rosto ou músculos.

Em **Treino**, a escolha do exercício atualiza imediatamente último registro, recorde e média; caminhada/corrida usam km registrados em vez de repetições. O botão **Iniciar GPS** aparece só nesses dois exercícios. No navegador, exige HTTPS e permissão explícita, mede apenas com a página aberta/visível e transfere distância e duração ao formulário ao tocar em **Parar GPS**; se indisponível, digite os valores manualmente. Em **Evolução física**, o período e os exercícios filtram tanto os cards quanto os gráficos. O gráfico de peso foi movido para **Saúde → Peso** e mostra só o diário privado da conta; registros legados de peso não são migrados automaticamente.

No Android, a caminhada/corrida pode continuar a medir com a tela bloqueada por meio de um serviço de localização em primeiro plano e uma notificação persistente. Inicie o GPS com o app visível e pare antes de salvar; se o sistema encerrar o serviço, confira a distância antes do registro. O site móvel não consegue garantir GPS contínuo com a página oculta/bloqueada por limitações do navegador. Nenhuma coordenada ou rota é enviada ao Supabase; somente distância e duração do treino são usadas.

### Relógios do exercício isolado

O cronômetro tem iniciar, pausar/retomar e zerar. Para atividades com duração ou isometria, pause e toque em **Usar tempo no registro** para preencher minutos ou segundos. A contagem regressiva usa **Descanso entre séries** quando esse campo existe (60 s inicialmente para novos registros), com ajuste nos dois sentidos no site; exercícios sem descanso têm configuração independente. Alterar o intervalo reinicia o temporizador, não o cronômetro. O fim do intervalo sinaliza na tela e emite som quando permitido pelo navegador/aparelho. Inicie cada intervalo manualmente; nenhuma série é criada ou salva pelo relógio.

O GPS mostra início e tempo decorrido; **Parar GPS** preenche distância e duração. A coluna existente `duracao_min` é inteira, por isso minutos são arredondados para cima e os segundos exatos ficam em `dados_extras.tempo_treino_segundos` quando a duração automática não é alterada antes de salvar. Não há migração nova. Os relógios usam diferenças de timestamps, não soma de ticks; isso corrige atrasos da interface, mas não recupera pontos GPS perdidos nem garante alarme com o navegador suspenso. Teste os controles web com `node tools/test_workout_clocks.cjs` e `python -m pytest -q`.

**Financeiro** mostra salário apenas após tocar em **Mostrar salário**, com data de início e histórico de alterações. Assinaturas têm serviço, custo, frequência mensal/anual e data de início; o custo mensal comparativo divide planos anuais por 12. Os investimentos manuais continuam disponíveis na mesma aba. Não há sincronização bancária nem cotação automática.

**Atenção:** o projeto Supabase existente tem uma policy `treinos` de acesso público total (`public`, `ALL`, `true`). Os novos dados de saúde **não** são gravados nela; ficam em `solem_health_entries` sob RLS por usuário. O histórico antigo de alimentação/peso em `treinos` não é migrado sem atribuição segura de proprietário. Treinos/estudos e a pontuação legada continuam compartilhados; revisar a proteção da tabela `treinos` é o próximo passo de privacidade. O diário privado novo ainda não adiciona XP.

## Gamificação

- Treino registrado: 30 XP por dia.
- Estudo registrado: 30 XP por dia.
- Alimentação registrada no histórico legado `treinos`: 10 XP por dia, independentemente do alimento. O novo diário privado ainda não soma XP.
- Treino e estudo no mesmo dia: bônus de 15 XP.
- Cada nível exige 250 XP. O máximo diário é 85 XP.

O cálculo usa o histórico retornado pelo banco, com uma recompensa por categoria e data. Repetir registros, aumentar carga ou registrar peso não gera XP extra. Registros vazios, datas inválidas e futuras não pontuam. Uma sessão de estudo pode ter duração, vídeo, questões ou revisão Anki. Um treino precisa ter repetições, duração, distância ou isometria.

A semana vai de segunda a domingo. As datas seguem o mesmo horário brasileiro (UTC−3) do aplicativo original. A sequência permanece ativa se houve registro ontem; uma pausa interrompe a sequência, mas mantém os pontos acumulados. Conquistas contam dias acumulados, não exigem dias consecutivos. Edições e exclusões recalculam tudo, sem contadores ou tabelas adicionais. A pontuação representa o histórico compartilhado atual do app; não adiciona contas individuais.

## Arquivos da interface

- `app.py`: navegação, formulários, painéis e integração existente com Supabase.
- `solem_ui.py`: componentes visuais e página inicial.
- `solem_progress.py`: regras de progresso independentes da interface.
- `assets/solem.css`: estilos responsivos; Manrope via Google Fonts, com fonte local de fallback.
- `.streamlit/config.toml`: tema nativo para widgets, menus e formulários.
- `demo_data.py`: dados e armazenamento temporários da demonstração.

## Android nativo

O cliente Android nativo fica em [`android-app/`](android-app/). Ele usa o mesmo projeto Supabase, sem WebView. Treinos e estudos continuam em `treinos`; o diário de Saúde usa a nova tabela privada. Leia o [mapeamento da integração](android-app/ANALYSIS.md) e o [guia de configuração e APK](android-app/README.md). As credenciais do Android ficam em `android-app/local.properties`, fora do Git; nunca copie uma chave `service_role` para o APK.

Os vídeos, prompts, cronômetros, importação de simulados e configurações existentes continuam no projeto. As áreas são renderizadas sob demanda a partir da navegação principal. As metas existentes de 200 repetições e 150 questões foram preservadas nos painéis e apresentadas em barras compactas.

## Testes

```sh
python -m unittest discover -s tests -v
```

Os testes cobrem progresso, navegação, cálculos de água/sono/treino e remoção de metadados de fotos. Testes de interface usam somente a demonstração, nunca o banco real.

## Atualizar o Streamlit Community Cloud

Revise as alterações e integre a branch da interface à branch utilizada pelo aplicativo (atualmente `main`). Inclua os módulos, a pasta `assets` e `.streamlit/config.toml`, além de `app.py`. Preserve os Secrets existentes. A integração com Supabase em produção deve ser conferida após a atualização, pois os testes locais não usam suas credenciais.
