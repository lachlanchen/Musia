package art.lazying.musia

import android.content.Context
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.AtomicFile
import java.io.File
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.serialization.Serializable
import kotlinx.serialization.encodeToString

@Serializable data class CreatorSecrets(
    val session: CreatorSession? = null, val attempt: NativeAttempt? = null,
    val renders: Map<String, RenderPending> = emptyMap(), val drafts: Map<String, SongBrief> = emptyMap(),
    val purchases: List<PurchaseJournal> = emptyList(), val revocations: List<String> = emptyList()
)

/** Only ciphertext is stored on disk. The AES key is non-exportable in Android Keystore. */
class CreatorVault private constructor(context: Context) {
    private val file = AtomicFile(File(context.noBackupFilesDir, "creator-v1.enc"))
    private val alias = "musia.creator.v1"
    var warning: String? = null
        private set
    private fun key(): SecretKey {
        val ks = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }
        return (ks.getKey(alias, null) as? SecretKey) ?: KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore").run {
            init(KeyGenParameterSpec.Builder(alias, KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT)
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM).setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setRandomizedEncryptionRequired(true).build())
            generateKey()
        }
    }
    private fun read(): CreatorSecrets = try {
        if (!file.baseFile.exists() && !File(file.baseFile.path + ".bak").exists() && !File(file.baseFile.path + ".new").exists()) CreatorSecrets() else {
            val bytes = file.readFully()
            require(bytes.size > 28 && bytes.size < 2_000_000)
            val cipher = Cipher.getInstance("AES/GCM/NoPadding")
            cipher.init(Cipher.DECRYPT_MODE, key(), GCMParameterSpec(128, bytes.copyOfRange(0, 12)))
            cipher.updateAAD(alias.toByteArray())
            MusiaJson.decodeFromString<CreatorSecrets>(cipher.doFinal(bytes.copyOfRange(12, bytes.size)).toString(Charsets.UTF_8))
        }
    } catch (_: Exception) {
        // Do not overwrite an unreadable journal: that could permit a duplicate purchase/render.
        warning = "Protected account data could not be opened. Creator actions are paused; public listening remains available."
        CreatorSecrets()
    }
    private val mutable = MutableStateFlow(read())
    val state = mutable.asStateFlow()
    @Synchronized fun update(change: (CreatorSecrets) -> CreatorSecrets) {
        check(warning == null) { "Protected storage unavailable" }
        val next = change(mutable.value)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key())
        cipher.updateAAD(alias.toByteArray())
        val encrypted = cipher.iv + cipher.doFinal(MusiaJson.encodeToString(next).toByteArray())
        val stream = file.startWrite()
        try { stream.write(encrypted); file.finishWrite(stream) }
        catch (error: Exception) { file.failWrite(stream); throw error }
        mutable.value = next
    }
    companion object {
        @Volatile private var instance: CreatorVault? = null
        fun get(context: Context): CreatorVault = instance ?: synchronized(this) {
            instance ?: CreatorVault(context.applicationContext).also { instance = it }
        }
    }
}
