package com.matheussantos.solem.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val SolemColors = darkColorScheme(
    primary = Color(0xFF83DCFF), onPrimary = Color(0xFF091926),
    primaryContainer = Color(0xFF173951), onPrimaryContainer = Color(0xFFEAF7FF),
    secondary = Color(0xFFAAACFF), onSecondary = Color(0xFF161B44),
    background = Color(0xFF090F1B), onBackground = Color(0xFFEEF6FF),
    surface = Color(0xFF111B2B), onSurface = Color(0xFFEEF6FF),
    surfaceVariant = Color(0xFF1B2940), onSurfaceVariant = Color(0xFFB9C9D9),
    outline = Color(0xFF42617E)
)

@Composable fun SolemTheme(content: @Composable () -> Unit) = MaterialTheme(
    colorScheme = SolemColors,
    content = content)
