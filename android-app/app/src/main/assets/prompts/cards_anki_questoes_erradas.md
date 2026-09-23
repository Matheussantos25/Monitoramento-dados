# PROMPT — GERAR CARDS ANKI DAS QUESTÕES ERRADAS DO SIMULADO

Com base no **simulado que acabei de realizar, nas minhas respostas e na correção já feita nesta conversa**, gere cards para o Anki **SOMENTE das questões que eu errei**.

Não crie cards para questões que acertei.

Não crie cards para questões anuladas.

Se houver questão cujo gabarito tenha sido posteriormente corrigido ou anulado, considere sempre a **correção final válida**.

---

# 1. OBJETIVO DOS CARDS

Quero usar os cards para:

- refazer exatamente as questões que errei;
- entender por que errei;
- aprender o procedimento correto;
- reconhecer rapidamente o mesmo padrão em uma nova questão;
- memorizar um **bizu simples e eficiente** para prova.

Cada questão errada deve gerar **1 card**.

---

# 2. FRENTE DO CARD

Na frente, coloque a **questão completa**, incluindo:

- enunciado integral;
- todos os dados fornecidos;
- fórmulas;
- tabelas, quando existirem;
- código, quando existir;
- todas as alternativas **A, B, C, D e E**.

NÃO resuma a questão.

NÃO reescreva em versão simplificada.

NÃO retire partes que possam ser importantes para o raciocínio.

NÃO coloque:

- “Questão 41”;
- “Questão 52”;
- número da questão;
- assunto;
- gabarito;
- pista da resposta.

A frente deve começar diretamente pelo **texto bruto da questão**.

Exemplo:

Em determinada população, 10% dos indivíduos apresentam...

e NÃO:

Questão 43 — Em determinada população...

---

# 3. VERSO DO CARD

O verso deve possuir exatamente esta estrutura lógica:

**Gabarito: (X)**

**Passo a passo:**

Explique como resolver a questão corretamente, em etapas curtas e fáceis de acompanhar.

Depois:

**Bizu:**

Mostre a maneira **mais simples, rápida e prática possível** de reconhecer ou resolver esse padrão em uma prova.

O bizu deve ser realmente útil para concurso.

Evite apenas repetir a teoria.

Sempre que possível, transforme o conceito em uma regra curta, como:

- “PCA + escalas muito diferentes → padronize antes.”
- “LEFT JOIN + preservar todos da esquerda → filtro da direita no ON.”
- “γ ↑ → alcance ↓ → complexidade ↑ → overfitting ↑.”
- “Boxplot: primeiro encontre a cerca; outlier é quem ultrapassa a cerca.”
- “Bayes com porcentagem → imagine 100 pessoas.”

Se houver uma **pegadinha específica** que causou meu erro, destaque-a no verso.

---

# 4. EXPLICAÇÃO PASSO A PASSO

O passo a passo deve utilizar os **mesmos números e dados da questão**.

Para questões matemáticas, mostre as contas intermediárias.

Por exemplo, não escreva apenas:

“Aplicando Bayes, obtemos 1/3.”

Prefira:

Imagine 100 pessoas.

10 possuem a condição.

90% de 10 = 9 verdadeiros positivos.

90 não possuem a condição.

20% de 90 = 18 falsos positivos.

Logo:

\[
P(\text{condição}\mid +)
=
\frac{9}{9+18}
=
\frac13
\]

A explicação deve ser suficientemente completa para eu entender o erro, mas sem virar uma aula longa.

---

# 5. MATEMÁTICA — USAR MATHJAX DO ANKI

Todas as expressões matemáticas devem ser formatadas usando **MathJax compatível com o Anki**.

Para matemática no meio de uma frase, use:

`\( ... \)`

Exemplo:

`\(x\to0\)`

Para fórmulas em destaque, use:

`\[ ... \]`

Exemplo:

`\[\frac{a-b}{2}\]`

Utilize LaTeX adequadamente para:

- frações;
- raízes;
- limites;
- derivadas;
- integrais;
- probabilidades;
- matrizes;
- vetores;
- somatórios;
- potências;
- subscritos;
- símbolos estatísticos.

