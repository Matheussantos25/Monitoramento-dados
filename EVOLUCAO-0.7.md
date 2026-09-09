# Solem 0.7 — acesso antes do painel

- Site e Android agora exibem o login antes de carregar o painel.
- A opção Login foi removida dos menus.
- Depois da autenticação, a entrada acontece diretamente pela Visão geral.
- O cabeçalho horizontal duplicado foi removido do site; a marca permanece no menu lateral.
- A ação Sair fica no fim do menu lateral e volta para a tela de acesso.
- O Android salva a sessão de forma local e tenta restaurá-la e renová-la ao abrir o aplicativo.
- Se a sessão expirar, o conteúdo protegido deixa de ser exibido e o acesso volta para a tela inicial.

O projeto continua usando Supabase Auth e as políticas RLS já ativadas. Nenhuma credencial administrativa é incluída no site ou no APK.

O APK de teste é debug, versão 0.7.0, código 7. Para distribuição definitiva, gere uma versão release assinada com um keystore privado, conforme o README Android.
