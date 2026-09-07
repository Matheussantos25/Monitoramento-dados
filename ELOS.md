# Elos pessoais — 0.4

Site: painel Sua jornada ranqueada na Visão geral. Android: menu Elos.

As regras estão em solem_ranks.py e domain/Ranks.kt. São gamificação pessoal, não o algoritmo competitivo Elo. Nenhuma tabela ou permissão foi alterada.

Físico: soma das repetições totais já salvas, sem multiplicar séries. Faixas: 0, 100, 500, 1500, 3500, 7000, 12000 e 20000. Nomes: Ferro, Bronze, Prata, Ouro, Platina, Esmeralda, Diamante e Mestre. Descanso não reduz pontuação. Cardio/isometria continuam no calendário e XP.

Estudo: cada tópico literal do edital tem um elo independente. Colocação exige 20 questões. As faixas de acerto são 0/40/50/60/70/80/90/95%, com amostras mínimas 20/20/30/40/60/80/120/200. Usa todo o histórico válido e exclui Anki, datas futuras e registros duplicados por ID. Sessões com temas genéricos ou múltiplos tópicos não são distribuídas artificialmente. Tópicos contendo vírgulas são reconhecidos por correspondência completa, não por divisão de texto.

Som e animação são opcionais, desligados inicialmente. Site detecta promoções durante a sessão; Android enquanto a tela de elos permanece aberta. Não há notificação offline nem histórico persistente de promoções. Navegadores podem bloquear autoplay. Editar registros recalcula o elo, mas reverter uma edição não repete uma promoção já celebrada na mesma sessão/tela.

Biblioteca privada, PDFs, mapas mentais, cronograma editável e investimentos continuam pendentes; não foram implementados nesta entrega. Dependem também da preparação de Auth/tabelas/Storage privados. O módulo existente treinos e suas permissões não foram alterados.
