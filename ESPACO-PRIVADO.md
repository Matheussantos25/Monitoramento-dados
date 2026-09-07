# Solem 0.5 — espaço privado e emblemas

## O que foi implementado

- Anotações e resumos: criar, ler, buscar, editar, arquivar e restaurar.
- PDFs: cadastro de título/observações, envio de até 10 MiB e download autenticado. No Android, a exportação usa o seletor de destino do sistema, sem exigir acesso amplo aos arquivos. Não há leitor/anotador de páginas integrado.
- Mapas mentais: editor de estrutura por indentação (2 espaços por nível), até 80 tópicos e 5 níveis. Visualização em grafo no site e árvore no Android; não é um editor de arrastar nós.
- Cronograma: compromissos editáveis, data, horário local, duração e conclusão; filtro mensal. Não há recorrências nem alarmes de fundo nesta versão.
- Investimentos: posições manuais em reais, total aplicado, saldo informado e data de referência; totais da lista filtrada e diferença nominal. Não conecta corretoras, não negocia ativos e não busca cotações.
- Emblemas vetoriais originais com asas/cristal para os 8 elos existentes, a partir da mesma geometria no site e Android. Não são arquivos oficiais do LoL.
- Removido o bloco Detalhes do dia, preservando o calendário e os registros.

## Ativação necessária no mesmo Supabase

O código pode ser publicado antes da migração: o app explica a configuração ausente. Os novos módulos não poderão salvar até que a ativação seja concluída. Nenhuma migração foi aplicada ao projeto remoto nesta entrega, por falta de acesso administrativo nesta sessão.

1. Faça backup pelo processo usual do seu projeto. Abra o **SQL Editor do mesmo Supabase usado pelo Streamlit**.
2. Revise e execute **uma vez** `supabase/migrations/20260907_personal_workspace.sql`. O script é transacional e cria `public.solem_items`, o bucket privado `solem-documents`, validações e políticas. Se o nome já existir, ele falha sem sobrescrever dados; não contorne a falha apagando tabelas/buckets.
3. Nos Secrets do Streamlit, mantenha as configurações antigas e acrescente `SUPABASE_PUBLISHABLE_KEY` com a chave pública do projeto. Uma chave antiga `anon` em `SUPABASE_KEY` também é aceita, mas `service_role`/`sb_secret_` são recusadas pelo módulo privado. Não copie uma chave administrativa para o APK.
4. Em Authentication, confira se o provedor Email permite o fluxo desejado. Use uma conta existente ou crie sua conta pelo espaço privado e confirme o e-mail se solicitado. Nenhuma configuração de Auth foi alterada automaticamente. O redirecionamento de confirmação usa a configuração do seu projeto; após confirmar, volte ao Solem para entrar com e-mail/senha. Recuperação de senha é administrada pelo fluxo do seu Supabase, não implementada nesta interface.
5. Abra **Espaço privado** no site e no APK 0.5, usando a mesma conta. Crie uma nota e clique **Atualizar** no outro dispositivo. Edite, arquive e restaure. Faça o mesmo com um PDF pequeno. Valide também que uma segunda conta não vê seus dados.

## Segurança e consistência

- Novo client Auth separado do client legado de treinos. No Streamlit ele pertence à sessão do navegador, nunca a `cache_resource`; Android não persiste os tokens deste módulo em disco. Será necessário entrar novamente após encerrar a sessão/app.
- RLS por `auth.uid()` com proprietário imutável. Não há leitura anônima. Revisões no banco impedem sobrescritas silenciosas quando dois dispositivos editam a mesma versão.
- Restrições no banco validam títulos, datas, duração, valores em centavos e estrutura dos mapas. Os cálculos monetários não usam ponto flutuante para persistência.
- Políticas restritivas adicionais impedem que políticas permissivas antigas de Storage abram o novo bucket. Outros buckets mantêm seu comportamento. PDFs não são sobrescritos nem removidos permanentemente pelos clientes; arquivamento é recuperável.
- PDF: primeiro crie o registro, depois envie o arquivo. Se o upload falhar, o registro permanece e permite tentar novamente. Se a resposta da rede se perdeu, tente baixar antes de reenviar. A validação de assinatura/tamanho não equivale a antivírus; abra apenas PDFs confiáveis.
- Uma cópia baixada/exportada já não está protegida pelo login do Solem. Downloads não são criptografia ponta a ponta.
- Sincronização dos novos módulos por leitura inicial e botão Atualizar. Sem edição offline, fila de sincronização ou Realtime para estes módulos nesta versão. Rascunhos não salvos não têm garantia de recuperação após fechar o app/navegador.
- `treinos` e suas permissões não foram modificados. O novo login **não torna privado o histórico legado**.

## Verificações realizadas

- Testes Python de páginas, regras, mapas, moeda, PDF e proteção contra chave administrativa.
- Build, testes unitários e lint Android.
- Migração executada em PostgreSQL em memória (PGlite), com schemas Auth/Storage simulados: isolamento entre duas contas, anonimato bloqueado, proprietário imutável, conflito de revisão e PDFs inacessíveis após arquivar. Testado inclusive na presença de uma política Storage antiga permissiva.
- Isso não substitui o teste de integração no seu Supabase real: Auth/e-mail, API HTTP de Storage e sincronização entre dispositivos dependem da ativação acima. Não foram testados em um celular físico nesta sessão.

## Desenvolvimento

`tools/build_rank_emblems.py` gera os 8 SVGs e vetores Android a partir dos mesmos caminhos. Execute novamente após editar a geometria. `tools/test_workspace_sql.cjs` usa `@electric-sql/pglite@0.3.14` instalado separadamente apenas para testes (não é dependência do site). Defina `SOLEM_PGLITE_MODULE` com o caminho do pacote se necessário.

APK entregue: debug, versão 0.5.0, código 5. A assinatura release continua dependendo do seu keystore privado e não deve ser versionada. Preserve a assinatura da versão instalada para atualizar sem desinstalar.

Referências do SDK: [Auth Python](https://supabase.com/docs/reference/python/auth-signinwithpassword), [Storage Python](https://supabase.com/docs/reference/python/storage-from-upload), [Storage Kotlin](https://supabase.com/docs/reference/kotlin/storage-from-download).
