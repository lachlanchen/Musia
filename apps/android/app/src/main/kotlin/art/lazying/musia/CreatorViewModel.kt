package art.lazying.musia

import android.app.Application
import android.content.Context
import android.net.Uri
import androidx.browser.customtabs.CustomTabsIntent
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import java.io.IOException
import java.util.UUID
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.launch
import kotlinx.serialization.encodeToString
import kotlinx.serialization.json.JsonPrimitive

class CreatorViewModel(application: Application) : AndroidViewModel(application) {
    val vault = CreatorVault.get(application)
    val billing = CreatorPlayBilling(application, vault, viewModelScope) { refreshAccount() }
    var capabilities by mutableStateOf<CreatorCapabilities?>(null); private set
    var account by mutableStateOf<CreatorAccount?>(null); private set
    var accountEpoch by mutableStateOf(0L); private set
    var busy by mutableStateOf(false); private set
    var message by mutableStateOf<String?>(vault.warning); private set
    var brief by mutableStateOf(SongBrief()); private set
    var agentReply by mutableStateOf(""); private set
    var pending by mutableStateOf<RenderPending?>(null); private set
    var jobs by mutableStateOf<List<CreatorJob>>(emptyList()); private set
    var songs by mutableStateOf(LoadState<List<CreatorSong>>()); private set
    var mode by mutableStateOf("public"); private set
    var selected by mutableStateOf<CreatorSong?>(null); private set
    var comments by mutableStateOf(LoadState<List<CreatorComment>>()); private set
    var blocks by mutableStateOf<List<CreatorAuthor>>(emptyList()); private set
    private var songSequence = 0L
    private var commentSequence = 0L
    private var accountSequence = 0L
    private var exchanging = false
    private val session: CreatorSession? get() = vault.state.value.session
    val canCreate: Boolean get() = CreatorRules.canCreate(account, capabilities) && !busy && vault.warning == null
    init { refresh(); refreshSongs("public") }

