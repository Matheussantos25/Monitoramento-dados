package com.matheussantos.solem

import android.os.Bundle
import android.content.Intent
import androidx.activity.ComponentActivity
import androidx.activity.viewModels
import androidx.activity.compose.setContent
import com.matheussantos.solem.ui.SolemApp
import com.matheussantos.solem.viewmodel.WorkspaceViewModel

class MainActivity : ComponentActivity() {
    private val workspaceVm: WorkspaceViewModel by viewModels()
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent { SolemApp(workspaceVm) }
        consumeConfirmation(intent)
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        consumeConfirmation(intent)
    }

    private fun consumeConfirmation(incoming: Intent) {
        if (incoming.action != Intent.ACTION_VIEW) return
        val url = incoming.data?.toString() ?: return
        // Do not keep one-time codes in the Activity intent across recreation.
        incoming.data = null
        workspaceVm.confirmEmail(url)
    }
}
