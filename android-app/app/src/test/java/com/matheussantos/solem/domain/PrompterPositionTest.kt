package com.matheussantos.solem.domain

import org.junit.Assert.*
import org.junit.Test

class PrompterPositionTest {
    private val narrow=listOf(PrompterLine(0,0f,40f),PrompterLine(20,40f,80f),PrompterLine(40,80f,120f),PrompterLine(60,120f,160f))
    private val wide=listOf(PrompterLine(0,0f,40f),PrompterLine(30,40f,80f),PrompterLine(60,80f,120f))
    @Test fun keepsVisibleTextWhenLinesWrapDifferently() {
        val anchor=capturePrompterPosition(114,24f,narrow)
        assertEquals(40,anchor.character)
        assertEquals(74,restorePrompterPosition(anchor,24f,wide))
        assertEquals(114,restorePrompterPosition(anchor,24f,narrow))
    }
    @Test fun sameWidthAndSettingsToggleKeepExactOffset() {
        for(offset in listOf(30,60,114,150))assertEquals(offset,restorePrompterPosition(capturePrompterPosition(offset,24f,narrow),24f,narrow))
    }
    @Test fun startAndEmptyTextNeverJumpOrCrash() {
        assertEquals(0,restorePrompterPosition(capturePrompterPosition(0,24f,narrow),24f,wide))
        assertEquals(0,restorePrompterPosition(capturePrompterPosition(500,24f,emptyList()),24f,wide))
        assertEquals(0,restorePrompterPosition(PrompterAnchor(40,.5f),24f,emptyList()))
    }
}
