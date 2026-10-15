package com.matheussantos.solem.ui

import androidx.activity.compose.BackHandler
import androidx.compose.animation.AnimatedContent
import androidx.compose.animation.fadeIn
import androidx.compose.animation.fadeOut
import androidx.compose.animation.togetherWith
import androidx.compose.animation.core.tween
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.outlined.ArrowForward
import androidx.compose.material.icons.outlined.AlternateEmail
import androidx.compose.material.icons.outlined.Fingerprint
import androidx.compose.material.icons.outlined.Visibility
import androidx.compose.material.icons.outlined.VisibilityOff
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.res.painterResource
import androidx.compose.ui.semantics.LiveRegionMode
import androidx.compose.ui.semantics.liveRegion
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import com.matheussantos.solem.R
import com.matheussantos.solem.domain.EmailAccess
import com.matheussantos.solem.ui.theme.SolemTheme
import com.matheussantos.solem.viewmodel.WorkspaceState
import com.matheussantos.solem.viewmodel.WorkspaceViewModel
import kotlinx.coroutines.delay

@Composable fun LoginScreen(vm: WorkspaceViewModel) {
    val state by vm.state.collectAsStateWithLifecycle()
    EmailLoginContent(state, vm::requestEmailAccess, vm::verifyEmailAccess,
        { email, password -> vm.login(email,password,false) }, vm::changeAccessEmail)
}

