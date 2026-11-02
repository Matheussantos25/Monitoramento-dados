# Idiomas 0.22

O painel do Streamlit e do Android permite escolher Dia, Últimos 7 dias, Mês,
Semestre ou Ano, usando uma data de referência. Semana significa os sete dias
até essa data; mês, semestre e ano são períodos do calendário. O intervalo
atual termina em hoje. A faixa de datas fica explícita no painel.

Todos os indicadores e o gráfico usam o mesmo intervalo e filtro de idioma.
O gráfico agrupa por hora no dia, por dia na semana/mês e por mês no
semestre/ano. Dias sem registros continuam visíveis. O histórico e o XP
permanecem intactos; não há migração de dados.

O horário da sessão aceita busca por prefixo (22 mostra 22:00 a 22:59),
horário completo ou 2217. Valores inválidos impedem a gravação. Segundos de
horários antigos são preservados ao editar.

Séries, animes, filmes e vídeos compartilham o tipo de registro existente.
Os títulos são sugeridos a partir das sessões da própria conta, com os mais
recentes primeiro, sem duplicatas por capitalização. Também é possível
digitar um título novo; ele aparece nas sugestões depois de salvar.

Validação: testes de limites de calendário, filtragem, totais, deduplicação,
gráficos, horários e sugestões em Python e Kotlin; AppTest para o formulário
e painel; fluxo real no navegador em demonstração, incluindo título novo,
reutilização e largura de 390 px. O APK foi compilado e assinado com a mesma
chave das versões anteriores. Não foi realizado teste em aparelho físico.
