package com.matheussantos.solem.domain

import org.junit.Assert.*
import org.junit.Test

class WorkoutTimingTest {
    @Test fun delayedTicksAndPausedTime() {
        assertEquals(60000L, measuredMillis(0, 1000, 61000, true))
        assertEquals(60000L, measuredMillis(60000, 1000, 200000, false))
        assertEquals(75000L, measuredMillis(60000, 200000, 215000, true))
        assertEquals("00:01:15", clockText(75))
    }
    @Test fun gpsRoundsMinutesButKeepsSeconds() {
        assertEquals(0, workoutMinutes(0))
        assertEquals(1, workoutMinutes(1))
        assertEquals(1, workoutMinutes(60))
        assertEquals(3, workoutMinutes(125))
    }
    @Test(expected = IllegalArgumentException::class) fun invalidDuration() { workoutMinutes(-1) }
}
