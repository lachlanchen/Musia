package art.lazying.musia

import android.content.Context
import android.net.Uri
import androidx.media3.datasource.DataSource
import androidx.media3.datasource.DataSpec
import androidx.media3.datasource.DefaultDataSource
import androidx.media3.datasource.TransferListener
import androidx.media3.datasource.okhttp.OkHttpDataSource
import java.io.IOException
import java.util.concurrent.ConcurrentHashMap
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Response

/** Credentials never go in MediaItem metadata, URLs, disk caches or public media requests. */
@androidx.annotation.OptIn(androidx.media3.common.util.UnstableApi::class)
object CreatorAudio {
    private val owners = ConcurrentHashMap<String, String>()
    fun register(song: CreatorSong, session: CreatorSession?) {
        val url = CreatorApi.originUrl(song.audioUrl)
        require(url == MusiaApi.ORIGIN + "/creator" + CreatorApi.path("api", "songs", song.id, "audio"))
        if (song.needsAuth) {
            requireNotNull(session)
            require(song.mine)
            owners[url] = session.owner
        } else owners.remove(url)
    }
    class Headers(private val vault: CreatorVault) : Interceptor {
        override fun intercept(chain: Interceptor.Chain): Response {
            val request = chain.request()
            val owner = owners[request.url.toString()] ?: return chain.proceed(request)
            // The client disables redirects, so a token cannot follow a redirect to another resource.
            CreatorApi.originUrl(request.url.toString())
            val session = vault.state.value.session
            if (session == null || session.owner != owner || session.expiresAt <= System.currentTimeMillis()) throw IOException("Private audio requires the original account")
            return chain.proceed(request.newBuilder().header("Authorization", "Bearer ${session.token}")
                .header("X-Musia-Request", "1").build())
        }
    }
    class Sources(context: Context, vault: CreatorVault) : DataSource.Factory {
        private val publicSource = DefaultDataSource.Factory(context)
        private val privateSource = OkHttpDataSource.Factory(OkHttpClient.Builder()
            .followRedirects(false).followSslRedirects(false).addInterceptor(Headers(vault)).build())
        override fun createDataSource(): DataSource = object : DataSource {
            private var active: DataSource? = null
            private val listeners = mutableListOf<TransferListener>()
            override fun addTransferListener(listener: TransferListener) { listeners += listener; active?.addTransferListener(listener) }
            override fun open(dataSpec: DataSpec): Long {
                val source = if (owners.containsKey(dataSpec.uri.toString())) privateSource.createDataSource() else publicSource.createDataSource()
                active = source
                listeners.forEach(source::addTransferListener)
                return source.open(dataSpec)
            }
            override fun read(buffer: ByteArray, offset: Int, length: Int): Int = checkNotNull(active).read(buffer, offset, length)
            override fun getUri(): Uri? = active?.uri
            override fun getResponseHeaders(): Map<String, List<String>> = active?.responseHeaders.orEmpty()
            override fun close() { try { active?.close() } finally { active = null } }
        }
    }
}
