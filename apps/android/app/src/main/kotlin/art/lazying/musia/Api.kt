package art.lazying.musia

import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.serialization.decodeFromString
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.OkHttpClient
import okhttp3.Request

object MusiaApi {
    const val ORIGIN = "https://musia.lazying.art"
    val client = OkHttpClient.Builder().connectTimeout(12, TimeUnit.SECONDS)
        .readTimeout(20, TimeUnit.SECONDS).callTimeout(30, TimeUnit.SECONDS)
        .followSslRedirects(false).build()

    fun httpsUrl(value: String): String {
        val url = ORIGIN.toHttpUrl().resolve(value) ?: throw IOException("Invalid media URL")
        require(url.isHttps && url.username.isEmpty() && url.password.isEmpty()) { "Media must use HTTPS without credentials" }
        return url.toString()
    }

    private suspend fun get(path: String): String = withContext(Dispatchers.IO) {
        client.newCall(Request.Builder().url(ORIGIN + path).header("Accept", "application/json").build()).execute().use { response ->
            if (!response.isSuccessful) throw IOException("Service returned HTTP ${response.code}")
            val body = response.body ?: throw IOException("Empty service response")
            val source = body.source()
            source.request(8L * 1024 * 1024 + 1)
            if (source.buffer.size > 8L * 1024 * 1024) throw IOException("Service response is too large")
            source.readUtf8()
        }
    }

    suspend fun library(): Library = MusiaJson.decodeFromString<Library>(get("/api/v1/library")).also {
        require(it.version == 1) { "Unsupported library API version" }
        require(it.items.all { item -> item.id.isNotBlank() && item.title.isNotBlank() && item.duration.isFinite() && item.duration >= 0 }) { "Invalid library item" }
        require(it.items.map { item -> item.id }.distinct().size == it.items.size) { "Duplicate library IDs" }
    }

    suspend fun song(id: String): Song {
        val path = ORIGIN.toHttpUrl().newBuilder().addPathSegments("api/v1/songs").addPathSegment(id).build().encodedPath
        return MusiaJson.decodeFromString<Song>(get(path)).validated().also { song ->
            require(song.id == id) { "Song ID does not match request" }
            song.assets.forEach { httpsUrl(it.audioUrl) }
        }
    }
    suspend fun lessons(): Lessons = MusiaJson.decodeFromString(get("/api/v1/lessons"))
    suspend fun healthy(): Boolean = withContext(Dispatchers.IO) {
        client.newCall(Request.Builder().url("$ORIGIN/healthz").build()).execute().use { it.isSuccessful }
    }
}