    private fun current(epoch: Long, captured: CreatorSession?): Boolean = CreatorRules.current(captured, session, epoch, accountEpoch)
    private fun requireCurrent(epoch: Long, captured: CreatorSession?) {
        if (!current(epoch, captured)) throw CancellationException("Account changed")
    }
    private fun error(error: Exception) {
        if (error is CancellationException) throw error
        message = when (error) {
            is CreatorApiError -> "Service: ${error.code.replace('_', ' ')}. Refresh or retry when available."
            is IOException -> "Connection interrupted. Refresh to check the result before trying again."
            else -> "This action could not be completed. Refresh and check your account."
        }
    }
    private fun action(work: suspend (CreatorSession?, Long) -> Unit) {
        if (busy || vault.warning != null) return
        val captured = session
        val epoch = accountEpoch
        busy = true
        message = null
        viewModelScope.launch {
            try { work(captured, epoch) }
            catch (e: Exception) { if (current(epoch, captured)) error(e) else if (e is CancellationException) throw e }
            finally { if (epoch == accountEpoch) busy = false }
        }
    }
    fun refresh() {
        viewModelScope.launch {
            try { capabilities = CreatorApi.get("/api/capabilities"); refreshAccount() }
            catch (e: Exception) { capabilities = null; error(e) }
        }
        refreshAccount()
        retryRevocations()
    }
    fun refreshAccount() {
        val captured = session ?: return
        val epoch = accountEpoch
        val sequence = ++accountSequence
        viewModelScope.launch {
            try {
                val value = CreatorApi.get<CreatorMe>("/api/me", captured).account
                requireCurrent(epoch, captured)
                if (sequence != accountSequence) return@launch
                if (value == null || value.id != captured.owner || captured.expiresAt <= System.currentTimeMillis()) {
                    clearAccount("Sign in again to continue creating."); return@launch
                }
                val firstLoad = account == null
                account = value
                if (firstLoad) brief = vault.state.value.drafts[value.id] ?: SongBrief()
                pending = vault.state.value.renders[value.id]
                val data = CreatorApi.get<CreatorBilling>("/api/billing", captured)
                requireCurrent(epoch, captured)
                if (sequence != accountSequence) return@launch
                billing.bind(captured, data, capabilities?.salesEnabled == true)
            } catch (e: Exception) {
                if (current(epoch, captured) && sequence == accountSequence) {
                    if (e is CreatorApiError && e.status == 401) clearAccount("Sign in again to continue creating.")
                    else { billing.unavailable(); error(e) }
                }
            }
        }
    }
    fun startLogin(context: Context) = action { _, epoch ->
        check(account == null && session == null && capabilities?.login == true)
        val verifier = CreatorRules.verifier()
        val body = CreatorApi.fields("challenge" to JsonPrimitive(CreatorRules.challenge(verifier)), "platform" to JsonPrimitive("android"))
        val start = MusiaJson.decodeFromString<NativeStart>(CreatorApi.request("/auth/native/start", method = "POST", body = body))
        requireCurrent(epoch, null)
        val url = CreatorApi.originUrl(start.url)
        require(start.attempt.isNotBlank() && start.expiresIn in 1..600)
        vault.update { it.copy(attempt = NativeAttempt(start.attempt, verifier, System.currentTimeMillis() + start.expiresIn * 1000)) }
        CustomTabsIntent.Builder().setShowTitle(true).build().launchUrl(context, Uri.parse(url))
    }
    fun completeLogin(uri: String) {
        val attempt = vault.state.value.attempt ?: return
        val code = CreatorRules.callback(uri, attempt, System.currentTimeMillis()) ?: run {
            message = "Sign-in return was invalid or expired. Start sign-in again."; return
        }
        if (exchanging || session != null) return
        exchanging = true
        busy = true
        val epoch = accountEpoch
        viewModelScope.launch {
            try {
                // Consume locally before exchange. An uncertain exchange requires a fresh browser attempt.
                vault.update { it.copy(attempt = null) }
                val body = CreatorApi.fields("attempt" to JsonPrimitive(attempt.attempt), "code" to JsonPrimitive(code),
                    "verifier" to JsonPrimitive(attempt.verifier), "platform" to JsonPrimitive("android"))
                val token = MusiaJson.decodeFromString<NativeToken>(CreatorApi.request("/auth/native/exchange", method = "POST", body = body))
                requireCurrent(epoch, null)
                require(token.token.isNotBlank() && token.expiresIn > 0)
                val provisional = CreatorSession(token.token, "", System.currentTimeMillis() + token.expiresIn.coerceAtMost(604800) * 1000)
                val value = CreatorApi.get<CreatorMe>("/api/me", provisional).account ?: throw IOException("Account unavailable")
                requireCurrent(epoch, null)
                require(value.id.isNotBlank())
                vault.update { it.copy(session = provisional.copy(owner = value.id)) }
                accountEpoch++
                account = value
                brief = vault.state.value.drafts[value.id] ?: SongBrief()
                pending = vault.state.value.renders[value.id]
                message = "Signed in. Public listening and practice remain available to everyone."
                refreshAccount(); refreshJobs(); refreshSongs(mode)
            } catch (e: Exception) { if (epoch == accountEpoch) error(e) }
            finally { exchanging = false; busy = false }
        }
    }
    private fun clearAccount(notice: String) {
        vault.update { it.copy(session = null, attempt = null) }
        accountEpoch++; account = null; busy = false; brief = SongBrief(); pending = null
        jobs = emptyList(); blocks = emptyList(); selected = null; comments = LoadState(); agentReply = ""
        billing.unbind(); message = notice; refreshSongs("public")
    }
    fun logout() {
        val token = session?.token
        vault.update { it.copy(revocations = (it.revocations + listOfNotNull(token)).distinct()) }
        clearAccount("Signed out on this device. Server sign-out will retry if the connection is unavailable.")
        retryRevocations()
    }
    private fun retryRevocations() {
        viewModelScope.launch {
            vault.state.value.revocations.forEach { token ->
                try {
                    CreatorApi.request("/auth/logout", CreatorSession(token, "", 0), "POST")
                    vault.update { it.copy(revocations = it.revocations - token) }
                } catch (e: Exception) { if (e is CancellationException) throw e }
            }
        }
    }
    fun deleteAccount() = action { captured, epoch ->
        requireNotNull(captured)
        CreatorApi.request("/api/me", captured, "DELETE")
        requireCurrent(epoch, captured)
        vault.update { it.copy(renders = it.renders - captured.owner, drafts = it.drafts - captured.owner,
            purchases = it.purchases.filterNot { purchase -> purchase.owner == captured.owner }) }
        clearAccount("Account deleted. Store subscriptions must be cancelled separately in Google Play. Media cleanup may take time.")
    }
    fun acceptTerms() = accountMutation("/api/terms")
    fun redeem(code: String) = accountMutation("/api/invitations/redeem", CreatorApi.fields("code" to JsonPrimitive(code.trim())))
    private fun accountMutation(path: String, body: String = "{}") = action { captured, epoch ->
        requireNotNull(captured)
        CreatorApi.request(path, captured, "POST", body)
        requireCurrent(epoch, captured); refreshAccount()
    }
    fun edit(value: SongBrief) {
        if (busy) return
        brief = value
        account?.id?.let { owner ->
            try { vault.update { it.copy(drafts = it.drafts + (owner to value)) } } catch (e: Exception) { error(e) }
        }
    }
    fun askAgent(message: String) = action { captured, epoch ->
        requireNotNull(captured)
        check(CreatorRules.canCreate(account, capabilities) && capabilities?.agent == true && brief.valid(true) && message.isNotBlank() && message.length <= 4000)
        val reply = MusiaJson.decodeFromString<AgentReply>(CreatorApi.request("/api/agent", captured, "POST", MusiaJson.encodeToString(AgentRequest(message, brief))))
        requireCurrent(epoch, captured)
        require(reply.brief.valid(true))
        brief = reply.brief; agentReply = reply.message
        vault.update { it.copy(drafts = it.drafts + (captured.owner to reply.brief)) }
    }
    fun render(visibility: String) = action { captured, epoch ->
        requireNotNull(captured)
        check(CreatorRules.canCreate(account, capabilities) && capabilities?.generation == true && account!!.usage.remaining > 0)
        check(pending == null && brief.valid() && visibility in setOf("private", "public"))
        val request = RenderPending(captured.owner, UUID.randomUUID().toString(), MusiaJson.encodeToString(RenderRequest(brief, visibility = visibility)))
        vault.update { it.copy(renders = it.renders + (captured.owner to request)) }
        pending = request
        sendRender(captured, epoch, request, initial = true)
    }
    fun retryRender() = action { captured, epoch ->
        requireNotNull(captured)
        val request = CreatorRules.retry(vault.state.value.renders[captured.owner], captured) ?: return@action
        sendRender(captured, epoch, request)
    }
    private suspend fun sendRender(captured: CreatorSession, epoch: Long, request: RenderPending, initial: Boolean = false) {
        try {
            val job = MusiaJson.decodeFromString<CreatorJob>(CreatorApi.request("/api/jobs", captured, "POST", request.body, request.key))
            requireCurrent(epoch, captured)
            require(job.id.isNotBlank())
            vault.update { it.copy(renders = it.renders - captured.owner) }
            pending = null; message = "Render queued. Refresh jobs to follow its progress."
            refreshJobs(); refreshAccount()
        } catch (e: CreatorApiError) {
            // Definitive pre-admission failures can be edited; conflicts/5xx remain unresolved.
            if (CreatorRules.definitiveRenderRejection(initial, e.status)) {
                requireCurrent(epoch, captured)
                vault.update { it.copy(renders = it.renders - captured.owner) }; pending = null
            }
            throw e
        }
    }
    fun refreshJobs() {
        val captured = session ?: return
        val epoch = accountEpoch
        viewModelScope.launch {
            try {
                val result = CreatorApi.get<CreatorJobs>("/api/jobs", captured)
                requireCurrent(epoch, captured); jobs = result.jobs
            } catch (e: Exception) { if (current(epoch, captured)) error(e) }
        }
    }
    fun cancel(job: CreatorJob) = action { captured, epoch ->
        requireNotNull(captured); check(job.state == "queued")
        CreatorApi.request(CreatorApi.path("api", "jobs", job.id, "cancel"), captured, "POST")
        requireCurrent(epoch, captured); refreshJobs(); refreshAccount()
    }
    fun refreshSongs(value: String = mode) {
        if (value !in setOf("public", "mine", "saved") || value != "public" && account == null) return
        mode = value
        val sequence = ++songSequence
        val epoch = accountEpoch
        val captured = session
        songs = LoadState(loading = true)
        viewModelScope.launch {
            try {
                val result = CreatorApi.get<CreatorSongs>("/api/songs?mode=$value", captured)
                requireCurrent(epoch, captured)
                if (sequence == songSequence) songs = LoadState(value = result.songs)
            } catch (e: Exception) {
                if (current(epoch, captured) && sequence == songSequence) {
                    if (e is CancellationException) throw e
                    songs = LoadState(error = "Songs could not be loaded. Check the connection and refresh.")
                }
            }
        }
    }
    fun select(song: CreatorSong?) {
        selected = song; comments = LoadState(); ++commentSequence
        if (song != null) refreshComments()
    }
    fun openAudio(song: CreatorSong, play: (CreatorSong, CreatorSession?) -> Unit) = action { captured, epoch ->
        val fresh = CreatorApi.get<CreatorSong>(CreatorApi.path("api", "songs", song.id), captured)
        requireCurrent(epoch, captured)
        if (fresh.needsAuth) require(captured != null && fresh.mine)
        CreatorApi.originUrl(fresh.audioUrl)
        play(fresh, if (fresh.needsAuth) captured else null)
    }
    fun refreshComments() {
        val song = selected ?: return
        val sequence = ++commentSequence
        val epoch = accountEpoch; val captured = session
        comments = LoadState(loading = true)
        viewModelScope.launch {
            try {
                val result = CreatorApi.get<CreatorComments>(CreatorApi.path("api", "songs", song.id, "comments"), captured)
                requireCurrent(epoch, captured)
                if (sequence == commentSequence && selected?.id == song.id) comments = LoadState(value = result.comments)
            } catch (e: Exception) {
                if (current(epoch, captured) && sequence == commentSequence) {
                    if (e is CancellationException) throw e
                    comments = LoadState(error = "Comments unavailable. Refresh to retry.")
                }
            }
        }
    }
    fun react(song: CreatorSong, kind: String) = songMutation(song, "reactions/$kind", CreatorApi.fields("active" to JsonPrimitive(if (kind == "like") !song.liked else !song.saved)))
    fun visibility(song: CreatorSong, value: String) = songMutation(song, "visibility", CreatorApi.fields("visibility" to JsonPrimitive(value)))
    fun comment(song: CreatorSong, text: String) = songMutation(song, "comments", CreatorApi.fields("text" to JsonPrimitive(text)))
    fun report(song: CreatorSong, reason: String) = songMutation(song, "reports", CreatorApi.fields("reason" to JsonPrimitive(reason)))
    private fun songMutation(song: CreatorSong, suffix: String, body: String) = action { captured, epoch ->
        requireNotNull(captured)
        CreatorApi.request(CreatorApi.path("api", "songs", song.id, *suffix.split('/').toTypedArray()), captured, "POST", body)
        requireCurrent(epoch, captured)
        val fresh = CreatorApi.get<CreatorSong>(CreatorApi.path("api", "songs", song.id), captured)
        requireCurrent(epoch, captured)
        if (selected?.id == song.id) { selected = fresh; refreshComments() }
        refreshSongs(); message = if (suffix == "comments") "Comment submitted for moderation. Refresh before retrying." else "Saved."
    }
    fun deleteComment(id: String) = action { captured, epoch ->
        requireNotNull(captured)
        CreatorApi.request(CreatorApi.path("api", "comments", id), captured, "DELETE")
        requireCurrent(epoch, captured); refreshComments()
    }
    fun block(id: String, active: Boolean) = action { captured, epoch ->
        requireNotNull(captured)
        CreatorApi.request(CreatorApi.path("api", "accounts", id, "block"), captured, "POST", CreatorApi.fields("active" to JsonPrimitive(active)))
        requireCurrent(epoch, captured); select(null); refreshSongs(); refreshBlocks()
    }
    fun refreshBlocks() {
        val captured = session ?: return; val epoch = accountEpoch
        viewModelScope.launch {
            try {
                val result = CreatorApi.get<CreatorBlocks>("/api/blocks", captured)
                requireCurrent(epoch, captured); blocks = result.accounts
            } catch (e: Exception) { if (current(epoch, captured)) error(e) }
        }
    }
    override fun onCleared() { billing.close(); super.onCleared() }
}
