package art.lazying.musia

import java.net.URI
import java.net.URLDecoder
import java.security.MessageDigest
import java.security.SecureRandom
import java.util.Base64

object CreatorRules {
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
