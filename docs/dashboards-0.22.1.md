# Dashboards 0.22.1

O padrão visual aprovado em Idiomas foi aplicado aos gráficos existentes de
Visão geral, Evolução física, Evolução nos estudos e Peso. As áreas sem
gráficos mantêm seus cards e formulários.

No site, `solem_charts.py` centraliza a apresentação: sem grade ou linhas
de eixo, fundo transparente, barras arredondadas, paleta azul com cores
distintas para séries diferentes e tabela recolhível com valores completos.
As barras cronológicas compactas usam o mesmo degradê de Idiomas.
Os gráficos Plotly conservam dados, unidades, limites de eixo e informações
ao apontar para um valor; rótulos longos são quebrados em duas linhas.

No Android, `CleanBars` é compartilhado por Visão geral, Idiomas, Evolução
física e Estudos. Séries cronológicas usam barras com degradê e rolagem
horizontal quando necessário. Categorias de nomes longos usam barras
horizontais. Peso tem linha com preenchimento suave e lista recolhível.
Não há animação piscante, migração ou alteração de registros/metas.

Verificações: testes de todas as páginas preenchidas e vazias, preservação
das séries/valores/unidades/ranges dos gráficos, compilação do APK e testes
JVM. Revisão visual no navegador em desktop e 390 px. APK não foi testado
em aparelho físico nesta revisão.
