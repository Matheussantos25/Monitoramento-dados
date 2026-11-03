package com.matheussantos.solem.viewmodel

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.matheussantos.solem.domain.*
import io.github.jan.supabase.SupabaseClient
import io.github.jan.supabase.auth.auth
import io.github.jan.supabase.postgrest.from
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.json.*

data class MenuState(val tabs:Set<String>,val loaded:Boolean=false,val busy:Boolean=false,
    val configured:Boolean=false,val error:String?=null,val message:String?=null)

/** Session-scoped; preserves unrelated JSON preferences and rejects revision conflicts. */
class MenuViewModel(private val client:SupabaseClient,private val owner:String,private val generic:Boolean):ViewModel() {
    private val mutableState=MutableStateFlow(MenuState(menuTabs(null,generic)))
    val state=mutableState.asStateFlow()
    init {reload()}
    private fun checkOwner() {check(client.auth.currentUserOrNull()?.id==owner) {"Entre novamente para carregar suas abas."}}
    private suspend fun fetch():JsonObject? {
        checkOwner()
        return client.from("solem_journey_settings").select {filter {eq("owner_id",owner)}}.decodeList<JsonObject>().singleOrNull()
    }
    private fun received(row:JsonObject?) {
        val prefs=row?.get("preferences") as? JsonObject
        val saved=(prefs?.get("menu_tabs") as? JsonArray)?.mapNotNull {(it as? JsonPrimitive)?.contentOrNull}
        mutableState.value=MenuState(menuTabs(saved,generic),loaded=true,configured=(prefs?.get("menu_done") as? JsonPrimitive)?.booleanOrNull==true)
    }
    fun reload() {
        if(state.value.busy)return
        mutableState.value=state.value.copy(busy=true,error=null,message=null)
        viewModelScope.launch {
            try {received(fetch())}
            catch(e:CancellationException){throw e}
            catch(_:Exception){mutableState.value=state.value.copy(busy=false,error="Não foi possível carregar suas abas. Tente novamente.")}
        }
    }
    fun save(selected:Set<String>,done:()->Unit={}) {
        if(state.value.busy || !state.value.loaded)return
        mutableState.value=state.value.copy(busy=true,error=null,message=null)
        viewModelScope.launch {
            try {
                val old=fetch()
                val previous=old?.get("preferences") as? JsonObject ?: buildJsonObject {}
                val saved=(previous["menu_tabs"] as? JsonArray)?.mapNotNull {(it as? JsonPrimitive)?.contentOrNull}
                val values=mergedMenuTabs(selected,menuTabs(saved,generic),androidTabIds.toSet()-pinnedTabs)
                val prefs=JsonObject(previous+mapOf("menu_tabs" to JsonArray(values.map(::JsonPrimitive)),"menu_done" to JsonPrimitive(true)))
                val payload=buildJsonObject {put("preferences",prefs)}
                checkOwner()
                val rows=if(old==null) client.from("solem_journey_settings").insert(payload){select()}.decodeList<JsonObject>()
                else client.from("solem_journey_settings").update(payload) {
                    select();filter {eq("owner_id",owner);eq("revision",old.getValue("revision").jsonPrimitive.long)}
                }.decodeList<JsonObject>()
                require(rows.size==1) {"Atualize suas abas antes de salvar novamente."}
                checkOwner();received(rows.single())
                mutableState.value=state.value.copy(message="Abas salvas na sua conta.")
                done()
            } catch(e:CancellationException){throw e}
            catch(_:Exception){mutableState.value=state.value.copy(busy=false,error="Não foi possível confirmar. Atualize as abas antes de tentar novamente.")}
        }
    }
}
