package art.lazying.musia

import kotlinx.serialization.Serializable
import kotlinx.serialization.SerialName
import kotlinx.serialization.json.JsonObject

@Serializable data class CreatorCapabilities(
    val login: Boolean = false, val generation: Boolean = false, val agent: Boolean = false,
    val providers: JsonObject = JsonObject(emptyMap()), val plans: List<CreatorPlan> = emptyList(),
    val termsVersion: String = "", val invitationRequired: Boolean = true, val salesEnabled: Boolean = false
)
@Serializable data class CreatorPlan(val id: String, val name: String, val renders: Int = 0)
@Serializable data class CreatorUsage(val tier: String = "free", val period: String = "", val limit: Int = 0,
    val used: Int = 0, val remaining: Int = 0, val source: String = "")
@Serializable data class CreatorAccount(val id: String, val name: String, val termsAccepted: Boolean = false,
    val invited: Boolean = false, val usage: CreatorUsage = CreatorUsage())
@Serializable data class CreatorMe(val account: CreatorAccount? = null)
@Serializable data class SongBrief(val title: String = "", val idea: String = "", val lyrics: String = "",
    val caption: String = "", val language: String = "mixed", val duration: Int = 90,
    val bpm: Int = 100, val key: String = "C major") {
    fun valid(draft: Boolean = false): Boolean =
        (draft || listOf(title, lyrics, caption).all { it.isNotBlank() }) && title.length <= 120 &&
        idea.length <= 4000 && lyrics.length <= 6000 && caption.length <= 1600 &&
        language in setOf("en", "zh", "ja", "mixed") && duration in 30..180 && bpm in 40..200 &&
        Regex("^[A-G](?:#|b)? (?:major|minor)$").matches(key)
}
@Serializable data class AgentRequest(val message: String, val brief: SongBrief)
@Serializable data class AgentReply(val message: String, val brief: SongBrief)
@Serializable data class RenderRequest(val brief: SongBrief, @SerialName("rights_confirmed") val rightsConfirmed: Boolean = true,
    val visibility: String = "private")
@Serializable data class RenderPending(val owner: String, val key: String, val body: String)
@Serializable data class CreatorJob(val id: String, val brief: SongBrief = SongBrief(), val state: String,
    val visibility: String = "private", val credit: String = "", val error: String? = null)
@Serializable data class CreatorJobs(val jobs: List<CreatorJob> = emptyList())
@Serializable data class CreatorAuthor(val id: String, val name: String)
@Serializable data class CreatorLine(val start: Double, val end: Double, val text: String, val language: String = "und")
@Serializable data class CreatorSong(val id: String, val title: String, val language: String = "und", val duration: Double,
    val author: CreatorAuthor, val mine: Boolean = false, val visibility: String, val moderation: String = "",
    val lyrics: String = "", val lyricLines: List<CreatorLine> = emptyList(), val audioUrl: String,
    val sharePath: String? = null, val liked: Boolean = false, val saved: Boolean = false, val likes: Int = 0) {
    val needsAuth: Boolean get() = visibility != "public" || moderation != "approved"
    fun asLearningSong(): Song = Song(1, "creator:$id", title, author.name, assets = listOf(
        Asset("creator-audio", "Original", language, audioUrl, duration,
            lyricTracks = lyricLines.groupBy { it.language }.map { (language, lines) ->
                LyricTrack(language, lines.mapIndexed { index, line -> Lyric("line-$index", line.start, line.end, line.text) })
            })
    )).validated()
}
@Serializable data class CreatorSongs(val songs: List<CreatorSong> = emptyList())
@Serializable data class CreatorComment(val id: String, val text: String, val author: String, val state: String, val mine: Boolean = false)
@Serializable data class CreatorComments(val comments: List<CreatorComment> = emptyList())
@Serializable data class CreatorBlocks(val accounts: List<CreatorAuthor> = emptyList())
@Serializable data class NativeStart(val attempt: String, val url: String, val expiresIn: Long)
@Serializable data class NativeToken(val token: String, val expiresIn: Long)
@Serializable data class NativeAttempt(val attempt: String, val verifier: String, val expiresAt: Long)
@Serializable data class CreatorSession(val token: String, val owner: String, val expiresAt: Long)
@Serializable data class BillingProduct(val tier: String, val googleProductId: String = "", val googleBasePlanId: String = "monthly")
@Serializable data class BillingCapability(val purchase: Boolean = false, val restore: Boolean = false, val reason: String = "")
@Serializable data class BillingCapabilities(val google: BillingCapability = BillingCapability())
@Serializable data class CreatorEntitlement(val tier: String = "free", val state: String = "unknown", val expiresAt: Long? = null,
    val provider: String? = null, val environment: String? = null)
@Serializable data class CreatorBilling(val accountToken: String, val products: List<BillingProduct> = emptyList(),
    val entitlement: CreatorEntitlement = CreatorEntitlement(), val capabilities: BillingCapabilities = BillingCapabilities())
@Serializable data class BillingVerification(val verified: Boolean = false)
@Serializable data class PurchaseJournal(val owner: String, val accountToken: String, val product: String,
    val reference: String = "", val pending: Boolean = false)
