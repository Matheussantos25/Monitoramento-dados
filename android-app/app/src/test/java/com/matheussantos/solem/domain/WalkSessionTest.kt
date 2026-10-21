package com.matheussantos.solem.domain

import kotlinx.serialization.json.Json
import org.junit.Assert.*
import org.junit.Test

class WalkSessionTest {
    private fun fix(meters:Double,time:Long,accuracy:Double=3.0)=GpsFix(0.0,
        Math.toDegrees(meters/6_371_000),accuracy,time)
    @Test fun walkingSmallStepsAccumulateInsteadOfBeingDiscarded() {
        val counter=WalkDistanceAccumulator();var total=0.0
        for(i in 0..20) total+=counter.accept(fix(i.toDouble(),1000L+i*1000),1000L+i*1000).added
        assertTrue(total in 18.0..20.1)
    }
    @Test fun straightWalkCountsExpectedDistance() {
        val counter=WalkDistanceAccumulator();var total=0.0
        for(i in 0..200) total+=counter.accept(fix(i*2.0,1000L+i*2000),1000L+i*2000).added
        assertEquals(400.0,total,2.1)
    }
    @Test fun gapPreservesTotalButDoesNotInventMissingRoute() {
        val counter=WalkDistanceAccumulator()
        counter.accept(fix(0.0,1000),1000)
        val first=counter.accept(fix(20.0,11000),11000)
        val lost=counter.accept(fix(400.0,311000),311000)
        val resumed=counter.accept(fix(410.0,316000),316000)
        assertEquals(20.0,first.added,.01)
        assertTrue(lost.gap);assertEquals(0.0,lost.added,0.0)
        assertEquals(30.0,first.added+lost.added+resumed.added,.01)
    }
    @Test fun watchdogBreakDoesNotBridgeNewPosition() {
        val counter=WalkDistanceAccumulator()
        counter.accept(fix(0.0,1000),1000);counter.breakSegment()
        assertEquals(0.0,counter.accept(fix(100.0,5000),5000).added,0.0)
    }
    @Test fun stationaryFreshFixesDoNotCountOrLoseSignal() {
        val counter=WalkDistanceAccumulator()
        for(i in 1..100) {
            val update=counter.accept(fix(0.0,i*2000L),i*2000L)
            assertTrue(update.usable);assertEquals(0.0,update.added,0.0)
            assertEquals(GpsSignal.GOOD,gpsSignal(i*2000L,1000,i*2000L,true))
        }
    }
    @Test fun jumpDoesNotPoisonNextGoodAnchor() {
        val counter=WalkDistanceAccumulator()
        counter.accept(fix(0.0,1000),1000)
        assertFalse(counter.accept(fix(1000.0,3000),3000).usable)
        assertEquals(4.0,counter.accept(fix(4.0,5000),5000).added,.01)
    }
    @Test fun staleDuplicateReorderedAndFuturePointsDoNotCount() {
        val counter=WalkDistanceAccumulator()
        counter.accept(fix(0.0,20000),20000)
        for((point,now) in listOf(fix(10.0,20000) to 20000L,fix(10.0,19000) to 20000L,
            fix(10.0,22000) to 20000L,fix(10.0,21000) to 40000L)) {
            assertFalse(counter.accept(point,now).usable)
        }
        assertEquals(4.0,counter.accept(fix(4.0,24000),24000).added,.01)
    }
    @Test fun poorAccuracyDoesNotChangeAnchor() {
        val counter=WalkDistanceAccumulator();counter.accept(fix(0.0,1000),1000)
        assertFalse(counter.accept(fix(100.0,3000,80.0),3000).usable)
        assertEquals(4.0,counter.accept(fix(4.0,5000),5000).added,.01)
    }
    @Test fun invalidCoordinatesAreRejected() {
        for(point in listOf(GpsFix(Double.NaN,0.0,3.0,1000),GpsFix(91.0,0.0,3.0,1000),
            GpsFix(0.0,181.0,3.0,1000),GpsFix(0.0,0.0,Double.NaN,1000)))
            assertFalse(WalkDistanceAccumulator().accept(point,1000).usable)
    }
    @Test fun lossAlertDoesNotRequireLocationCallback() {
        assertEquals(GpsSignal.SEARCHING,gpsSignal(0,1000,1000,true))
        assertEquals(GpsSignal.LOST,gpsSignal(0,1000,32000,true))
        assertEquals(GpsSignal.LOST,gpsSignal(2000,1000,33000,true))
        assertEquals(GpsSignal.DISABLED,gpsSignal(2000,1000,3000,false))
        assertEquals(GpsSignal.GOOD,gpsSignal(33000,1000,34000,true))
    }
    private fun session()=WalkSession(owner="account-a",active=true,pending=true,meters=1523.456,
        startedAtMillis=100000,startedElapsedMillis=1000,durationMillis=4000,bootCount=7)
    @Test fun processDeathRestoresTotalsAndMarksInterruption() {
        val restored=session().recovered(11000,7)
        assertFalse(restored.active);assertTrue(restored.pending);assertTrue(restored.hasGap)
        assertEquals(1523.456,restored.meters,0.0);assertEquals(10000L,restored.durationMillis)
        assertEquals(GpsSignal.INTERRUPTED,restored.signal)
    }
    @Test fun rebootUsesCheckpointInsteadOfSubtractingDifferentClocks() {
        val restored=session().recovered(500,8)
        assertEquals(4000L,restored.durationMillis)
        assertEquals(5000L,restored.copy(active=true).duration(1500))
    }
    @Test fun stoppedSessionDoesNotResumeOrAccumulateOfflineTime() {
        val restored=session().copy(active=false,pending=false).recovered(11000,7)
        assertFalse(restored.pending);assertEquals(4000L,restored.duration(99999))
        assertEquals(GpsSignal.STOPPED,restored.signal)
    }
    @Test fun snapshotRoundTripStoresTotalsNotCoordinates() {
        val json=Json.encodeToString(session())
        assertEquals(session(),Json.decodeFromString<WalkSession>(json))
        assertFalse(json.contains("latitude"));assertFalse(json.contains("longitude"))
        assertEquals("account-a",Json.decodeFromString<WalkSession>(json).owner)
    }
}