Prefira:

`\[\frac{1}{1+e^{-z}}\]`

em vez de:

`1/(1+e^(-z))`

Prefira:

`\[\sqrt{1+4x}\]`

em vez de escrever a fórmula de maneira visualmente improvisada.

O objetivo é que as fórmulas apareçam no Anki com aparência semelhante à matemática renderizada pelo ChatGPT.

---

# 6. NEGRITO — NÃO USAR MARKDOWN

O Anki não deve receber:

`**Gabarito**`

Use HTML:

`<b>Gabarito</b>`

Utilize `<b>...</b>` para destacar apenas palavras realmente importantes, como:

- gabarito;
- conceito central;
- palavra-chave;
- regra;
- pegadinha;
- resultado final.

Exemplo:

`<b>Data leakage</b>`

---

# 7. QUEBRAS DE LINHA

Utilize HTML:

`<br>`

ou

`<br><br>`

para organizar visualmente os cards.

NÃO utilize quebras físicas de linha dentro de um card no arquivo final.

Cada card inteiro deve ocupar **uma única linha física do arquivo**.

As quebras que aparecerão visualmente no Anki devem existir através de `<br>`.

---

# 8. CÓDIGO PYTHON / NUMPY / PANDAS / R / SPARK

Quando a questão possuir código, preserve o código **COMPLETO**.

NÃO corte linhas.

NÃO omita indentação.

NÃO deixe apenas a primeira linha do código.

Exemplo de aparência desejada:

`<div style="background:#f5f5f5;border:1px solid #ddd;border-radius:6px;padding:10px;white-space:pre-wrap;font-family:monospace">def f(x, valores=[]):<br>&nbsp;&nbsp;&nbsp;&nbsp;valores.append(x)<br>&nbsp;&nbsp;&nbsp;&nbsp;return len(valores)</div>`

Preserve corretamente:

- indentação;
- colchetes;
- parênteses;
- aspas;
- operadores;
- listas;
- matrizes;
- outputs.

Se a resolução depender de acompanhar a execução do código, mostre o trace passo a passo no verso.

---

# 9. SQL

Questões SQL também devem aparecer completas.

Cada alternativa deve continuar legível e separada das outras.

Use bloco HTML visual para consultas SQL.

Exemplo:

`<div style="background:#f5f5f5;border:1px solid #ddd;border-radius:6px;padding:10px;white-space:pre-wrap;font-family:monospace">SELECT * FROM CLIENTE C<br>LEFT JOIN PEDIDO P<br>ON C.id = P.cliente_id</div>`

IMPORTANTE:

Caracteres que possam ser interpretados como HTML devem ser escapados quando necessário.

Por exemplo:

`<` → `&lt;`

`>` → `&gt;`

`<>` → `&lt;&gt;`

Isso é especialmente importante em SQL, Python e comparações matemáticas escritas fora do MathJax.

Não permita que uma alternativa seja cortada porque contém `<`, `>`, `<>`, `<=` ou `>=`.

---

# 10. FORMATO DO ARQUIVO — MUITO IMPORTANTE

NÃO use ponto e vírgula `;` como separador.

Código SQL e outros conteúdos podem conter `;`, o que pode quebrar a importação.

Utilize **TABULAÇÃO REAL (TAB)** como separador entre os dois campos.

Cada linha deverá possuir exatamente:

`FRENTE[TAB]VERSO`

Ou seja:

- campo 1 = Frente;
- campo 2 = Verso;
- exatamente **1 TAB** separando os campos;
- uma linha por card.

O arquivo deve ser salvo em:

**UTF-8**

Preferencialmente com extensão:

`.txt`

ou

`.tsv.txt`

---

# 11. NÃO CRIAR CAMPOS EXTRAS

Cada linha deve possuir **exatamente dois campos**:

1. Frente
2. Verso

NÃO adicione:

- número da questão;
- tags;
- assunto;
- dificuldade;
- minha resposta;
- nível de confiança;
- comentários externos;

como campos separados.

Essas informações podem ser utilizadas para construir a explicação, mas não devem gerar novas colunas.

---

# 12. PRESERVAÇÃO DAS ALTERNATIVAS

