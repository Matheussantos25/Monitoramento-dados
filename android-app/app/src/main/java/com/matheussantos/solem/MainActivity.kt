package com.matheussantos.solem

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import com.matheussantos.solem.ui.SolemApp
import com.matheussantos.solem.ui.theme.SolemTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { SolemTheme { SolemApp() } }
    }
}
