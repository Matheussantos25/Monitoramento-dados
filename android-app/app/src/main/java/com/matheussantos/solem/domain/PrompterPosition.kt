package com.matheussantos.solem.domain

/** A text anchor survives line wrapping when the reader changes size. */
data class PrompterLine(val start: Int, val top: Float, val bottom: Float)
data class PrompterAnchor(val character: Int, val lineFraction: Float, val atStart: Boolean = false)

fun capturePrompterPosition(scroll: Int, padding: Float, lines: List<PrompterLine>): PrompterAnchor {
    if (scroll <= padding || lines.isEmpty()) return PrompterAnchor(0, 0f, true)
    val y = scroll - padding
    val line = lines.lastOrNull { it.top <= y } ?: lines.first()
    return PrompterAnchor(line.start, ((y-line.top)/(line.bottom-line.top).coerceAtLeast(1f)).coerceIn(0f,1f))
}

fun restorePrompterPosition(anchor: PrompterAnchor, padding: Float, lines: List<PrompterLine>): Int {
    if (anchor.atStart || lines.isEmpty()) return 0
    val line = lines.lastOrNull { it.start <= anchor.character } ?: lines.first()
    return (padding + line.top + (line.bottom-line.top)*anchor.lineFraction).toInt().coerceAtLeast(0)
}
