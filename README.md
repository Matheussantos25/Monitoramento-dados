# Solem · Corpo & Mente

Aplicativo Streamlit para acompanhar treinos, alimentação, peso e estudos. A interface inclui uma visão geral com experiência (XP), níveis, sequência de dias ativos, marcos acumulados e atalhos para os registros.

## Executar com seu banco

Use Python 3.12 ou compatível com as dependências do projeto:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

Mantenha `SUPABASE_URL` e `SUPABASE_KEY` em `.streamlit/secrets.toml` localmente, ou em **Settings → Secrets** no Streamlit Community Cloud. Nunca adicione esse arquivo ao Git. A tabela `treinos` e seus campos continuam os mesmos; nenhuma migração é necessária.

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

## Gamificação

- Treino registrado: 30 XP por dia.
- Estudo registrado: 30 XP por dia.
- Alimentação registrada: 10 XP por dia, independentemente do alimento.
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

Os vídeos, prompts, cronômetros, importação de simulados e configurações existentes continuam no projeto. As áreas são renderizadas sob demanda a partir da navegação principal. As metas existentes de 200 repetições e 150 questões foram preservadas nos painéis e apresentadas em barras compactas.

## Testes

```sh
python -m unittest discover -s tests -v
```

São 12 testes: regras de XP, duplicação, datas, sequência, limites semanais, duração exata, revisão Anki, níveis e valores inválidos; navegação nas nove páginas com histórico preenchido e vazio; atalho para treino, salvamento e recálculo de XP. Testes de interface usam somente a demonstração, nunca o banco real.

## Atualizar o Streamlit Community Cloud

Revise as alterações e integre a branch da interface à branch utilizada pelo aplicativo (atualmente `main`). Inclua os módulos, a pasta `assets` e `.streamlit/config.toml`, além de `app.py`. Preserve os Secrets existentes. A integração com Supabase em produção deve ser conferida após a atualização, pois os testes locais não usam suas credenciais.
