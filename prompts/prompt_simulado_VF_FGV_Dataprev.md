# Prompt — Simulado FGV (Formato Certo/Errado) — Analista TI-Inteligência da Informação (DATAPREV)

Aja como um Examinador Sênior e Especialista na elaboração de provas de alto nível, com domínio do estilo conceitual da banca FGV (Fundação Getulio Vargas), adaptado ao formato de julgamento **CERTO ou ERRADO** (Verdadeiro ou Falso), no padrão utilizado por bancas como CESPE/CEBRASPE.

Sua tarefa é elaborar um simulado completo e inédito para o cargo de **Analista de Tecnologia da Informação – Inteligência da Informação** da DATAPREV (Nível Superior). O nível de dificuldade deve ser **EXTREMAMENTE ALTO**, mantendo o rigor conceitual e a densidade de contextualização típicos da FGV, mas no formato de itens julgáveis.

## Diretrizes de Formato e Dificuldade

1. **Estrutura do item:** Cada questão NÃO tem alternativas A-E. É um item único — uma assertiva que o candidato julga como **C (Certo)** ou **E (Errado)**. Nunca apresente opções de resposta.

2. **Extensão das assertivas:** Cada item deve ter entre 150 e 300 caracteres, condensando contexto e afirmação em uma ou duas frases curtas. A redação deve ser objetiva e inequívoca — nada de duplo sentido ou ambiguidade proposital (a pegadinha deve estar no conteúdo técnico, nunca na interpretação do enunciado).

3. **Textos-base (blocos de itens):** Para Português e Inglês, use textos-base densos (até 3000 caracteres). A partir de cada texto, gere um bloco numerado no formato "Com base no texto acima, julgue os itens a seguir", com cada item avaliado de forma independente.

4. **Erros sutis (pegadinhas):** Itens ERRADOS devem conter uma falha plausível e sutil — uma palavra trocada, uma condição lógica invertida, um sinal de operação errado, uma citação incorreta de artigo de lei, um parâmetro de função/método inexistente, um erro de cálculo numa etapa intermediária de uma conta. Evite erros grosseiros ou óbvios.

5. **Proporção C/E:** Busque algo próximo de 50% Certo / 50% Errado por bloco temático, sem alternância previsível (nada de C-E-C-E-C-E).

6. **Formatação técnica rigorosa:**
   - Matemática e Estatística: use estritamente LaTeX para equações, matrizes de covariância, integrais e derivadas.
   - Ciência de Dados e BD: insira blocos de código reais (Python, Pandas, R, SQL) e faça o item depender do candidato "tracear" o código mentalmente (prever output, métrica de avaliação ou erro) antes de julgar C/E.

7. **Sem gabarito antecipado:** Não informe se um item é C ou E durante a geração. Ao final de cada bloco solicitado, pergunte se deve prosseguir. O gabarito comentado só deve ser fornecido quando explicitamente pedido.

## Estrutura do Simulado (Total de 70 Itens)

**Módulo I – Conhecimentos Gerais (Itens 01 a 40)**
- Língua Portuguesa: 12 itens (01–12) — 2 blocos de leitura, 2 textos-base, 6 itens cada
- Língua Inglesa: 12 itens (13–24) — 2 blocos de leitura, 2 textos-base, 6 itens cada
- Raciocínio Lógico-Matemático: 6 itens (25–30) — assertivas independentes
- Atualidades e IA: 5 itens (31–35) — assertivas independentes
- Legislação (Segurança/Proteção de Dados): 5 itens (36–40) — assertivas independentes, com referência a artigos específicos das leis

**Módulo II – Conhecimentos Específicos (Itens 41 a 70)**
- 30 itens sobre Cálculo, Álgebra Linear, Estatística Multidimensional, Machine Learning, Redes Neurais, PLN, Hadoop/Spark e Modelagem de Dados. Vários itens devem exigir trace de código ou cálculo antes do julgamento C/E.

## Dinâmica de Execução

Como o simulado é longo, gere em dois blocos para não perder densidade.

**Ação imediata:** gere agora APENAS o Módulo I (itens 01 a 40). Não forneça gabarito. Ao terminar, pergunte se pode prosseguir para o Módulo II.

## Assunto do Edital

MATEMÁTICA E ESTATÍSTICA APLICADA: I MATEMÁTICA: 1 Cálculo: Funções. Limites. Derivadas. Derivadas
Parciais. Máximos e mínimos. Integrais. 2 Álgebra linear: Notação de vetores e matrizes. Produto escalar e
produto vetorial. Matriz identidade, inversa e transposta. Transformações lineares. Normas L1 e L2.
Autovalores e autovetores. II ESTATÍSTICA: 1 Conceitos de probabilidade. Modelo de probabilidade.
Probabilidade condicional. Independência. Variáveis aleatórias. Esperança, variância e covariância.
Distribuições contínuas e discretas. Distribuições multidimensionais: matriz de covariância. 2 Estatísticas
descritivas. Teorema do Limite Central. Teste de hipótese e intervalo de confiança. Estimador de máxima
verossimilhança. Inferência bayesiana. Coeficiente de correlação de Pearson. Diagrama boxplot e avaliação de
outliers.

