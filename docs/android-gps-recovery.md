# GPS Android — 0.18.4

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
- Localização combinada do Google Play Services com prioridade de alta precisão,
  intervalo solicitado de 2 segundos, intervalo mínimo de 1 segundo, sem lote
  intencional nem posição inicial em cache. Sem Play Services disponível, ou se
  a solicitação falhar, usa GPS por satélite. Os dois provedores não são inscritos
  simultaneamente. Pontos estacionários também indicam que há atualizações.
- Descarta precisão pior que 35 m, pontos antigos, futuros, fora de ordem,
  coordenadas inválidas e saltos incompatíveis com caminhada/corrida (>8 m/s).
  O ponto rejeitado não substitui a âncora válida.
- Deslocamentos menores que o limiar acumulam a partir da última âncora, em vez
  de serem esquecidos a cada callback. O provedor combinado continua sujeito aos
  mesmos filtros; não se somam posições imprecisas só para aumentar o total.
- Mais de 30 segundos sem ponto utilizável interrompe o segmento, preservando
  o total. Posições recentes rejeitadas mostram posição imprecisa; ausência de
  posições mostra sinal perdido. GPS desligado tem aviso próprio. O watchdog verifica a cada 5 segundos
  enquanto o processo executa; suspensão do processo pode atrasar o aviso.
- Ao voltar o sinal, começa um segmento novo. Não liga extremos de um intervalo
  perdido por uma reta e não inventa quilômetros. O aviso de trecho incompleto
  continua visível mesmo depois de recuperar o sinal.
- A notificação informa o estado; é necessário autorizar notificações para vê-la
  na tela bloqueada. Não promete alarme sonoro. A tela mostra o último sinal.
- Após 45 segundos sem posição recente, reinscreve o provedor com intervalo
  mínimo de 60 segundos entre tentativas. Posições fracas recentes e paradas
  normais não causam reinscrições. Callbacks de inscrições antigas são ignorados.
- Tela mostra fonte, precisão estimada, idade da posição e tentativas de retomada.
  Ajuda expansível explica as configurações Samsung e oferece atalhos às
  configurações do app e de localização. Não altera permissões nem bateria.
  Diagnósticos são transitórios; rascunhos antigos continuam compatíveis.
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
Testes adicionais distinguem sinal impreciso de silêncio, verificam o intervalo
entre tentativas, uma sequência longa de posições ruins e compatibilidade dos
rascunhos sem persistir os diagnósticos.

Teste de campo pendente no Galaxy A56 5G: iniciar ao ar livre com localização
precisa; caminhar com tela ligada e bloqueada; alternar aplicativos; desligar a
localização por mais de 30 segundos e religar; confirmar total preservado, aviso
e retomada. Conferir também notificação e recuperação após encerramento do
processo. Sem aparelho conectado, os testes JVM não comprovam comportamento do
firmware Samsung nem precisão real do percurso.
Comparar o mesmo trecho na mão com tela ligada, na mão com tela bloqueada e no
bolso com tela bloqueada. Isso ajuda a distinguir recepção de restrição de energia.
Nenhum provedor garante posição dentro do bolso; corpo, obstáculos e capa podem
atenuar o sinal. O app não estima nem inventa a distância de trechos sem posição.

Referências de implementação:
- https://developer.android.com/reference/android/app/Service#START_STICKY
- https://developer.android.com/reference/android/location/LocationManager
- https://developer.android.com/reference/android/location/LocationListener
- https://developers.google.com/android/reference/com/google/android/gms/location/FusedLocationProviderClient
- https://developers.google.com/android/reference/com/google/android/gms/location/LocationRequest.Builder
- https://www.samsung.com/us/support/troubleshoot/TSG10001558/
