# GPS Android — 0.14.2

Correção restrita ao APK. Não altera Supabase, registros existentes, autenticação
ou o rastreador do navegador. Instalar a atualização sobre a versão anterior,
sem desinstalar o aplicativo.

## Comportamento

- Serviço de localização em primeiro plano iniciado pelo usuário, agora com
  `START_STICKY`. O Android pode tentar recriá-lo após encerrar o processo; isso
  não garante sobrevivência a força de parada, reinício do aparelho ou restrições
  do fabricante. O usuário pode retomar o rascunho pelo aplicativo.
- Distância, duração e identificador da sessão são gravados em armazenamento
  privado por conta a cada incremento. Não são gravados pontos, coordenadas ou
  trajetos. O manifesto já desabilita backup. Falha de gravação aparece na tela.
- Apenas localização GPS precisa, intervalo solicitado de 2 segundos, distância
  mínima de atualização zero. Assim pontos estacionários comprovam que ainda há
  sinal; deixar de se mover não gera alerta falso por ausência de callbacks.
- Descarta precisão pior que 35 m, pontos antigos, futuros, fora de ordem,
  coordenadas inválidas e saltos incompatíveis com caminhada/corrida (>8 m/s).
  O ponto rejeitado não substitui a âncora válida.
- Deslocamentos menores que o limiar acumulam a partir da última âncora, em vez
  de serem esquecidos a cada callback. Não se intercala localização de rede.
- Mais de 30 segundos sem ponto utilizável: aviso de sinal perdido, preservando
  o total. GPS desligado tem aviso próprio. O watchdog verifica a cada 5 segundos
  enquanto o processo executa; suspensão do processo pode atrasar o aviso.
- Ao voltar o sinal, começa um segmento novo. Não liga extremos de um intervalo
  perdido por uma reta e não inventa quilômetros. O aviso de trecho incompleto
  continua visível mesmo depois de recuperar o sinal.
- A notificação informa o estado; é necessário autorizar notificações para vê-la
  na tela bloqueada. Não promete alarme sonoro. A tela mostra o último sinal.
- Após interrupção: Retomar GPS ou Encerrar e usar distância recuperada. Após
  encerramento: Usar medição guardada. O usuário ainda revisa e salva o treino;
  não há criação automática de registros. Nova medição substitui o rascunho
  anterior, mas não registros salvos. Cada conta só acessa seu próprio rascunho.
- Duração usa relógio monotônico; após reboot conserva duração do checkpoint,
  sem subtrair relógios de boots diferentes. Retomada não reconstrói tempo ou
  distância desconhecidos. O rascunho protege medições feitas nesta versão;
  não recupera distâncias que versões anteriores já perderam.

## Validação

Testes JVM de caminhada contínua, passos pequenos, parada, sinal perdido,
retomada, saltos, precisão ruim, pontos fora de ordem, reinício de processo,
reboot, serialização sem coordenadas e persistência/isolamento entre contas.

Teste de campo pendente no Galaxy A56 5G: iniciar ao ar livre com localização
precisa; caminhar com tela ligada e bloqueada; alternar aplicativos; desligar a
localização por mais de 30 segundos e religar; confirmar total preservado, aviso
e retomada. Conferir também notificação e recuperação após encerramento do
processo. Sem aparelho conectado, os testes JVM não comprovam comportamento do
firmware Samsung nem precisão real do percurso.

Referências de implementação:
- https://developer.android.com/reference/android/app/Service#START_STICKY
- https://developer.android.com/reference/android/location/LocationManager
- https://developer.android.com/reference/android/location/LocationListener