CIÊNCIA DE DADOS: 1 Aprendizado supervisionado: Regressão e Classificação. Métricas de avaliação.
Overfitting e underfitting de modelos. Regularização. Seleção de modelos. Validação cruzada. Conjunto de
treino, validação e teste. Trade off entre variância e viés. Regressão Linear e Regressão Logística. Árvores de
Decisão e random forests. SVM. K-NN. 2 Aprendizado não-supervisionado: Redução de dimensionalidade: PCA.
K-Means. Mistura de Gaussianas. Regras de Associação. 3 Redes neurais artificiais: Definições e arquitetura.
Funções de ativação. Otimização: método do gradiente, método do gradiente estocástico e backpropagation.
Métodos de regularização: penalização com normas L1 e L2. CNN. 4 Machine Learning aplicado. Noções de
visão computacional com CNN. Classificação de imagens e detecção de objetos. Noções de processamento de
linguagem natural. 5 ETL. 6 Manipulação, tratamento e visualização de dados. 7 Inteligência artificial. 7.1
Análise de dados (Pandas, NumPy, Jupiter, R). 7.2 Aprendizado de máquina. 7.2.1 Técnicas de classificação.
7.2.2 Técnicas de regressão. 7.2.3 Técnicas de agrupamento. 7.2.4 Técnicas de redução de dimensionalidade.
7.2.5 Técnicas de associação. 7.2.6 Sistemas de recomendação. 8 Processamento de linguagem natural (PLN).
9 Visão computacional. 10 Deep learning. 11 Mineração de Dados. 12 Ferramenta SAS.

LINGUAGENS DE PROGRAMAÇÃO E SOFTWARES EM CIÊNCIAS DE DADOS: 1 Python e suas bibliotecas:
Numpy, Matplotlib, Seaborn, Streamlit, Pandas, Scipy, TensorFlow, Keras e Pytorch. 2 R e suas bibliotecas. 3
Apache Hadoop e Apache Spark.

BANCO DE DADOS: 1 Modelagem de dados (conceitual, lógica e física). 2 Abordagem relacional. 3
Normalização das estruturas de dados. 4 Integridade referencial. 5 Metadados. 6 Modelagem dimensional. 7
Linguagem de consulta estruturada (SQL). 8 Linguagem de definição de dados (DDL). 9 Linguagem de
manipulação de dados (DML). 10 SGBD. 11 Propriedades de banco de dados. 12 Banco de dados NoSQL. 13
Banco de dados em memória. 14 Data lakes e soluções para big data.

### MÓDULO I - CONHECIMENTOS GERAIS (PARA TODOS OS CARGOS/PERFIS)

LÍNGUA PORTUGUESA: 1 Compreensão e interpretação de textos de gêneros variados. 2 Reconhecimento de
tipos e gêneros textuais. 3 Domínio da ortografia oficial. 4 Domínio dos mecanismos de coesão textual. 4.1
Emprego de elementos de referenciação, substituição e repetição, de conectores e de outros elementos de
sequenciação textual. 4.2 Emprego de tempos e modos verbais. 5 Domínio da estrutura morfossintática do
período. 5.1 Emprego das classes de palavras. 5.2 Relações de coordenação entre orações e entre termos da
oração. 5.3 Relações de subordinação entre orações e entre termos da oração. 5.4 Emprego dos sinais de
pontuação. 5.5 Concordância verbal e nominal. 5.6 Regência verbal e nominal. 5.7 Emprego do sinal indicativo
de crase. 5.8 Colocação dos pronomes átonos. 6 Reescrita de frases e parágrafos do texto. 6.1 Significação das
palavras. 6.2 Substituição de palavras ou de trechos de texto. 6.3 Reorganização da estrutura de orações e de
períodos do texto. 6.4 Reescrita de textos de diferentes gêneros e níveis de formalidade.

LÍNGUA INGLESA: 1 Compreensão de textos em língua inglesa e itens gramaticais relevantes para o
entendimento dos sentidos dos textos.

RACIOCÍNIO LÓGICO: 1 Estruturas lógicas. 2 Lógica de argumentação: analogias, inferências, deduções e
conclusões. 3 Lógica sentencial (ou proposicional). 3.1 Proposições simples e compostas. 3.2 Tabelas-verdade.
3.3 Equivalências. 3.4 Diagramas lógicos. 4 Lógica de primeira ordem. 5 Raciocínio lógico envolvendo
problemas aritméticos, geométricos e matriciais

ATUALIDADES E INTELIGÊNCIA ARTIFICIAL: 1 Tópicos relevantes e atuais de diversas áreas, tais como
segurança, transportes, política, economia, sociedade, educação, saúde, cultura, tecnologia, energia, relações
internacionais, desenvolvimento sustentável e ecologia. 2 Inteligência Artificial: fundamentos e aplicações:
conceitos de inteligência artificial; aprendizado da máquina; introdução aos modelos generativos e modelos
de linguagem; ética, governança e privacidade em IA.

LEGISLAÇÃO ACERCA DE SEGURANÇA DA INFORMAÇÃO E PROTEÇÃO DE DADOS: 1 Lei nº 12.527/2011 (Lei
de Acesso à Informação): capítulos I, II, III, IV e V; Dec. nº 7.724 e nº 7845. 2 Lei nº 12.737/2012 (Lei de Delitos
Informáticos): art. 2º. 3 Lei nº 12.965/2014 (Marco Civil da Internet): capítulos II, Seção I, e III, Seções I e II. 4
Lei nº 13.709/2018 (Lei Geral de Proteção de Dados Pessoais – LGPD): capítulos I, II, III, IV, VII, VIII
