# Entrada por voz (site e APK 0.17.0)

Em Saúde → Alimentação → Registrar alimentos com balança, abra **Preencher por
voz**, toque em **Falar** e dite a lista inteira. Exemplo:

> Almoço, arroz 170, feijão 323, ovo cozido 371, peso acumulado.

Confira a transcrição e corrija o texto se necessário. O resultado mostra 170 g
de arroz, 153 g de feijão e 48 g de ovo. **Preencher campos** substitui apenas o
rascunho da refeição nova. Revise referências de preparo, horário, ordem e pesos;
marque a confirmação e só então salve. O APK tem o botão **Conferir o que
entendeu** antes de preencher. Nenhum reconhecimento salva automaticamente.

O modo acumulado é o padrão e pressupõe prato tarado (leitura inicial 0 g).
Pode dizer “individual” no começo ou no fim para informar porções individuais.
Nomes reconhecidos são os nomes simplificados do catálogo; alimento desconhecido,
leitura faltante ou sequência decrescente exige correção. Repetições do mesmo
alimento são permitidas como adições separadas. Use gramas; não são inferidas
porções por unidade, colheres ou imagens. Refeições já salvas não são alteradas.

Outros formulários:

- Peso: “peso 67 vírgula 5 quilos”.
- Sono: “dormi às 3 e acordei às 13:30, na mesma data”. Use formato de 24 horas.
- Treino isolado: “agachamento, 3 séries de 20, descanso de 60 segundos”.
  Preenche 60 repetições totais. Cardio: “caminhada, 30 minutos, 2 quilômetros”.

A data é sempre a selecionada no formulário. Não há comandos para excluir,
salvar, navegar nem executar instruções contidas na fala. A interpretação usa
regras locais, sem IA remota, e rejeita campos que não pertencem ao exercício.

## Reconhecimento e privacidade

Não há API paga, chave de API nem modelo grande incorporado ao app. O site usa
Web Speech quando disponível. O APK abre o reconhecedor de voz instalado no
Android por `RecognizerIntent.ACTION_RECOGNIZE_SPEECH`; não grava áudio em
segundo plano nem requer uma nova permissão de gravação própria. O provedor de
voz do navegador/celular pode processar áudio remotamente e exigir internet.
Não se promete modo offline. O Solem recebe texto e não armazena o áudio.

Quando o navegador não oferece reconhecimento ou o microfone está bloqueado,
use o microfone do teclado no campo “O que você falou” ou digite. Não é necessário
um reboot do servidor ou configurar Secrets. Documentação dos provedores:
[Web Speech](https://developer.mozilla.org/en-US/docs/Web/API/SpeechRecognition)
e [Android](https://developer.android.com/reference/android/speech/RecognizerIntent).

## Validação

`tests/test_voice.py` verifica interpretação, rejeições, pré-preenchimento,
correção manual, troca de rascunho e ausência de salvamento automático. Os testes
de interface usam demonstração, nunca o banco real. `VoiceDraftTest.kt` cobre as
mesmas frases e cálculos no Android. `node --test tests/test_voice_component.cjs`
simula o reconhecedor e verifica início por clique, conclusão, erro de permissão
e saída da página. Esses testes não medem a qualidade de transcrição real do
microfone do usuário; isso depende do dispositivo, ambiente e provedor.
