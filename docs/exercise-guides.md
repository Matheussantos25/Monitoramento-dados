# Guias de técnica · 0.14.1

Em **Treino → Exercício isolado**, o guia acompanha o exercício selecionado.
Toque em **Ver execução e pegada**. As figuras têm rosto, tronco, mãos e membros
com volume. Início/Meio/Final e o controle deslizante permitem examinar o movimento.
Reproduzir interpola nove poses vetoriais em dois ciclos de oito segundos, com
limite de 30 atualizações por segundo. Não é captura de movimento nem análise da
execução do usuário. As referências estáticas não recebem animação.

## Desempenho e privacidade

- Desenhos vetoriais originais, sem imagens baixadas, bibliotecas extras, GIF ou vídeo.
- Web: SVG no componente local. Android: Canvas nativo e asset empacotado, sem WebView.
- Um único catálogo de aproximadamente 285 KB contém todas as coordenadas e dicas.
  No site, apenas o exercício selecionado é enviado ao componente; no APK, o
  catálogo fica empacotado e não precisa ser baixado durante o treino.
- Nenhuma consulta ao Supabase, uso de câmera, API de IA ou alteração do histórico.
- Sem reprodução automática. Web para ao fechar, sair da área visível ou ocultar a
  página; Android para ao fechar, trocar de exercício ou sair do aplicativo.
- Preferência de movimento reduzido desabilita a reprodução; posições manuais permanecem.
- O link de referência só abre um site externo se o usuário tocar nele.

## Conteúdo

18 exercícios têm ilustrações (17 desenhos, alguns compartilhados).
Pronada e supinada têm detalhes ampliados de dorso/palma, dedos e polegar,
distâncias diferentes entre as mãos no corpo e textos explícitos.
Abdominal Levantada é elevação das pernas deitado e Remada em Pé na Polia é
puxada horizontal ao abdômen, conforme confirmação do usuário.

Massagem Facial e Mewing com borracha mantêm cadastro e histórico, mas não recebem
instruções de pressão/carga facial. Planche legado não recebe progressão sem
orientação profissional. Exercícios desconhecidos exibem aviso, nunca uma técnica
adivinhada. Handstand e L-Sit mostram somente uma posição final, sem ensinar entrada.

As referências são ACE Exercise Library, ACE Chin-Ups, Mayo Clinic (técnica geral
e agachamento) e ADA (exercitadores mandibulares), com links no catálogo. Os
desenhos não são reprodução de figuras dessas fontes nem material validado por elas.

## Manutenção e testes

`python tools/build_exercise_guides.py` gera os três JSONs idênticos (web, APK e
testes Kotlin). `android-app/tools/sync_web_assets.py` também copia o catálogo web.
Editar o desenho em `tools/exercise_figure_art.py` e as dicas no gerador, não os
JSONs individuais. `tools/preview_exercise_figures.py` cria uma galeria local
isolada para inspecionar todas as poses, sem dados pessoais.

Testar: `python -m pytest tests`, `node tools/test_exercise_guides.cjs` e
`android-app/build-apk.ps1` (JDK/SDK conforme README Android). A suíte verifica
cobertura do catálogo, paridade, dimensões, pegadas, duração/cancelamento,
fallback e preservação de registros durante a troca do exercício.
