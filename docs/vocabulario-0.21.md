# Solem 0.21 — vocabulário para Anki

Em Idiomas → Vocabulário → Anki, capture uma palavra em inglês, procure o sentido usado na cena e revise a frase, o significado e uma imagem antes de salvar ou copiar. É possível salvar só a palavra para completar depois. Os exemplos vêm do dicionário; quando não existem, o formulário pede uma frase do usuário. As formas flexionadas fornecidas pelo dicionário também recebem negrito.

## Dados e privacidade

- Notas privadas existentes em `solem_items`, prefixo `SOLEM_VOCAB_V1`, versão JSON compartilhada entre Python e Kotlin. Nenhuma migração nem alteração dos registros de treino, refeições ou estudo.
- Edição com revisão otimista; exclusão recuperável pela lixeira. Notas de vocabulário ficam no próprio caderno, sem expor JSON na aba Anotações.
- Consultas explícitas enviam apenas a palavra ao FreeDictionaryAPI.com e o termo da busca ao Wikimedia Commons. Frase, contexto e histórico não são enviados a esses serviços. Sem chave nem API paga. A disponibilidade e os limites dos serviços gratuitos podem variar.
- O caderno utiliza a sessão autenticada e as mesmas políticas por usuário da biblioteca privada. A troca de conta já limpa os rascunhos da sessão.
- Salvar/copiar/exportar não altera o número de cards adicionados ao Anki, minutos estudados ou XP.

## Fontes e licenças

Definições e exemplos: [FreeDictionaryAPI.com](https://freedictionaryapi.com/), dados do [Wiktionary](https://en.wiktionary.org/) sob [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). A página original, o provedor e a licença são preservados no verso. O texto pode ser revisado pelo usuário.

Imagens: Wikimedia Commons, somente JPEG/PNG com licença identificada, miniatura de 480 px e créditos de autor/licença/página original. A pessoa escolhe uma imagem que corresponde ao significado; palavras abstratas ou ambíguas podem não ter resultado útil. Não usamos um gerador de imagens.

## Levar ao Anki

- Copiar frente/verso usa HTML para preservar negrito. Dependendo do aplicativo de destino, a formatação pode ser removida ao colar; confira a prévia.
- Imagem copiada como link depende da conexão. O ZIP exportado inclui `card.txt` (UTF-8, tabulação, HTML), arquivo da imagem e instruções para importar no Anki para computador e sincronizar.
- Extraia o ZIP, copie a imagem de `media/` para `collection.media` do perfil e importe `card.txt` como Básico com campos Front/Back e HTML. O ZIP **não é um pacote .apkg**. O aplicativo não grava diretamente no Anki e não tem acesso à conta do Anki.
- A importação deve ser conferida no Anki, inclusive a opção para duplicatas. Exportar novamente uma frase modificada pode gerar outro card conforme as opções de importação.

Referência: [Importação de texto e imagens no Anki](https://docs.ankiweb.net/importing/text-files.html).

## Validação

- Testes Python: nota versionada, texto hostil escapado, negrito e flexões, exportação com imagem local/aspas/tabulações, ausência de exemplo, indisponibilidade do serviço, criar/editar/lixeira/restaurar no Streamlit.
- Testes Kotlin: compatibilidade do documento privado, HTML seguro, negrito/flexões, rascunhos incompletos, hosts de imagem, exportação.
- Verificação ao vivo dos provedores com palavras públicas; revisão visual em demonstração isolada. Nenhum registro fictício salvo na conta principal.
- APK usa a assinatura existente. A interface nativa precisa de validação final no aparelho do usuário; não foi executada em um Galaxy físico nesta entrega.
