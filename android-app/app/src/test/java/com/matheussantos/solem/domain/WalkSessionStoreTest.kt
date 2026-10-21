package com.matheussantos.solem.domain

import android.content.SharedPreferences
import com.matheussantos.solem.data.WalkSessionStore
import org.junit.Assert.*
import org.junit.Test

class WalkSessionStoreTest {
    private class MemoryPrefs:SharedPreferences {
        val values=mutableMapOf<String,String?>()
        var fail=false
        override fun getString(key:String?,defValue:String?)=values[key] ?: defValue
        override fun contains(key:String?)=values.containsKey(key)
        override fun getAll():MutableMap<String,*> = values
        override fun edit():SharedPreferences.Editor=object:SharedPreferences.Editor {
            val pending=mutableMapOf<String,String?>();var clear=false
            override fun putString(key:String?,value:String?)=apply {pending[key!!]=value}
            override fun remove(key:String?)=apply {pending[key!!]=null}
            override fun clear()=apply {clear=true}
            override fun commit():Boolean {
                if(fail)return false
                if(clear)values.clear()
                pending.forEach {(key,value)->if(value==null)values.remove(key) else values[key]=value}
                return true
            }
            override fun apply() {commit()}
            override fun putStringSet(key:String?,values:MutableSet<String>?)=error("unused")
            override fun putInt(key:String?,value:Int)=error("unused")
            override fun putLong(key:String?,value:Long)=error("unused")
            override fun putFloat(key:String?,value:Float)=error("unused")
            override fun putBoolean(key:String?,value:Boolean)=error("unused")
        }
        override fun getStringSet(key:String?,defValues:MutableSet<String>?)=defValues
        override fun getInt(key:String?,defValue:Int)=defValue
        override fun getLong(key:String?,defValue:Long)=defValue
        override fun getFloat(key:String?,defValue:Float)=defValue
        override fun getBoolean(key:String?,defValue:Boolean)=defValue
        override fun registerOnSharedPreferenceChangeListener(listener:SharedPreferences.OnSharedPreferenceChangeListener?) {}
        override fun unregisterOnSharedPreferenceChangeListener(listener:SharedPreferences.OnSharedPreferenceChangeListener?) {}
    }
    @Test fun newStoreRecoversCommittedTotalsAfterProcessLoss() {
        val prefs=MemoryPrefs();val session=WalkSession(owner="a",active=true,pending=true,meters=1234.567)
        assertTrue(WalkSessionStore(prefs).save(session))
        assertEquals(session,WalkSessionStore(prefs).active())
        assertEquals(1234.567,WalkSessionStore(prefs).read("a")!!.meters,0.0)
    }
    @Test fun accountsNeverReadEachOthersCheckpoint() {
        val store=WalkSessionStore(MemoryPrefs())
        store.save(WalkSession(owner="a",meters=100.0))
        assertNull(store.read("b"));assertNull(store.read(""))
        store.save(WalkSession(owner="b",meters=20.0))
        assertEquals(100.0,store.read("a")!!.meters,0.0)
        assertEquals(20.0,store.read("b")!!.meters,0.0)
    }
    @Test fun explicitStopClearsRestartButKeepsFinishedDistance() {
        val store=WalkSessionStore(MemoryPrefs())
        val active=WalkSession(owner="a",active=true,pending=true,meters=321.0)
        store.save(active);store.save(active.copy(active=false,pending=false))
        assertNull(store.active());assertEquals(321.0,store.read("a")!!.meters,0.0)
    }
    @Test fun failurePreservesLastDurableValueAndIsReported() {
        val prefs=MemoryPrefs();val store=WalkSessionStore(prefs)
        store.save(WalkSession(owner="a",meters=42.0));prefs.fail=true
        assertFalse(store.save(WalkSession(owner="a",meters=50.0)))
        assertEquals(42.0,store.read("a")!!.meters,0.0)
    }
    @Test fun corruptedOrMismatchedSnapshotIsNotRestored() {
        val prefs=MemoryPrefs();val store=WalkSessionStore(prefs)
        prefs.values["session_a"]="broken";assertNull(store.read("a"))
        store.save(WalkSession(owner="b",meters=50.0))
        prefs.values["session_a"]=prefs.values["session_b"];assertNull(store.read("a"))
    }
}
