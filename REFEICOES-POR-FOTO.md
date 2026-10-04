# Refeições: reconhecimento por API removido

A opção de analisar fotos de comida por Gemini/OpenRouter foi retirada do site e do Android 0.10.2 a pedido do usuário. Não há reconhecimento local implementado neste momento.

- A função meal-analysis agora retorna HTTP 410 (feature_removed), inclusive para APKs antigos. Não lê imagens, não consulta credenciais e não chama provedores.
- Registro manual de alimentação, histórico, edição e cálculos nutricionais dos registros existentes foram preservados.
- O catálogo USDA é um arquivo local; calcular os valores não faz requisições à USDA nem a serviços de IA.
- Fotos de evolução facial/corporal são uma funcionalidade separada e permanecem disponíveis.
- Não execute migrações novas. Os contadores da antiga análise e os registros de saúde não são apagados.
- Chaves OpenRouter existentes não são revogadas nem alteradas. A função retirada não as utiliza; outros usos da conta OpenRouter não são afetados.

## Alternativa sem API

No Android, um modelo treinado especificamente para alimentos pode executar no próprio celular com LiteRT, sem cobrança por foto. Isso exige selecionar/licenciar o modelo, validar os alimentos suportados e medir tamanho, desempenho e qualidade antes de integrar. Não basta usar um classificador genérico de imagens.

Para pratos mistos, a identificação pode falhar e deve ser apresentada como sugestão para o usuário confirmar. Fotos não medem gramas nem revelam óleo, molhos ou ingredientes ocultos. Calorias e macronutrientes exigem uma porção informada/estimada e uma referência nutricional, com incerteza explícita.

No site, executar o modelo no navegador é uma possibilidade distinta, que exige integração e testes nos dispositivos. Executá-lo no servidor não tem custo de API, mas consome memória e CPU da hospedagem; portanto não garante custo total zero.

Para a versão atual, a alternativa mais simples e previsível é selecionar alimentos habituais e porções manualmente. Não apresentamos reconhecimento inexistente nem números nutricionais como medições exatas.

## Verificação

- Python: python -m pytest -q. Cálculos locais, preservação/edição do histórico e ausência da integração nos clientes.
- Node: node tools/test_meal_analysis.mjs. Endpoint aposentado e cálculo determinístico, sem chamadas de rede.
- Android: ./gradlew :app:testDebugUnitTest :app:assembleDebug.
- Publicação: atualizar a função com index.ts + retired.mjs; o handler deve retornar 410 sem chamar fetch, mesmo recebendo a ação antiga recognize.
