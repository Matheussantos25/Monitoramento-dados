package com.matheussantos.solem.ui

import android.net.Uri
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Menu
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material.icons.outlined.*
import androidx.compose.material.icons.automirrored.outlined.MenuBook
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
import com.matheussantos.solem.data.PersonalizationStore
import com.matheussantos.solem.ui.theme.LocalDashboardPreferences
import com.matheussantos.solem.ui.theme.SolemTheme

val pages = listOf("Visão geral", "Treino", "Evolução física", "Saúde", "Peso", "Estudar", "Evolução nos estudos", "Prompts", "Todos os registros", "Calendário", "Elos", "Anotações", "Resumos", "PDFs", "Mapas mentais", "Cronograma", "Financeiro", "Personalizar")

@Composable fun SolemApp(workspaceVm: WorkspaceViewModel = viewModel()) {
    val auth by workspaceVm.state.collectAsStateWithLifecycle()
    val context=LocalContext.current
    val store=remember(auth.accountId,auth.generic) { PersonalizationStore(context,auth.accountId,auth.generic) }
    val settings by store.state.collectAsStateWithLifecycle()
    CompositionLocalProvider(LocalDashboardPreferences provides settings) {
    SolemTheme(settings) { Surface(Modifier.fillMaxSize()) { when {
        !auth.initialized -> Box(Modifier.fillMaxSize(),contentAlignment=androidx.compose.ui.Alignment.Center) { CircularProgressIndicator() }
        !auth.signedIn -> WorkspacePage(workspaceVm)
        else -> key(auth.accountId) { AuthenticatedSolemApp(workspaceVm, auth.accountId, auth.generic,store) }
    } } }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable private fun AuthenticatedSolemApp(workspaceVm: WorkspaceViewModel, accountId: String, generic: Boolean,store:PersonalizationStore) {
    val vm: TrainingViewModel = viewModel(key="training-$accountId", factory=object : androidx.lifecycle.ViewModelProvider.Factory {
        @Suppress("UNCHECKED_CAST")
        override fun <T : androidx.lifecycle.ViewModel> create(modelClass: Class<T>): T = TrainingViewModel(
            if (generic) com.matheussantos.solem.data.repository.TrainingRepository(workspaceVm.trainingClient, "solem_activities")
            else com.matheussantos.solem.data.repository.TrainingRepository()
        ) as T
    })
    val context = LocalContext.current
    val nav = rememberNavController()
    val state by vm.state.collectAsStateWithLifecycle()
    val busy by vm.busy.collectAsStateWithLifecycle()
    val message by vm.message.collectAsStateWithLifecycle()
    val backStack by nav.currentBackStackEntryAsState()
    val snack = remember { SnackbarHostState() }
    val drawer = rememberDrawerState(DrawerValue.Closed)
    val scope = rememberCoroutineScope()
    val rows = (state as? TrainingUiState.Ready)?.records.orEmpty()
    val healthState by workspaceVm.state.collectAsStateWithLifecycle()
    var healthRequested by remember { mutableStateOf(false) }
    LaunchedEffect(healthState.busy,healthState.healthLoaded) {
        if(!healthState.busy && !healthState.healthLoaded && !healthRequested) {healthRequested=true;workspaceVm.loadHealth()}
    }
    val activityAvailable=state is TrainingUiState.Ready || state is TrainingUiState.Empty
    val route=backStack?.destination?.route.orEmpty()
    val isRecord=route.startsWith("edit/") || route.startsWith("new-workout/")
    val catalog = remember(generic, rows) { Catalog(context, generic).withStudyTopics(rows) }
    LaunchedEffect(message) { message?.let { snack.showSnackbar(it); vm.consumeMessage() } }
    JourneyPromotionHost(rows,catalog,activityAvailable,store)
    ModalNavigationDrawer(drawerState=drawer,drawerContent={
        ModalDrawerSheet {
            Column(Modifier.verticalScroll(rememberScrollState()).padding(12.dp)) {
                Text("✳ solem",Modifier.padding(16.dp),style=MaterialTheme.typography.headlineMedium)
                listOf("JORNADA" to listOf(0,1,2,3,5,6,9,10), "BIBLIOTECA" to listOf(11,12,13,14,7), "PLANEJAMENTO" to listOf(15,16), "CONTA" to listOf(17,8)).forEach { (group, indices) ->
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
        TopAppBar(title={Text(if(route.startsWith("health/")) "Saúde" else pages.getOrNull(route.toIntOrNull() ?: -1) ?: "Registro",
            maxLines=1,overflow=androidx.compose.ui.text.style.TextOverflow.Ellipsis)},
            navigationIcon={if(isRecord) IconButton({nav.popBackStack()}) {Icon(Icons.AutoMirrored.Filled.ArrowBack,"Voltar")}
                else IconButton({scope.launch {drawer.open()}}) {Icon(Icons.Default.Menu,"Abrir menu")}},
            actions={IconButton({nav.navigate("17") {launchSingleTop=true}}) {Icon(Icons.Outlined.Tune,"Personalizar")}
                IconButton({vm.refresh();workspaceVm.loadHealth()},enabled=!busy && !healthState.busy) {Icon(Icons.Default.Refresh,"Atualizar dados")}})
    },bottomBar={if(!isRecord) NavigationBar {
        listOf(Triple(0,"Jornada",Icons.Outlined.AutoAwesome),Triple(3,"Saúde",Icons.Outlined.FavoriteBorder),
            Triple(1,"Treino",Icons.Outlined.FitnessCenter),Triple(5,"Estudo",Icons.AutoMirrored.Outlined.MenuBook)).forEach { (index,label,icon) ->
            val active=when {route.startsWith("health/") || route=="4" -> 3;route=="2" -> 1;route=="6" -> 5;route in listOf("9","10") -> 0;else -> route.toIntOrNull()}
            NavigationBarItem(selected=active==index,
                onClick={nav.navigate(index.toString()) {launchSingleTop=true;popUpTo("0")}},icon={Icon(icon,null)},label={Text(label)})
        }
    }}) { padding ->
        Column(Modifier.padding(padding).fillMaxSize()) {
            when (val current = state) {
                TrainingUiState.Loading -> LinearProgressIndicator(Modifier.fillMaxWidth())
                TrainingUiState.SetupRequired -> Text("Configure a URL e a chave pública para conectar seu histórico.", Modifier.padding(16.dp))
                is TrainingUiState.Error -> Row(Modifier.padding(horizontal=16.dp),verticalAlignment=androidx.compose.ui.Alignment.CenterVertically) {
                    Text(current.message,Modifier.weight(1f),color=MaterialTheme.colorScheme.error)
                    TextButton(vm::refresh,enabled=!busy) {Text("Tentar novamente")}
                }
                else -> {}
            }
            if(route=="0" && healthState.healthFailed) Row(Modifier.padding(horizontal=16.dp),verticalAlignment=androidx.compose.ui.Alignment.CenterVertically) {
                Text("Diário indisponível. As metas de saúde aguardam conexão.",Modifier.weight(1f),color=MaterialTheme.colorScheme.error)
                TextButton(workspaceVm::loadHealth,enabled=!healthState.busy) {Text("Tentar novamente")}
            }
            NavHost(nav, startDestination = "0") {
                composable("0") { JourneyDashboard(rows,healthState.healthEntries,healthState.healthLoaded && !healthState.healthFailed,
                    activityAvailable,generic,{nav.navigate(it.toString()) {launchSingleTop=true}},
                    {exercise -> nav.navigate("new-workout/${Uri.encode(exercise)}")}, {section -> nav.navigate("health/$section")}) }
                composable("1") {
                    var section by rememberSaveable { mutableStateOf("Registrar") }
                    Column(Modifier.fillMaxSize()) {
                        Row(Modifier.padding(horizontal=20.dp), horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                            listOf("Registrar", "Registros").forEach { option -> FilterChip(selected=section==option, onClick={section=option}, label={Text(option)}) }
                        }
                        if (section == "Registrar") EntryScreen("Treino", catalog, rows, busy = busy,
                            save = { id, value, done -> vm.save(id, value, done) }, batch = { value, done -> vm.insertBatch(value, done) })
                        else History(rows, busy, vm::delete, { nav.navigate("edit/" + it.id) }, "Treino", Modifier.weight(1f))
                    }
                }
                composable("2") { PhysicalCharts(rows, catalog) }
                composable("3") { HealthPage(catalog, workspaceVm) }
                composable("4") { HealthPage(catalog, workspaceVm,2) }
                composable("health/{section}") { entry -> HealthPage(catalog,workspaceVm,entry.arguments?.getString("section")?.toIntOrNull() ?: -1) }
                composable("5") {
                    var section by rememberSaveable { mutableStateOf("Registrar") }
                    Column(Modifier.fillMaxSize()) {
                        Row(Modifier.padding(horizontal=20.dp), horizontalArrangement=Arrangement.spacedBy(8.dp)) {
                            listOf("Registrar", "Registros").forEach { option -> FilterChip(selected=section==option, onClick={section=option}, label={Text(option)}) }
                        }
                        if (section == "Registrar") StudyPage(rows, catalog, busy, vm)
                        else History(rows, busy, vm::delete, { nav.navigate("edit/" + it.id) }, "Estudo", Modifier.weight(1f))
                    }
                }
                composable("6") { StudyCharts(rows, catalog) }
                composable("7") { PromptsPage(workspaceVm, generic) }
                composable("8") { History(rows, busy, vm::delete, { nav.navigate("edit/" + it.id) }) }
                composable("new-workout/{exercise}") { entry ->
                    EntryScreen("Treino", catalog, rows, busy=busy,
                        save={ id, value, done -> vm.save(id, value, done) },
                        batch={ value, done -> vm.insertBatch(value, done) },
                        initialExercise=entry.arguments?.getString("exercise")?.let(Uri::decode))
                }
                composable("9") { MonthlyJournal(rows) }
                composable("10") { if (state is TrainingUiState.Ready || state is TrainingUiState.Empty) RanksPage(rows, catalog) }
                (11..16).forEach { index -> composable(index.toString()) { WorkspacePage(workspaceVm,pages[index]) } }
                composable("17") { PersonalizationPage(store,generic) }
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
@Composable fun History(rows: List<TrainingRecord>, busy: Boolean, delete: (Long) -> Unit, edit: (TrainingRecord) -> Unit, fixedCategory: String? = null, modifier: Modifier = Modifier) {
    var search by rememberSaveable { mutableStateOf("") }
    var category by rememberSaveable { mutableStateOf("Todos") }
    var confirm by remember { mutableStateOf<TrainingRecord?>(null) }
    Column(modifier.fillMaxSize().padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
        Text("Gerenciar histórico", style = MaterialTheme.typography.headlineMedium)
        Field("Buscar exercício, disciplina ou data", search) { search = it }
        if (fixedCategory == null) Choice("Categoria", category, listOf("Todos", "Treino", "Estudo", "Alimentação", "Peso", "Saúde")) { category = it }
        else Text("Categoria: $fixedCategory")
        val selectedCategory = fixedCategory ?: category
        val filtered = rows.filter { (selectedCategory == "Todos" || kind(it) == selectedCategory) && (it.exercicio + it.data).contains(search, true) }
        Text("${filtered.size} registros")
        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(filtered, key = { it.id }) { row -> Panel(row.exercicio) {
                val detail = when {
                    row.group == "Estudos" -> "${row.repeticoes} questões · ${row.durationMinutes} min"
                    row.distanceKm > 0 -> "%.2f km".format(row.distanceKm)
                    row.repeticoes > 0 -> "${row.repeticoes} repetições"
                    row.durationMinutes > 0 -> "${row.durationMinutes} min"
                    else -> "Atividade registrada"
                }
                Text("${row.data} às ${row.horario.take(5)} · $detail · Registro #${row.id}")
                Row { TextButton({ edit(row) }, enabled = !busy) { Text("Editar") }; TextButton({ confirm = row }, enabled = !busy) { Text("Excluir") } }
            } }
        }
    }
    confirm?.let { row -> AlertDialog(onDismissRequest = { confirm = null }, title = { Text("Excluir registro?") },
        text = { Text("A exclusão de ${row.exercicio} é permanente e altera o histórico compartilhado.") },
        confirmButton = { TextButton({ delete(row.id); confirm = null }) { Text("Excluir") } },
        dismissButton = { TextButton({ confirm = null }) { Text("Cancelar") } }) }
}