Todas as alternativas precisam aparecer na frente.

Formato visual:

(A) alternativa

(B) alternativa

(C) alternativa

(D) alternativa

(E) alternativa

Cada alternativa deve ficar visualmente separada usando `<br>`.

Se uma alternativa possuir código ou fórmula, preserve tudo integralmente.

---

# 13. BIZU PARA QUESTÕES DE CÁLCULO

Sempre procure primeiro uma solução de prova que seja:

1. correta;
2. simples;
3. rápida;
4. fácil de memorizar.

Se existir um padrão que permita evitar cálculos longos, ensine esse padrão.

Por exemplo, para:

\[
\lim_{x\to0}
\frac{\sqrt{1+ax}-\sqrt{1+bx}}{x}
\]

pode ser útil registrar no bizu:

\[
\boxed{\frac{a-b}{2}}
\]

Em uma questão de Bayes, pode ser mais simples utilizar uma população hipotética de 100 pessoas do que aplicar diretamente uma fórmula abstrata.

Em uma questão de código, pode ser mais simples acompanhar variável por variável.

Em SQL, identificar primeiro o que precisa ser preservado.

O objetivo do bizu é:

> “Se essa estrutura aparecer novamente na prova, qual é o caminho mais rápido para chegar à resposta?”

---

# 14. CARDS DE ERROS DE ALTA CONFIANÇA

Se eu tiver errado uma questão com confiança **(3)**, o card deve dar atenção especial à confusão que me levou à falsa certeza.

No verso, depois do passo a passo, o bizu deve explicitar brevemente a pegadinha.

Exemplo:

`<b>Pegadinha:</b> 30 é a cerca superior, não um outlier. Outlier precisa ser maior que 30.`

Não precisa criar um segundo card para isso.

---

# 15. QUESTÕES ANULADAS

Se uma questão tiver sido anulada durante a correção:

**NÃO gere card para ela.**

Mesmo que minha alternativa originalmente estivesse diferente do gabarito inicialmente pensado.

---

# 16. VALIDAÇÃO OBRIGATÓRIA ANTES DE ENTREGAR

Antes de entregar o arquivo, faça uma validação automática.

Confirme que:

- a quantidade de cards é igual à quantidade de questões erradas válidas;
- nenhuma questão acertada foi incluída;
- nenhuma questão anulada foi incluída;
- nenhuma frente está vazia;
- nenhum verso está vazio;
- nenhuma questão ficou truncada;
- todas as alternativas A–E estão presentes quando existiam na questão original;
- todo código está completo;
- SQL não foi cortado;
- cada linha possui exatamente **2 campos**;
- os campos estão separados por exatamente **1 TAB**;
- nenhum TAB adicional existe dentro dos campos;
- cada card ocupa exatamente **1 linha física**;
- o negrito utiliza `<b>...</b>`;
- não existe `**Markdown**` usado para negrito;
- fórmulas estão em MathJax;
- o arquivo está em UTF-8.

Se qualquer card falhar nessa validação, **corrija-o antes de gerar o arquivo final**.

---

# 17. ENTREGA

Não cole todos os cards no chat.

Crie diretamente um arquivo pronto para importação no Anki.

Nome sugerido:

`anki_erros_simulado_XX_completo_mathjax.tsv.txt`

Ao final, informe apenas:

- quantidade de cards gerados;
- que foram incluídas somente questões erradas válidas;
- link para baixar o arquivo;
- instrução de importação:

**Separador:** Tabulação / Tab

**Permitir HTML nos campos:** ativado

**Codificação:** UTF-8

---

# REGRA FINAL

O padrão visual e técnico deve ser:

**Frente:** questão completa + todas as alternativas.

**Verso:** gabarito + resolução passo a passo + bizu.

**Matemática:** MathJax.

**Negrito:** HTML `<b>`.

**Código:** bloco monoespaçado completo.

**Separador:** TAB.

**Uma linha física por card.**

**Exatamente 2 campos por card.**

**Somente questões erradas válidas.**

Antes de entregar, valide o arquivo para garantir que nenhum card esteja vazio, incompleto, truncado ou dividido incorretamente.