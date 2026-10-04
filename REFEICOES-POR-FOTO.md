# Refeições por foto — Solem 0.10.1 / OpenRouter

Site e Android oferecem **Saúde → Alimentação → Registrar refeição por foto**. Uma foto produz apenas uma sugestão: o usuário revisa alimentos, preparo e porções, confirma e salva no diário privado existente. A imagem não é salva no Supabase Storage nem em `solem_health_entries`.

## Ativação com teto de US$ 1 por mês

1. Em [OpenRouter → API Keys](https://openrouter.ai/settings/keys), crie pessoalmente uma chave **exclusiva do Solem**, não de gerenciamento, chamada por exemplo `Solem-refeicoes`. Configure **Credit limit = 1 USD**, **Limit reset = Monthly** e **Include BYOK in limit = ativado**. A conta já tem saldo: não é necessário comprar créditos novos nem cadastrar chave/faturamento separado do Google. Não envie a chave no chat, não compartilhe e não use essa chave em outros apps.
2. Em [Supabase → Edge Functions → Secrets](https://supabase.com/dashboard/project/frxgrkgljsepykhutskq/functions/secrets), adicione `OPENROUTER_API_KEY` com a chave criada. Nenhuma chave vai para o Streamlit Secrets, `local.properties` ou APK. Não se usam mais `GEMINI_API_KEY`, `GEMINI_FREE_TIER_CONFIRMED` ou `GEMINI_MEAL_MODEL`.
3. Modelo fixo `google/gemini-2.5-flash`, servido por Google Vertex através do OpenRouter. Não use BYOK/chaves próprias do Google na sua conta OpenRouter para esse recurso: o fluxo deve usar somente seus créditos OpenRouter. `Include BYOK` é uma proteção adicional para o limite, não uma instrução para cadastrar outro provedor.
4. A migração `supabase/migrations/20261004_meal_analysis_budget.sql` já foi aplicada no **mesmo** Supabase do site; não execute outra migração para trocar de provedor. Publique a versão atual da função `meal-analysis` e atualize o site/APK. Não há outro banco e não se alteram registros existentes.
5. Entre no Solem, envie somente o prato, aceite o novo aviso e declare ter 18 anos ou mais. Confira a sugestão antes de salvar. O APK antigo 0.10.0 é bloqueado pelo consentimento v2, pois não autorizava OpenRouter. Sem chave ou limite correto, o registro manual continua disponível.

O serviço é **pago com o saldo já existente**, não gratuito. O teto de US$ 1/mês vale para o aplicativo inteiro, site e Android juntos, não US$ 1 por usuário. Antes de **cada** reconhecimento, o servidor consulta [GET /api/v1/key](https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key) e recusa chaves sem limite, acima de US$ 1, com renovação não mensal, de gerenciamento, sem contagem BYOK ou com configuração incompleta. Com margem menor que US$ 0,02, bloqueia a próxima análise. O bloqueio de gasto efetivo, inclusive concorrência, é o limite nativo da chave no OpenRouter, não um contador visual do app. Falha ao conferir a chave também bloqueia o envio da imagem, sem fallback.

Não ative recarga automática para esse recurso. Não substitua a chave por outra durante o mês para contornar o limite: uma nova chave pode ter um contador novo no provedor. Administradores podem alterar credenciais/políticas fora do app; a configuração nativa deve permanecer limitada. Preços, disponibilidade e comportamento de cobrança são controlados pelo OpenRouter. Não há compra automática, grounding, ferramentas, plugins, cache explícito ou chamadas de reconhecimento repetidas. O pedido usa no máximo 1536 tokens de saída, raciocínio desligado, um único modelo e teto de US$ 0,30/M de entrada e US$ 2,50/M de saída. Sem endpoint compatível com preço, schema e privacidade, a análise falha com segurança. Não há garantia de quantidade fixa de fotos por dólar. Limites gratuitos do Supabase continuam aplicáveis.

## Publicação e desenvolvimento

Via Supabase CLI autenticado, a partir da raiz do repositório:

```powershell
supabase functions deploy meal-analysis --project-ref frxgrkgljsepykhutskq
```

`supabase/config.toml` desliga somente a verificação da assinatura JWT **legada** no gateway; a própria função exige um Bearer e valida a sessão com `/auth/v1/user` antes de qualquer processamento. Isso suporta sessões com chaves assimétricas. Anon/public key sozinha não autoriza reconhecimento. Não se usa `service_role`. Pelo editor do dashboard, publique `index.ts` e os importados `core.mjs`, `openrouter.mjs` e `nutrition_catalog.json`; uma versão unificada equivalente pode ser gerada juntando catálogo como `const catalog = ...`, os módulos e o handler sem linhas `import`.

O site usa o cliente privado autenticado já existente. O APK usa a mesma URL e chave pública existentes, não precisa de chave OpenRouter em `local.properties`. O novo debug é `android-app/app/build/outputs/apk/debug/app-debug.apk`, versão 0.10.1. Não foi criada assinatura release; siga o README Android para keystore próprio.

## Privacidade e limites

- JPG, PNG e WebP até 8 MB/20 megapixels. Clientes redimensionam e re-encodificam JPEG, descartando EXIF/localização antes do envio. O servidor rejeita JPEG com EXIF/IPTC ou dimensões acima do limite. Sem câmera automática; Android usa seletor de arquivo/foto. No site há câmera opcional, acionada pelo usuário.
- A foto e o catálogo vão ao **OpenRouter e Google Vertex**, não e-mail, ID da conta, peso, histórico de saúde ou localização. O pedido exige `data_collection=deny` e `zdr=true`, somente Google Vertex e sem fallback. Essas opções filtram endpoints conforme as políticas declaradas; não são garantia independente de anonimato nem eliminam processamento/transporte e metadados operacionais. Consulte a [privacidade do OpenRouter](https://openrouter.ai/privacy) e [roteamento ZDR](https://openrouter.ai/docs/guides/routing/provider-selection). Desative logging opcional de inputs/outputs na sua conta OpenRouter. Não criamos arquivo persistente via Files API. Remover EXIF não anonimiza rostos/documentos/textos visíveis; não envie imagens com essas informações. A detecção pelo modelo acontece depois do envio.
- O aviso e a declaração de maioridade são obrigatórios. Não é monitoramento médico, diagnóstico ou recomendação nutricional.
- Por conta: 6 tentativas/dia UTC e intervalo mínimo de 30 segundos. Por aplicativo: 20 tentativas/dia UTC. OpenRouter/provedor podem impor cotas menores; isso não substitui o teto financeiro mensal. Tentativas que passam pela reserva diária contam mesmo quando falham. Chave ausente, limite mensal incorreto ou margem insuficiente são verificados **antes** da reserva e da chamada paga.
- A reserva é atômica em PostgreSQL, com lock de transação. A tabela tem RLS e nenhum acesso direto por `anon`/`authenticated`. A função SECURITY DEFINER usa `auth.uid()`, search path vazio e não aceita identidade nem limite do cliente. Contadores antigos são descartados após dois dias, sem imagens ou resultados associados.
- Requisições têm limite de tamanho e timeout. Erros de chave, cota, rede, sessão, foto inadequada ou resultado inválido são mensagens seguras. Não há logs explícitos com foto, prompt, chave ou respostas do provedor no código; não habilite logs de corpo de requisição nas plataformas.

## Como se calculam os nutrientes

Gemini propõe **alimentos, correspondência de preparo e gramas aproximadas**, não valores nutricionais. Os cálculos usam 24 referências identificadas do **USDA FoodData Central, SR Legacy, abril de 2018**, dados de domínio público [CC0](https://fdc.nal.usda.gov/api-guide/). Dados extraídos do [download oficial](https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_json_2018-04.zip); cada referência inclui ID, descrição original e link da fonte. Valores por 100 g são preservados e multiplicados pela porção confirmada.

O catálogo é inicial e limitado, não uma tabela completa de todas as receitas brasileiras. Feijão cozido em grãos não equivale à concha de caldo; pratos mistos, cuscuz, sopas e receitas sem referência ficam **sem cálculo**, até adicionar uma fonte adequada ou o usuário escolher uma correspondência que represente o preparo. Nenhum alimento desconhecido recebe zero calorias como se fosse um valor conhecido. Totais são explicitamente **parciais** quando há alimentos desconhecidos ou refeições manuais.

São exibidos energia, proteínas, carboidratos, gorduras e fibras, com uma casa decimal. A conta aritmética pode estar correta e a estimativa do prato continuar errada: peso, óleo, molhos e receita não são mensuráveis com precisão por foto. Não há alegação de margem de erro validada. Fonte e porção podem ser alteradas, removidas e complementadas sem novo reconhecimento. Edições recalculam os valores; no site, editar os alimentos pelo formulário manual substitui a análise, com aviso.

O mesmo catálogo está em Python, backend e assets/testes Android. Para ampliar, adicione referências verificadas com o mesmo esquema e atualize as duas cópias Android; o teste de paridade impede divergência silenciosa. Registros salvos preservam itens confirmados, versão da referência e totais, dentro do limite JSON existente de 4096 bytes.

## Verificação

```powershell
python -m pytest -q
node tools/test_meal_analysis.mjs
# Na pasta android-app, com o SDK/caches já configurados no E:
.\gradlew.bat :app:testDebugUnitTest :app:assembleDebug --offline
```

Os testes cobrem cálculos, catálogo idêntico, nutrientes parciais, porções inválidas, EXIF removido, novo consentimento antes do envio, chave mensal restrita, margem insuficiente, falha de reserva, falha do provedor sem retry, schema/privacidade/limites de tokens e edição/confirmar antes de salvar. Não geram cobrança. Reconhecimento real exige a chave e teste com fotos consentidas; testes de unidade não demonstram acurácia nutricional nem auditam o sistema de cobrança do OpenRouter.