@Composable internal fun EmailLoginContent(
    state: WorkspaceState,
    onSend: (String) -> Unit,
    onVerify: (String) -> Unit,
    onPassword: (String, String) -> Unit,
    onChangeEmail: () -> Unit,
) {
    var email by rememberSaveable { mutableStateOf(state.emailChallenge) }
    var passwordMode by rememberSaveable { mutableStateOf(false) }
    // Credentials intentionally do not survive Activity/process recreation.
    var password by remember { mutableStateOf("") }
    var showPassword by remember { mutableStateOf(false) }
    var code by remember(state.emailChallenge) { mutableStateOf("") }
    var fieldError by remember { mutableStateOf<String?>(null) }
    var remaining by remember { mutableIntStateOf(0) }
    val hasCode = state.emailChallenge.isNotBlank()
    val colors = MaterialTheme.colorScheme
    LaunchedEffect(state.emailChallenge) {
        if (hasCode) { email=state.emailChallenge;passwordMode=false }
        fieldError=null
    }
    LaunchedEffect(state.resendAvailableAt) {
        do {
            remaining=EmailAccess.resendSeconds(state.resendAvailableAt,System.currentTimeMillis())
            if (remaining>0) delay(1000)
        } while (remaining>0)
    }
    fun submit() {
        if (state.busy) return
        fieldError = when {
            hasCode && !EmailAccess.validCode(code) -> "Digite o código numérico recebido no e-mail."
            !hasCode && !EmailAccess.validEmail(email) -> "Confira o endereço de e-mail."
            passwordMode && password.isBlank() -> "Informe sua senha."
            else -> null
        }
        if (fieldError!=null) return
        when {
            hasCode -> onVerify(code)
            passwordMode -> { onPassword(email.trim(),password);password="" }
            remaining==0 -> onSend(email.trim())
        }
    }
    fun backToEmail() {
        if (state.busy) return
        onChangeEmail();passwordMode=false;password="";code="";fieldError=null
    }
    BackHandler(enabled=hasCode || passwordMode) { backToEmail() }

    Box(Modifier.fillMaxSize().background(colors.background).safeDrawingPadding().imePadding()) {
        Column(Modifier.align(Alignment.TopCenter).widthIn(max=480.dp).fillMaxWidth()
            .verticalScroll(rememberScrollState()).padding(horizontal=28.dp,vertical=28.dp)) {
            Row(verticalAlignment=Alignment.CenterVertically,horizontalArrangement=Arrangement.spacedBy(12.dp)) {
                Surface(shape=RoundedCornerShape(16.dp),color=colors.primary) {
                    Image(painterResource(R.drawable.ic_solem_foreground),null,Modifier.size(52.dp))
                }
                Column {
                    Text("solem",fontSize=26.sp,fontWeight=FontWeight.Bold,letterSpacing=(-1).sp)
                    Text("Corpo, mente e constância",style=MaterialTheme.typography.bodySmall,color=colors.onSurfaceVariant)
                }
            }
            Spacer(Modifier.height(40.dp))
            Row(horizontalArrangement=Arrangement.spacedBy(6.dp)) {
                Box(Modifier.size(34.dp,3.dp).background(colors.primary,RoundedCornerShape(2.dp)))
                Box(Modifier.size(34.dp,3.dp).background(if(hasCode) colors.primary else colors.outlineVariant,RoundedCornerShape(2.dp)))
            }
            Spacer(Modifier.height(22.dp))
            AnimatedContent(targetState=hasCode,transitionSpec={fadeIn(tween(180)) togetherWith fadeOut(tween(120))},label="loginHeading") { confirming ->
                Column(verticalArrangement=Arrangement.spacedBy(14.dp)) {
                    Text(if(confirming) "Confira seu e-mail." else "Seu próximo passo\ncomeça aqui.",
                        style=MaterialTheme.typography.displaySmall,fontWeight=FontWeight.SemiBold)
                    Text(if(confirming) "Digite o código enviado para" else "Informe seu e-mail para entrar ou começar. Sem precisar criar uma senha.",
                        style=MaterialTheme.typography.bodyLarge,color=colors.onSurfaceVariant)
                }
            }
            if(hasCode) {
                Text(state.emailChallenge,Modifier.padding(top=6.dp),style=MaterialTheme.typography.titleMedium,color=colors.primary)
                TextButton(::backToEmail,enabled=!state.busy,contentPadding=PaddingValues(vertical=8.dp)) { Text("Corrigir e-mail") }
            }
            Spacer(Modifier.height(if(hasCode) 12.dp else 30.dp))
            if(hasCode) {
                OutlinedTextField(code,{code=it.filter { c -> c in '0'..'9' }.take(10);fieldError=null},
                    Modifier.fillMaxWidth(),enabled=!state.busy,singleLine=true,
                    label={Text("Código de acesso")},placeholder={Text("Código do e-mail")},
                    textStyle=MaterialTheme.typography.headlineMedium.copy(fontFamily=FontFamily.Monospace,letterSpacing=4.sp),
                    shape=RoundedCornerShape(16.dp),isError=fieldError!=null,
                    keyboardOptions=KeyboardOptions(keyboardType=KeyboardType.NumberPassword,imeAction=ImeAction.Done),
                    keyboardActions=KeyboardActions(onDone={submit()}))
            } else {
                OutlinedTextField(email,{email=it;fieldError=null},Modifier.fillMaxWidth(),enabled=!state.busy,
                    label={Text("Seu e-mail")},placeholder={Text("voce@exemplo.com")},singleLine=true,
                    leadingIcon={Icon(Icons.Outlined.AlternateEmail,null)},shape=RoundedCornerShape(16.dp),
                    isError=fieldError!=null && !EmailAccess.validEmail(email),
                    keyboardOptions=KeyboardOptions(keyboardType=KeyboardType.Email,imeAction=if(passwordMode) ImeAction.Next else ImeAction.Done),
                    keyboardActions=KeyboardActions(onDone={submit()}))
                if(passwordMode) {
                    Spacer(Modifier.height(14.dp))
                    OutlinedTextField(password,{password=it;fieldError=null},Modifier.fillMaxWidth(),enabled=!state.busy,
                        label={Text("Sua senha")},singleLine=true,shape=RoundedCornerShape(16.dp),
                        visualTransformation=if(showPassword) VisualTransformation.None else PasswordVisualTransformation(),
                        trailingIcon={IconButton({showPassword=!showPassword}) {
                            Icon(if(showPassword) Icons.Outlined.VisibilityOff else Icons.Outlined.Visibility,if(showPassword) "Ocultar senha" else "Mostrar senha") }},
                        keyboardOptions=KeyboardOptions(keyboardType=KeyboardType.Password,imeAction=ImeAction.Done),
                        keyboardActions=KeyboardActions(onDone={submit()}))
                }
            }
            val error = fieldError ?: state.message?.takeIf { state.failed }
            if(error!=null) {
                Text(error,Modifier.padding(top=12.dp).semantics { liveRegion=LiveRegionMode.Polite },color=colors.error,
                    style=MaterialTheme.typography.bodyMedium)
            } else if(state.message!=null) {
                Text(state.message,Modifier.padding(top=12.dp).semantics { liveRegion=LiveRegionMode.Polite },
                    color=colors.onSurfaceVariant,style=MaterialTheme.typography.bodyMedium)
            }
            Spacer(Modifier.height(20.dp))
            Button(::submit,Modifier.fillMaxWidth().heightIn(min=56.dp),shape=RoundedCornerShape(16.dp),
                enabled=!state.busy && (hasCode || passwordMode || remaining==0)) {
                if(state.busy) CircularProgressIndicator(Modifier.size(20.dp),strokeWidth=2.dp)
                else Icon(Icons.AutoMirrored.Outlined.ArrowForward,null,Modifier.size(20.dp))
                Spacer(Modifier.width(10.dp))
                Text(when {
                    state.busy -> if(state.emailSending) "Enviando…" else "Entrando…"
                    hasCode -> "Confirmar e entrar"
                    passwordMode -> "Entrar com senha"
                    remaining>0 -> "Tente novamente em ${remaining}s"
                    else -> "Continuar com e-mail"
                })
            }
            if(hasCode) {
                Text("Você também pode tocar no link do e-mail para abrir o Solem neste celular.",
                    Modifier.padding(top=16.dp),style=MaterialTheme.typography.bodyMedium,color=colors.onSurfaceVariant)
                TextButton({code="";onSend(state.emailChallenge)},enabled=!state.busy && remaining==0,
                    modifier=Modifier.padding(top=6.dp)) {Text(if(remaining>0) "Reenviar em ${remaining}s" else "Reenviar código")}
                Text("Não chegou? Confira o spam. Use sempre o código do e-mail mais recente.",
                    style=MaterialTheme.typography.bodySmall,color=colors.onSurfaceVariant)
            } else {
                Text(if(passwordMode) "Use a senha que você já tem. Se preferir, receba um código no e-mail." else
                    "Já tem conta? Seu histórico continua com você. É sua primeira vez? Criamos seu acesso ao confirmar o e-mail.",
                    Modifier.padding(top=18.dp),style=MaterialTheme.typography.bodyMedium,color=colors.onSurfaceVariant)
                TextButton({onChangeEmail();passwordMode=!passwordMode;password="";fieldError=null},enabled=!state.busy,
                    modifier=Modifier.padding(top=8.dp)) {
                    Text(if(passwordMode) "Prefiro receber um código" else "Já tenho senha · entrar com senha")
                }
            }
            Spacer(Modifier.height(36.dp))
            HorizontalDivider(color=colors.outlineVariant)
            Row(Modifier.padding(top=20.dp),horizontalArrangement=Arrangement.spacedBy(10.dp)) {
                Icon(Icons.Outlined.Fingerprint,null,Modifier.size(18.dp),tint=colors.onSurfaceVariant)
                Text("O acesso só é liberado após confirmar que o e-mail é seu. Sua sessão fica salva neste celular.",
                    style=MaterialTheme.typography.bodySmall,color=colors.onSurfaceVariant)
            }
        }
    }
}

@Preview(showBackground=true,widthDp=390,heightDp=844)
@Composable private fun EmailLoginPreview() = SolemTheme {
    EmailLoginContent(WorkspaceState(initialized=true),{},{},{_,_->},{})
}

@Preview(showBackground=true,widthDp=360,heightDp=800,fontScale=1.3f)
@Composable private fun EmailCodePreview() = SolemTheme {
    EmailLoginContent(WorkspaceState(initialized=true,emailChallenge="voce@exemplo.com"),{},{},{_,_->},{})
}
