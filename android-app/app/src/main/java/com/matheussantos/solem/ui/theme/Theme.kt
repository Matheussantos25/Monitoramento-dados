package com.matheussantos.solem.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.material3.Shapes
import androidx.compose.material3.Typography
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.runtime.Composable
import androidx.compose.runtime.staticCompositionLocalOf
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.matheussantos.solem.domain.DashboardPreferences

val LocalDashboardPreferences = staticCompositionLocalOf { DashboardPreferences() }
private val SolemType = Typography(
    displaySmall = TextStyle(fontSize=36.sp, lineHeight=40.sp, fontWeight=FontWeight.Bold, letterSpacing=(-1).sp),
    headlineLarge = TextStyle(fontSize=32.sp, lineHeight=36.sp, fontWeight=FontWeight.Bold, letterSpacing=(-.8).sp),
    headlineMedium = TextStyle(fontSize=26.sp, lineHeight=32.sp, fontWeight=FontWeight.Bold, letterSpacing=(-.5).sp),
    titleLarge = TextStyle(fontSize=21.sp, lineHeight=28.sp, fontWeight=FontWeight.SemiBold),
    titleMedium = TextStyle(fontSize=17.sp, lineHeight=24.sp, fontWeight=FontWeight.SemiBold),
    bodyLarge = TextStyle(fontSize=16.sp, lineHeight=24.sp, fontFamily=FontFamily.SansSerif),
    bodyMedium = TextStyle(fontSize=14.sp, lineHeight=21.sp, fontFamily=FontFamily.SansSerif),
    labelLarge = TextStyle(fontSize=14.sp, lineHeight=20.sp, fontWeight=FontWeight.SemiBold),
    labelSmall = TextStyle(fontSize=11.sp, lineHeight=16.sp, fontWeight=FontWeight.Medium, letterSpacing=.5.sp)
)

@Composable fun SolemTheme(settings: DashboardPreferences = DashboardPreferences(), content: @Composable () -> Unit) {
    val dark = settings.theme == "Escuro" || settings.theme == "Sistema" && isSystemInDarkTheme()
    val accent = when(settings.accent) {
        "Âmbar" -> if(dark) Color(0xFFFFCD94) else Color(0xFF815017)
        "Rubi" -> if(dark) Color(0xFFFFABB4) else Color(0xFF923343)
        else -> if(dark) Color(0xFF8DDEFF) else Color(0xFF006387)
    }
    val container = when(settings.accent) { "Âmbar" -> Color(0xFF413321); "Rubi" -> Color(0xFF442D37); else -> Color(0xFF163C51) }
    val colors = if(dark) darkColorScheme(
        primary=accent, onPrimary=Color(0xFF092132), primaryContainer=container, onPrimaryContainer=Color(0xFFF0F6FF),
        secondary=accent, onSecondary=Color(0xFF092132), secondaryContainer=container, onSecondaryContainer=Color(0xFFF0F6FF),
        tertiary=accent, onTertiary=Color(0xFF092132), tertiaryContainer=container, onTertiaryContainer=Color(0xFFF0F6FF),
        background=Color(0xFF090F1B), onBackground=Color(0xFFF0F6FF), surface=Color(0xFF111D2E), onSurface=Color(0xFFF0F6FF),
        surfaceVariant=Color(0xFF1B2B41), onSurfaceVariant=Color(0xFFBBCBDC),
        surfaceContainer=Color(0xFF132136), surfaceContainerHigh=Color(0xFF1B2B41), surfaceContainerHighest=Color(0xFF21324A),
        outline=Color(0xFF677D94), outlineVariant=Color(0xFF2A3C52), error=Color(0xFFFFB4AB)
    ) else lightColorScheme(
        primary=accent, onPrimary=Color.White, primaryContainer=when(settings.accent) {"Âmbar" -> Color(0xFFFFE5C5);"Rubi" -> Color(0xFFFFE0E5);else -> Color(0xFFD5EEFA)}, onPrimaryContainer=accent,
        secondary=accent, onSecondary=Color.White, secondaryContainer=Color(0xFFE6EDF5), onSecondaryContainer=accent,
        tertiary=accent, onTertiary=Color.White, tertiaryContainer=Color(0xFFE6EDF5), onTertiaryContainer=accent,
        background=Color(0xFFF3F7FC), onBackground=Color(0xFF142337), surface=Color(0xFFFFFFFF), onSurface=Color(0xFF142337),
        surfaceVariant=Color(0xFFE6EDF5), onSurfaceVariant=Color(0xFF43566B),
        surfaceContainer=Color(0xFFEAF0F7), surfaceContainerHigh=Color(0xFFE2EBF4), surfaceContainerHighest=Color(0xFFD9E4F0),
        outline=Color(0xFF708397), outlineVariant=Color(0xFFCBD7E5)
    )
    MaterialTheme(colorScheme=colors, typography=SolemType,
        shapes=Shapes(extraSmall=RoundedCornerShape(6.dp), small=RoundedCornerShape(12.dp), medium=RoundedCornerShape(18.dp), large=RoundedCornerShape(24.dp), extraLarge=RoundedCornerShape(32.dp)),
        content=content)
}
