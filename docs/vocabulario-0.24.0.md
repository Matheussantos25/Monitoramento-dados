# Solem 0.24.0 · Cartões e revisão

- Escuta não exibe legendas; novos salvamentos usam Sem legenda. Série / vídeo mantém o seletor. Registros anteriores não são migrados.
- Front mostra só a frase com a palavra/forma flexionada em negrito. Back mostra significado e imagem selecionada, com créditos. Busca gratuita e exportação continuam disponíveis.
- Revisar apresenta apenas cartões completos e vencidos. O verso e as avaliações ficam ocultos até Mostrar resposta. Lixeira não entra na fila.
- Agendamento próprio do Solem, inspirado nos quatro níveis de resposta de ferramentas como Anki; não é FSRS nem sincronização com a coleção Anki. Referências: https://docs.ankiweb.net/studying.html e https://faqs.ankiweb.net/what-spaced-repetition-algorithm.html.
- Aprendizado: Errei 1 min, Difícil 5 min (10 min no segundo passo), Bom 10 min e depois 1 dia, Fácil 4 dias. Após aprender: Difícil ×1,2, Bom ×facilidade e Fácil ×facilidade×1,3; mínimo intervalo anterior +1 dia. Facilidade entre 1,3 e 3. Erro reinicia aprendizado. Intervalos são mostrados antes de avaliar.
- Campo review no JSON do cartão privado existente: vencimento em epoch UTC, passo, intervalo, facilidade, contadores e última revisão. Site e APK usam os mesmos campos/regras. Edição preserva review; gravação usa revisão otimista existente para evitar respostas duplicadas entre aparelhos. Nenhuma tabela ou RLS mudou.
- Revisar aqui não aumenta contadores de cards adicionados/revisados no Anki nem cria registros de tempo fictícios.
- Formulários de água e refeição simples recebem default explícito local no time_input. Sem ele, clear_on_submit usava o relógio UTC do servidor visualmente, embora a sessão enviasse o horário local.
- Validação: testes Python de passos, crescimento, reaprendizado, HTML, edição, fila, gravação única e horário/default; testes JVM equivalentes e build APK. Conferência visual com cartão fictício em ambiente local. APK ainda requer teste em aparelho físico.
