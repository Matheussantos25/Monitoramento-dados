package com.matheussantos.solem.ui

import androidx.compose.material3.Surface
import androidx.compose.runtime.Composable
import androidx.compose.runtime.CompositionLocalProvider
import androidx.compose.ui.tooling.preview.Preview
import com.matheussantos.solem.data.model.HealthEntry
import com.matheussantos.solem.data.model.TrainingRecord
import com.matheussantos.solem.domain.DashboardPreferences
import com.matheussantos.solem.domain.today
import com.matheussantos.solem.ui.theme.LocalDashboardPreferences
import com.matheussantos.solem.ui.theme.SolemTheme
import kotlinx.serialization.json.buildJsonObject
import kotlinx.serialization.json.put

// Fictitious, preview-only data. Not reachable from the app's navigation or written anywhere.
private fun previewWorkouts()=listOf(
    TrainingRecord(1,today().toString(),"10:00:00","Peitoral","Flexão",repeticoes=8),
    TrainingRecord(2,today().toString(),"11:00:00","Pernas","Agachamento",repeticoes=15),
    TrainingRecord(3,today().minusDays(1).toString(),"12:00:00","Estudos","Matemática",durationMinutes=25,
        extras=buildJsonObject {put("q_certas",18);put("q_erradas",2)})
)
private fun previewHealth()=listOf(HealthEntry("preview",today().toString(),"12:00:00","water",
    buildJsonObject {put("volume_ml",750);put("quantidade",2)}))

@Composable private fun DashboardPreview(settings:DashboardPreferences) {
    CompositionLocalProvider(LocalDashboardPreferences provides settings) {
        SolemTheme(settings) { Surface {
            JourneyDashboard(previewWorkouts(),previewHealth(),true,true,true,{}, {}, {})
        } }
    }
}
@Preview(name="Jornada · azul escuro",widthDp=360,heightDp=800,showBackground=true)
@Composable private fun DarkJourneyPreview() {DashboardPreview(DashboardPreferences.defaults(true))}
@Preview(name="Jornada · fonte ampliada",widthDp=320,heightDp=760,fontScale=1.3f,showBackground=true)
@Composable private fun LargeTextJourneyPreview() {DashboardPreview(DashboardPreferences.defaults(true))}
@Preview(name="Jornada · tema claro",widthDp=360,heightDp=800,showBackground=true)
@Composable private fun LightJourneyPreview() {DashboardPreview(DashboardPreferences.defaults(true).copy(theme="Claro"))}
