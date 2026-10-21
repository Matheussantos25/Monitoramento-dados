package com.matheussantos.solem.domain

import kotlinx.serialization.Serializable
import kotlin.math.*

enum class GpsSignal { SEARCHING, GOOD, WEAK, LOST, DISABLED, INTERRUPTED, STOPPED }

/** Only totals are durable. Coordinates exist exclusively in the live accumulator. */
@Serializable data class WalkSession(
    val owner: String = "", val exercise: String = "Caminhada",
    val active: Boolean = false, val pending: Boolean = false,
    val meters: Double = 0.0, val error: String? = null,
    val startedAtMillis: Long = 0, val startedElapsedMillis: Long = 0,
    val durationMillis: Long = 0, val bootCount: Int = -1,
    val hasGap: Boolean = false, val signal: GpsSignal = GpsSignal.STOPPED,
    val lastFixElapsed: Long = 0
) {
    fun duration(now: Long) = if (active) maxOf(durationMillis, now-startedElapsedMillis) else durationMillis
    fun recovered(now: Long, boot: Int): WalkSession {
        val duration = if (active && boot >= 0 && boot == bootCount && now >= startedElapsedMillis)
            maxOf(durationMillis, now-startedElapsedMillis) else durationMillis
        return copy(active=false, durationMillis=duration, startedElapsedMillis=now-duration,
            bootCount=boot, hasGap=hasGap || pending, lastFixElapsed=0,
            signal=if(pending) GpsSignal.INTERRUPTED else GpsSignal.STOPPED)
    }
}

data class GpsFix(val latitude: Double, val longitude: Double, val accuracy: Double, val elapsed: Long)
data class GpsUpdate(val added: Double = 0.0, val usable: Boolean = false, val gap: Boolean = false)

/** Conservative walking/running filter. Never bridges an unobserved signal gap. */
class WalkDistanceAccumulator {
    private var anchor: GpsFix? = null
    private var latest: GpsFix? = null
    fun breakSegment() { anchor=null; latest=null }
    fun accept(point: GpsFix, now: Long): GpsUpdate {
        if (!point.latitude.isFinite() || point.latitude !in -90.0..90.0 ||
            !point.longitude.isFinite() || point.longitude !in -180.0..180.0 ||
            !point.accuracy.isFinite() || point.accuracy !in 0.0..35.0 ||
            point.elapsed <= 0 || now-point.elapsed !in 0..15_000) return GpsUpdate()
        val last=latest
        if(last!=null && point.elapsed<=last.elapsed) return GpsUpdate()
        if(last==null || point.elapsed-last.elapsed>30_000) {
            anchor=point; latest=point
            return GpsUpdate(usable=true,gap=last!=null)
        }
        val seconds=(point.elapsed-last.elapsed)/1000.0
        if(distance(last,point)/seconds>8.0) return GpsUpdate()
        latest=point
        val origin=anchor ?: point
        val step=distance(origin,point)
        // Keep the anchor on small steps: repeated 1 m advances must accumulate.
        if(step<maxOf(2.0, maxOf(origin.accuracy,point.accuracy)*.35)) return GpsUpdate(usable=true)
        anchor=point
        return GpsUpdate(added=step,usable=true)
    }
    private fun distance(a:GpsFix,b:GpsFix):Double {
        val lat=Math.toRadians(b.latitude-a.latitude); val lon=Math.toRadians(b.longitude-a.longitude)
        val h=sin(lat/2).pow(2)+cos(Math.toRadians(a.latitude))*cos(Math.toRadians(b.latitude))*sin(lon/2).pow(2)
        return 6_371_000*2*asin(sqrt(h.coerceIn(0.0,1.0)))
    }
}

fun gpsSignal(lastFix: Long, started: Long, now: Long, enabled: Boolean): GpsSignal = when {
    !enabled -> GpsSignal.DISABLED
    now-(if(lastFix>0) lastFix else started)>30_000 -> GpsSignal.LOST
    lastFix==0L -> GpsSignal.SEARCHING
    else -> GpsSignal.GOOD
}
