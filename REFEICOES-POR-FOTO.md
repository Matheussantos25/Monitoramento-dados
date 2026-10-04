# Refeições por foto — Solem 0.10.0

Site e Android oferecem **Saúde → Alimentação → Registrar refeição por foto**. Uma foto produz apenas uma sugestão: o usuário revisa alimentos, preparo e porções, confirma e salva no diário privado existente. A imagem não é salva no Supabase Storage nem em `solem_health_entries`.

## Ativação sem cobrança de API

1. No [Google AI Studio](https://aistudio.google.com/apikey), crie pessoalmente uma chave em um projeto **Free**, sem conta de faturamento vinculada. Não publique nem envie a chave no chat. Verifique a classificação e as cotas reais do projeto no AI Studio; a disponibilidade gratuita pode mudar.
2. No [Supabase → Edge Functions → Secrets](https://supabase.com/dashboard/project/frxgrkgljsepykhutskq/functions/secrets), configure:
   - `GEMINI_API_KEY`: sua chave, somente aqui no servidor.
   - `GEMINI_FREE_TIER_CONFIRMED`: `true`, somente após confirmar o projeto gratuito sem faturamento.
   - `GEMINI_MEAL_MODEL`: `gemini-3.8-flash` (padrão). `gemini-2.5-flash` também é aceito; confirme a disponibilidade gratuita no projeto antes de trocar.
3. A migração `supabase/migrations/20261004_meal_analysis_budget.sql` e a função `meal-analysis` precisam estar publicadas no **mesmo** Supabase do site. Não há outro banco.
4. Entre no Solem, envie uma foto somente do prato, aceite o aviso e declare ter 18 anos ou mais. Confira a sugestão antes de salvar. Se a chave não estiver configurada, a interface mostra essa pendência sem impedir o registro manual.

Não habilite faturamento para contornar uma cota. O app não configura cartão, não faz grounding, não usa cache pago, não alterna provedores e não repete automaticamente chamadas de reconhecimento. **A configuração do projeto Google é que garante não haver cobrança; o código não consegue verificar nem impedir que um administrador habilite faturamento depois.** Não há garantia de gratuidade permanente de serviços externos, e os limites gratuitos do Supabase também continuam aplicáveis.

## Publicação e desenvolvimento

Via Supabase CLI autenticado, a partir da raiz do repositório:

```powershell
supabase functions deploy meal-analysis --project-ref frxgrkgljsepykhutskq
```

`supabase/config.toml` desliga somente a verificação da assinatura JWT **legada** no gateway; a própria função exige um Bearer e valida a sessão com `/auth/v1/user` antes de qualquer processamento. Isso suporta sessões com chaves assimétricas. Anon/public key sozinha não autoriza reconhecimento. Não se usa `service_role`. Pelo editor do dashboard, publique o conteúdo de `index.ts` com os arquivos importados `core.mjs` e `nutrition_catalog.json`; uma versão unificada equivalente também pode ser gerada juntando o catálogo como `const catalog = ...`, o módulo de regras e o handler sem as linhas `import`.

O site usa o cliente privado autenticado já existente. O APK usa a mesma URL e chave pública existentes, não precisa de chave Gemini em `local.properties`. O novo debug é `android-app/app/build/outputs/apk/debug/app-debug.apk`, versão 0.10.0. Não foi criada assinatura release; siga o README Android para keystore próprio.

## Privacidade e limites

- JPG, PNG e WebP até 8 MB/20 megapixels. Clientes redimensionam e re-encodificam JPEG, descartando EXIF/localização antes do envio. O servidor rejeita JPEG com EXIF/IPTC ou dimensões acima do limite. Sem câmera automática; Android usa seletor de arquivo/foto. No site há câmera opcional, acionada pelo usuário.
- A foto e o catálogo vão ao Google, **não** e-mail, ID da conta, peso, histórico de saúde ou localização. O Google recebe metadados da conexão do servidor e pode reter/revisar entradas e saídas nos termos do serviço gratuito. Remover EXIF não anonimiza rostos, documentos ou textos visíveis; não envie imagens com essas informações. A detecção posterior pelo modelo é uma proteção adicional, não garantia de anonimato antes do envio.
- O aviso e a declaração de maioridade são obrigatórios. Não é monitoramento médico, diagnóstico ou recomendação nutricional.
- Por conta: 6 tentativas/dia UTC e intervalo mínimo de 30 segundos. Por aplicativo: 20 tentativas/dia UTC. O Google pode impor cota menor. Tentativas que chegam ao Google também consomem reserva mesmo quando falham; isso evita tempestades de repetição.
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

Os testes cobrem cálculos, catálogo idêntico, nutrientes parciais, porções inválidas, EXIF removido, consentimento antes do envio, respostas seguras, edição e confirmação antes de salvar. Reconhecimento real exige a chave e teste com fotos consentidas; testes de unidade não demonstram acurácia nutricional.
