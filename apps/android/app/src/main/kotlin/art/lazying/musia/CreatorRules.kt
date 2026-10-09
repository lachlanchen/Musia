package art.lazying.musia

import java.net.URI
import java.net.URLDecoder
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Base64
import kotlinx.serialization.encodeToString

object CreatorRules {
    fun boundedHistory(messages: List<AgentMessage>): List<AgentMessage> {
        val result = messages.filter { it.role in setOf("user", "assistant") && it.content.isNotBlank() }
            .map { it.copy(content = it.content.take(4000)) }.takeLast(12).toMutableList()
        while (result.sumOf { it.content.length } > 16000) result.removeAt(0)
        return result
    }

    fun agentBody(message: String, brief: SongBrief, messages: List<AgentMessage>): String? {
        val history = boundedHistory(messages).toMutableList()
        while (true) {
            val body = MusiaJson.encodeToString(AgentRequest(message, brief, history))
            if (body.toByteArray(Charsets.UTF_8).size <= 45000) return body
            if (history.isEmpty()) return null
            history.removeAt(0)
        }
    }

    fun changedFields(before: SongBrief, after: SongBrief): Set<String> = buildSet {
        if (before.title != after.title) add("title")
        if (before.idea != after.idea) add("idea")
        if (before.lyrics != after.lyrics) add("lyrics")
        if (before.caption != after.caption) add("caption")
        if (before.language != after.language) add("language")
        if (before.duration != after.duration) add("duration")
        if (before.bpm != after.bpm) add("bpm")
        if (before.key != after.key) add("key")
    }

    /** Even a field edited and reverted while waiting remains under manual control. */
    fun mergeAgent(current: SongBrief, reply: SongBrief, edited: Set<String>): SongBrief = reply.copy(
        title = if ("title" in edited) current.title else reply.title,
        idea = if ("idea" in edited) current.idea else reply.idea,
        lyrics = if ("lyrics" in edited) current.lyrics else reply.lyrics,
        caption = if ("caption" in edited) current.caption else reply.caption,
        language = if ("language" in edited) current.language else reply.language,
        duration = if ("duration" in edited) current.duration else reply.duration,
        bpm = if ("bpm" in edited) current.bpm else reply.bpm,
        key = if ("key" in edited) current.key else reply.key
    )

    fun verifier(): String = Base64.getUrlEncoder().withoutPadding().encodeToString(ByteArray(32).also { SecureRandom().nextBytes(it) })
    fun challenge(verifier: String): String = Base64.getUrlEncoder().withoutPadding()
        .encodeToString(MessageDigest.getInstance("SHA-256").digest(verifier.toByteArray(Charsets.US_ASCII)))

    /** Reject duplicate parameters, userinfo, paths, ports, fragments and replayed/expired attempts. */
    fun callback(value: String, expected: NativeAttempt, now: Long): String? = runCatching {
        val uri = URI(value)
        require(uri.scheme == "art.lazying.musia" && uri.rawAuthority == "auth" && uri.rawPath.orEmpty().isEmpty() && uri.rawFragment == null)
        require(now < expected.expiresAt)
        val entries = uri.rawQuery.orEmpty().split('&').map { entry ->
            val pair = entry.split('=', limit = 2)
            require(pair.size == 2)
            URLDecoder.decode(pair[0], "UTF-8") to URLDecoder.decode(pair[1], "UTF-8")
        }
        require(entries.size == 2 && entries.map { it.first }.toSet() == setOf("attempt", "code"))
        val params = entries.toMap()
        require(params["attempt"] == expected.attempt)
        params.getValue("code").also { require(it.isNotBlank() && it.length <= 512) }
    }.getOrNull()

    fun canCreate(account: CreatorAccount?, caps: CreatorCapabilities?): Boolean = account != null && caps != null &&
        account.termsAccepted && (!caps.invitationRequired || account.invited)

    fun canBuy(salesEnabled: Boolean, serverEnabled: Boolean, ownedQueryComplete: Boolean,
        hasOwned: Boolean, unresolved: Boolean, entitlementState: String): Boolean =
        salesEnabled && serverEnabled && ownedQueryComplete && !hasOwned && !unresolved &&
            entitlementState in setOf("none", "expired", "revoked", "free")

    fun purchaseBelongs(accountToken: String, purchaseAccountToken: String?): Boolean =
        accountToken.isNotBlank() && purchaseAccountToken == accountToken

    fun current(captured: CreatorSession?, current: CreatorSession?, epoch: Long, currentEpoch: Long): Boolean =
        epoch == currentEpoch && captured == current

    fun retry(pending: RenderPending?, session: CreatorSession): RenderPending? = pending?.takeIf { it.owner == session.owner }
    fun definitiveRenderRejection(initial: Boolean, status: Int): Boolean = initial && status in setOf(400, 401, 403, 422, 429)
}
