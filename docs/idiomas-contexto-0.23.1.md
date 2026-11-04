# Solem 0.23.1 · Próximo episódio

Ao confirmar uma nova sessão, site e Android mantêm atividade, idioma, fonte, título, tipo de conteúdo, idioma do áudio e legendas. Duração, contagem e observações são de uma nova sessão; editar registros antigos não muda esse contexto. A memória pertence ao formulário da sessão autenticada, sem regravar histórico nem alterar o banco.

No Android, o contexto é atualizado com os dados validados somente no retorno de sucesso do salvamento e sobrevive à recriação do formulário. No site, áudio e legendas passam a ter chaves próprias por atividade e geração do formulário.

Validação: 28 testes Python, incluindo duas gravações consecutivas de Escuta mantendo as seleções e preservando o registro anterior. Build Android e testes JVM concluídos; teste de contexto cobre serialização e nova sessão sem copiar contagens/observações. Não foi testado em aparelho físico.
