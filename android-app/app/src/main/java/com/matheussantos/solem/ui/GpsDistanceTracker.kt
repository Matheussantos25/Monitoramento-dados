package com.matheussantos.solem.ui

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.SystemClock
import android.os.Build
import android.os.PowerManager
import android.provider.Settings
import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.matheussantos.solem.domain.*
import kotlinx.coroutines.delay
import java.time.Instant
import java.time.ZoneId
import java.time.format.DateTimeFormatter

/** Foreground service owns the session; leaving this screen must not stop it. */
@Composable fun GpsDistanceTracker(exercise: String, onDistance: (Double) -> Unit, onFinished: (Double, Long) -> Unit) {
    val context=LocalContext.current
    val owner=LocalGpsAccount.current
    val shared by WalkLocationService.state.collectAsStateWithLifecycle()
    val tracking=shared.takeIf {it.owner==owner} ?: WalkSession(owner=owner)
    var startedHere by rememberSaveable(owner) {mutableStateOf(false)}
    var consumedSession by rememberSaveable(owner) {mutableStateOf(0L)}
    var now by remember {mutableLongStateOf(SystemClock.elapsedRealtime())}
    var message by remember {mutableStateOf<String?>(null)}
    val finishedCallback by rememberUpdatedState(onFinished)
    val distanceCallback by rememberUpdatedState(onDistance)
    LaunchedEffect(owner) {WalkLocationService.restore(context,owner)}
    fun precise()=ContextCompat.checkSelfPermission(context,Manifest.permission.ACCESS_FINE_LOCATION)==PackageManager.PERMISSION_GRANTED
    fun command(action:String) {
        val intent=Intent(context,WalkLocationService::class.java).setAction(action)
            .putExtra(WalkLocationService.OWNER,owner).putExtra(WalkLocationService.EXERCISE,exercise)
        try {
            message=null
            if(action==WalkLocationService.START) ContextCompat.startForegroundService(context,intent)
            else context.startService(intent)
            startedHere=true
        } catch (_:Exception) {message="O Android não permitiu iniciar o GPS. Sua medição anterior continua guardada; tente novamente com o app aberto."}
    }
    val launcher=rememberLauncherForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) {
        if(precise()) command(WalkLocationService.START)
        else message="Ative localização precisa nas permissões do Solem. A localização aproximada não mede esta caminhada com segurança."
    }
    var notificationAllowed by remember {mutableStateOf(Build.VERSION.SDK_INT<33 ||
        ContextCompat.checkSelfPermission(context,Manifest.permission.POST_NOTIFICATIONS)==PackageManager.PERMISSION_GRANTED)}
    val notificationLauncher=rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) {notificationAllowed=it}
    LaunchedEffect(tracking.meters,tracking.active,tracking.owner,exercise) {
        if(tracking.active && tracking.exercise==exercise) distanceCallback(tracking.meters/1000)
    }
    LaunchedEffect(tracking.active,tracking.startedAtMillis,tracking.pending) {
        if(tracking.active) {
            startedHere=true
            while(true) {now=SystemClock.elapsedRealtime();delay(1000)}
        } else if(startedHere && !tracking.pending && tracking.error==null && tracking.startedAtMillis>0 &&
            consumedSession!=tracking.startedAtMillis && tracking.exercise==exercise) {
            consumedSession=tracking.startedAtMillis
            finishedCallback(tracking.meters/1000,tracking.durationMillis/1000)
            startedHere=false
        }
    }
    val matching=tracking.exercise==exercise
    val signal=when(tracking.signal) {
        GpsSignal.GOOD -> "GPS recebendo sinal"
        GpsSignal.SEARCHING -> "Buscando sinal GPS…"
        GpsSignal.WEAK -> "O Android envia posições, mas ainda não são confiáveis para somar distância."
        GpsSignal.LOST -> "Sinal GPS perdido. Sua distância acumulada está preservada."
        GpsSignal.DISABLED -> "Localização desligada. Ative o GPS do aparelho para continuar."
        GpsSignal.INTERRUPTED -> "Medição interrompida. A distância anterior foi recuperada."
        GpsSignal.STOPPED -> if(tracking.startedAtMillis>0) "Medição encerrada · rascunho guardado" else "GPS ainda não iniciado"
    }
    Column(verticalArrangement=Arrangement.spacedBy(8.dp)) {
        Text("Distância por GPS (opcional)",style=MaterialTheme.typography.titleSmall)
        Text("Mede com a tela bloqueada enquanto o Android mantiver o serviço. Guarda distância e duração neste aparelho, por conta, sem salvar coordenadas ou o trajeto.",
            style=MaterialTheme.typography.bodySmall)
        Text(signal,color=if(tracking.signal in listOf(GpsSignal.LOST,GpsSignal.DISABLED,GpsSignal.WEAK,GpsSignal.INTERRUPTED))
            MaterialTheme.colorScheme.error else MaterialTheme.colorScheme.primary)
        Text("%.3f km".format(java.util.Locale.US,tracking.meters/1000),style=MaterialTheme.typography.headlineSmall)
        Text("Duração: "+clockText(tracking.duration(now)/1000))
        if(tracking.active && tracking.lastFixElapsed>0)
            Text("Último sinal confiável há "+((now-tracking.lastFixElapsed).coerceAtLeast(0)/1000)+" s",style=MaterialTheme.typography.bodySmall)
        if(tracking.active) {
            Text(tracking.locationSource.ifBlank {"Preparando localização"},style=MaterialTheme.typography.bodySmall)
            tracking.accuracyMeters?.let {
                Text("Última precisão estimada: ±%.0f m · recebida há %d s".format(it,
                    (now-tracking.receivedElapsed).coerceAtLeast(0)/1000),style=MaterialTheme.typography.bodySmall)
            }
            if(tracking.recoveryAttempts>0) Text("Tentativas automáticas de reconectar: ${tracking.recoveryAttempts}",style=MaterialTheme.typography.bodySmall)
        }
        if(tracking.hasGap) Text("Houve interrupção de sinal. Trechos sem localização não foram somados; o total pode ser menor que o percurso real.",
            style=MaterialTheme.typography.bodySmall)
        if(tracking.pending && !matching) Text("Você tem uma sessão de "+tracking.exercise+". Selecione esse exercício para retomar ou encerrar a medição.")
        Row(horizontalArrangement=Arrangement.spacedBy(8.dp)) {
            OutlinedButton(enabled=owner.isNotBlank() && (!tracking.pending || matching),onClick={
                if(tracking.active) command(WalkLocationService.STOP)
                else if(precise()) command(WalkLocationService.START)
                else launcher.launch(arrayOf(Manifest.permission.ACCESS_FINE_LOCATION,Manifest.permission.ACCESS_COARSE_LOCATION))
            }) {Text(if(tracking.active) "Parar GPS" else if(tracking.pending) "Retomar GPS" else "Iniciar GPS")}
        }
        if(!tracking.active && tracking.startedAtMillis>0 && matching) {
            TextButton(onClick={
                if(tracking.pending) command(WalkLocationService.STOP)
                else {
                    finishedCallback(tracking.meters/1000,tracking.durationMillis/1000)
                    consumedSession=tracking.startedAtMillis
                    message="Distância e duração preenchidas. Revise e salve o treino."
                }
            }) {Text(if(tracking.pending) "Encerrar e usar distância recuperada" else "Usar medição guardada")}
        }
        Text("Pare o GPS antes de salvar o treino. Retomar não recupera o trajeto percorrido sem sinal.",style=MaterialTheme.typography.bodySmall)
        var showHelp by rememberSaveable {mutableStateOf(false)}
        TextButton({showHelp=!showHelp}) {Text(if(showHelp) "Ocultar ajuda" else "GPS falha no bolso ou com tela apagada?")}
        if(showHelp) {
            Text("Antes de guardar o celular, aguarde uma posição confiável ao ar livre. No bolso, o corpo, a posição da antena e a capa podem reduzir a recepção. Se falhar, experimente outro bolso ou uma braçadeira.",style=MaterialTheme.typography.bodySmall)
            Text("No Galaxy: confira Solem → Bateria → Sem restrições e remova o Solem dos apps em suspensão. Em Localização, confira precisão do Google e localização precisa do Solem. Os nomes variam conforme a versão do Android.",style=MaterialTheme.typography.bodySmall)
            val power=context.getSystemService(PowerManager::class.java)
            if(power.isPowerSaveMode) Text("Economia de energia está ativada e pode limitar a localização.",color=MaterialTheme.colorScheme.error)
            Text("A localização combinada usa os recursos disponíveis no Android. Sem uma posição confiável, o app mantém o total já medido e avisa; não estima o trecho perdido.",style=MaterialTheme.typography.bodySmall)
            TextButton(onClick={runCatching {
                context.startActivity(Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS,Uri.parse("package:${context.packageName}")))
            }.onFailure {message="Abra Configurações → Aplicativos → Solem no Android."}}) {Text("Abrir ajustes do Solem")}
            TextButton(onClick={runCatching {
                context.startActivity(Intent(Settings.ACTION_LOCATION_SOURCE_SETTINGS))
            }.onFailure {message="Abra Configurações → Localização no Android."}}) {Text("Abrir ajustes de localização")}
        }
        if(Build.VERSION.SDK_INT>=33 && !notificationAllowed) {
            Text("Ative as notificações para ver avisos de sinal e o botão Parar GPS na tela bloqueada.",style=MaterialTheme.typography.bodySmall)
            TextButton({notificationLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)}) {Text("Ativar notificação do GPS")}
        }
        if(tracking.startedAtMillis>0) Text("Iniciado em "+Instant.ofEpochMilli(tracking.startedAtMillis).atZone(ZoneId.systemDefault())
            .format(DateTimeFormatter.ofPattern("dd/MM HH:mm:ss")),style=MaterialTheme.typography.bodySmall)
        (message ?: tracking.error)?.let {Text(it,style=MaterialTheme.typography.bodySmall,color=MaterialTheme.colorScheme.error)}
    }
}
