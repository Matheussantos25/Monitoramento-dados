package com.matheussantos.solem.ui

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.Refresh
import kotlinx.coroutines.launch
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import androidx.navigation.compose.*
import com.matheussantos.solem.data.model.*
import com.matheussantos.solem.domain.*
import com.matheussantos.solem.ui.state.TrainingUiState
import com.matheussantos.solem.viewmodel.TrainingViewModel
import com.matheussantos.solem.viewmodel.WorkspaceViewModel

val pages = listOf("Visão geral", "Treino", "Evolução física", "Saúde", "Peso", "Estudar", "Evolução nos estudos", "Prompts", "Configurações", "Calendário", "Elos", "Anotações", "Resumos", "PDFs", "Mapas mentais", "Cronograma", "Investimentos")

@Composable fun SolemApp(workspaceVm: WorkspaceViewModel = viewModel()) {
    val auth by workspaceVm.state.collectAsStateWithLifecycle()
    when {
        !auth.initialized -> Box(Modifier.fillMaxSize(),contentAlignment=androidx.compose.ui.Alignment.Center) { CircularProgressIndicator() }
        !auth.signedIn -> WorkspacePage(workspaceVm)
        else -> AuthenticatedSolemApp(workspaceVm)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable private fun AuthenticatedSolemApp(workspaceVm: WorkspaceViewModel, vm: TrainingViewModel = viewModel()) {
    val context = LocalContext.current
    val catalog = remember { Catalog(context) }
    val nav = rememberNavController()
    val state by vm.state.collectAsStateWithLifecycle()
    val busy by vm.busy.collectAsStateWithLifecycle()
    val message by vm.message.collectAsStateWithLifecycle()
    val backStack by nav.currentBackStackEntryAsState()
    val snack = remember { SnackbarHostState() }
    val drawer = rememberDrawerState(DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    val rows = (state as? TrainingUiState.Ready)?.records.orEmpty()
    LaunchedEffect(message) { message?.let { snack.showSnackbar(it); vm.consumeMessage() } }
    ModalNavigationDrawer(drawerState=drawer,drawerContent={
        ModalDrawerSheet {
            Column(Modifier.verticalScroll(rememberScrollState()).padding(12.dp)) {
                Text("✳ solem",Modifier.padding(16.dp),style=MaterialTheme.typography.headlineMedium)
                listOf("JORNADA" to listOf(0,1,2,3,5,6,9,10), "BIBLIOTECA" to listOf(11,12,13,14,7), "PLANEJAMENTO" to listOf(15,16), "CONTA" to listOf(8)).forEach { (group, indices) ->
                    Text(group,Modifier.padding(16.dp,12.dp),style=MaterialTheme.typography.labelSmall)
                    indices.forEach { index -> NavigationDrawerItem(label={Text(pages[index])},selected=backStack?.destination?.route==index.toString(),onClick={
                        nav.navigate(index.toString()) {launchSingleTop=true;popUpTo("0")}
                        scope.launch {drawer.close()}
                    }) }
                }
                HorizontalDivider(Modifier.padding(vertical=8.dp))
                TextButton({
                    workspaceVm.logout()
                    nav.navigate("0") {popUpTo("0") {inclusive=true}}
                    scope.launch {drawer.close()}
                },modifier=Modifier.fillMaxWidth()) {Text("Sair")}
            }
        }
    }) {
    Scaffold(snackbarHost = { SnackbarHost(snack) }, topBar = {
        TopAppBar(title={Text(pages.getOrNull(backStack?.destination?.route?.toIntOrNull() ?: -1) ?: "Registro")},
            navigationIcon={IconButton({scope.launch {drawer.open()}}) {Icon(Icons.Default.Menu,"Abrir menu")}},
            actions={IconButton(vm::refresh,enabled=!busy) {Icon(Icons.Default.Refresh,"Atualizar histórico")}})
    }) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            when (val current = state) {
                TrainingUiState.Loading -> LinearProgressIndicator(Modifier.fillMaxWidth())
                TrainingUiState.SetupRequired -> Text("Configure a URL e a chave pública para conectar seu histórico.", Modifier.padding(16.dp))
                is TrainingUiState.Error -> Text(current.message, Modifier.padding(16.dp), color = MaterialTheme.colorScheme.error)
                else -> {}
            }
            NavHost(nav, startDestination = "0") {
                composable("0") { Overview(rows) { nav.navigate(it.toString()) } }
                composable("1") { EntryScreen("Treino", catalog, rows, busy = busy, save = { id, value, done -> vm.save(id, value, done) }, batch = { value, done -> vm.insertBatch(value, done) }) }
                composable("2") { PhysicalCharts(rows, catalog) }
                composable("3") { HealthPage(catalog, workspaceVm) }
                composable("4") { HealthPage(catalog, workspaceVm) }
                composable("5") { StudyPage(rows, catalog, busy, vm) }
                composable("6") { StudyCharts(rows, catalog) }
                composable("7") { PromptsPage() }
                composable("8") { History(rows, busy, vm::delete) { nav.navigate("edit/" + it.id) } }
                composable("9") { MonthlyJournal(rows) }
                composable("10") { if (state is TrainingUiState.Ready || state is TrainingUiState.Empty) RanksPage(rows, catalog) }
                (11..16).forEach { index -> composable(index.toString()) { WorkspacePage(workspaceVm,pages[index]) } }
                composable("edit/{id}") { entry ->
                    val record = rows.firstOrNull { it.id == entry.arguments?.getString("id")?.toLongOrNull() }
                    if (record == null) Text("Registro não encontrado. Atualize o histórico.")
                    else if (kind(record) in listOf("Saúde", "Alimentação", "Peso")) Text("Este registro legado está na tabela compartilhada. Para novos dados pessoais, use a aba Saúde, que salva em uma tabela privada.", Modifier.padding(16.dp))
                    else key(record.id) { EntryScreen(kind(record), catalog, rows, record, busy,
                        save = { id, value, _ -> vm.save(id, value) { nav.popBackStack() } }) }
                }
            }
        }
    }
    }
}
fun kind(row: TrainingRecord) = when(row.group) {
    "Estudos" -> "Estudo"
    "Nutrição" -> if (row.exercicio == "Água") "Saúde" else "Alimentação"
    "Métricas" -> if (row.exercicio == "Sono Diário") "Saúde" else "Peso"
    else -> "Treino"
}
@Composable fun Overview(rows: List<TrainingRecord>, navigate: (Int) -> Unit) {
    val p = calculateProgress(rows)
    Page("Seu espaço de evolução") {
        Panel("STATUS DO PERSONAGEM") {
            Text("NÍVEL ${p.xp / 250 + 1}", style = MaterialTheme.typography.headlineLarge,
                color = MaterialTheme.colorScheme.primary)
            Text("${p.xp % 250} / 250 XP para o próximo nível")
            LinearProgressIndicator(progress = { (p.xp % 250) / 250f }, modifier = Modifier.fillMaxWidth())
            Text("◈ ${p.streak} dias de sequência  •  ${p.xp} XP no histórico",
                color = MaterialTheme.colorScheme.onSurfaceVariant)
        }
        OutlinedButton({ navigate(3) }, modifier=Modifier.fillMaxWidth()) { Text("Abrir diário de saúde") }
        OutlinedButton({ navigate(10) }) { Text("Ver meus elos de físico e estudo") }
        OutlinedButton({ navigate(9) },modifier=Modifier.fillMaxWidth()) { Text("Abrir calendário mensal") }
        val todayProgress = calculateProgress(rows.filter { it.data.take(10) == today().toString() })
        Panel("MISSÕES DIÁRIAS") {
            Text("${if (todayProgress.workoutDays > 0) "✓" else "◇"} Treinar  ·  +30 XP")
            Text("${if (todayProgress.studyDays > 0) "✓" else "◇"} Estudar  ·  +30 XP")
            Text("Treino e estudo no mesmo dia: +15 XP", color = MaterialTheme.colorScheme.onSurfaceVariant)
            Text("${todayProgress.xp} XP conquistados hoje", color = MaterialTheme.colorScheme.primary)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton({ navigate(1) }) { Text("Treinar") }
                OutlinedButton({ navigate(5) }) { Text("Estudar") }
            }
        }
        val start = today().minusDays((today().dayOfWeek.value - 1).toLong())
        val week = rows.filter { it.data >= start.toString() && it.data <= today().toString() }
        Panel("Esta semana") {
            Text("${week.filter { it.isWorkout() && (it.repeticoes > 0 || it.durationMinutes > 0 || it.distanceKm > 0 || it.number("isometria_segundos") > 0) }.map { it.data }.distinct().size} dias de treino")
            Text("%.1f minutos de estudo".format(week.filter { it.group == "Estudos" }.sumOf { it.studyMinutes() + it.number("tempo_video") }))
            Text("%.0f questões".format(week.filter { it.group == "Estudos" && it.extra("fonte_questoes") != "Anki" }.sumOf { it.number("q_certas") + it.number("q_erradas") }))
        }
        Panel("Seus marcos") {
            listOf(Triple("Primeiro passo", p.days, 1), Triple("Construindo o ritmo", p.days, 7),
                Triple("Mente em movimento", p.studyDays, 10), Triple("Corpo em movimento", p.workoutDays, 10),
                Triple("Uma nova rotina", p.days, 30)).forEach { (label, value, total) -> Goal(label, value.toDouble(), total) }
        }
        Text("Registros recentes", style = MaterialTheme.typography.titleLarge)
        if (rows.isEmpty()) Text("Registre sua primeira atividade para começar.")
        rows.take(5).forEach { row -> Panel(row.exercicio) { Text("${row.data} • ${kind(row)}") } }
    }
}
@Composable fun History(rows: List<TrainingRecord>, busy: Boolean, delete: (Long) -> Unit, edit: (TrainingRecord) -> Unit) {
    var search by rememberSaveable { mutableStateOf("") }
    var category by rememberSaveable { mutableStateOf("Todos") }
    var confirm by remember { mutableStateOf<TrainingRecord?>(null) }
    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Gerenciar histórico", style = MaterialTheme.typography.headlineMedium)
        Field("Buscar exercício, disciplina ou data", search) { search = it }
        Choice("Categoria", category, listOf("Todos", "Treino", "Estudo", "Alimentação", "Peso", "Saúde")) { category = it }
        val filtered = rows.filter { (category == "Todos" || kind(it) == category) && (it.exercicio + it.data).contains(search, true) }
        Text("${filtered.size} registros")
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(filtered, key = { it.id }) { row -> Panel(row.exercicio) {
                Text("${row.data} • ${row.horario} • ${kind(row)}")
                Row { TextButton({ edit(row) }, enabled = !busy) { Text("Editar") }; TextButton({ confirm = row }, enabled = !busy) { Text("Excluir") } }
            } }
        }
    }
    confirm?.let { row -> AlertDialog(onDismissRequest = { confirm = null }, title = { Text("Excluir registro?") },
        text = { Text("A exclusão de ${row.exercicio} é permanente e altera o histórico compartilhado.") },
        confirmButton = { TextButton({ delete(row.id); confirm = null }) { Text("Excluir") } },
        dismissButton = { TextButton({ confirm = null }) { Text("Cancelar") } }) }
}
