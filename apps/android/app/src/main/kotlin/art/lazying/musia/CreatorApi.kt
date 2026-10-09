package art.lazying.musia

import java.io.IOException
import java.util.concurrent.TimeUnit
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.withContext
import kotlinx.serialization.json.*
import okhttp3.HttpUrl.Companion.toHttpUrl
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody

class CreatorApiError(val status: Int, val code: String) : IOException(code)

object CreatorApi {
    private val client = OkHttpClient.Builder().connectTimeout(12, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS).callTimeout(75, TimeUnit.SECONDS)
        .followRedirects(false).followSslRedirects(false).retryOnConnectionFailure(false).build()
    fun path(vararg segments: String): String = MusiaApi.ORIGIN.toHttpUrl().newBuilder()
        .addPathSegment("creator").apply { segments.forEach(::addPathSegment) }.build().encodedPath.removePrefix("/creator")
    fun originUrl(value: String): String {
        val origin = MusiaApi.ORIGIN.toHttpUrl()
        val url = origin.resolve(value) ?: throw IOException("Invalid service URL")
        require(url.isHttps && url.host == origin.host && url.port == origin.port && url.username.isEmpty() && url.password.isEmpty())
        return url.toString()
    }
    suspend fun request(path: String, session: CreatorSession? = null, method: String = "GET", body: String = "{}", key: String? = null): String = withContext(Dispatchers.IO) {
        require(path.startsWith("/") && !path.startsWith("//"))
        val builder = Request.Builder().url(MusiaApi.ORIGIN + "/creator" + path)
            .header("Accept", "application/json").header("X-Musia-Request", "1")
        session?.let { builder.header("Authorization", "Bearer ${it.token}") }
        key?.let { builder.header("Idempotency-Key", it) }
        if (method != "GET") builder.method(method, body.toRequestBody("application/json".toMediaType()))
        client.newCall(builder.build()).execute().use { response ->
            currentCoroutineContext().ensureActive()
            val source = response.body?.source() ?: throw IOException("Empty response")
            source.request(2_000_001)
            require(source.buffer.size <= 2_000_000) { "Response too large" }
            val text = source.readUtf8()
            if (!response.isSuccessful) {
                val code = runCatching { MusiaJson.parseToJsonElement(text).jsonObject["detail"]?.jsonPrimitive?.content }.getOrNull()
                throw CreatorApiError(response.code, code?.takeIf { Regex("[a-z_0-9]{1,100}").matches(it) } ?: "service_unavailable")
            }
            text
        }
    }
    suspend inline fun <reified T> get(path: String, session: CreatorSession? = null): T = MusiaJson.decodeFromString(request(path, session))
    fun fields(vararg fields: Pair<String, JsonElement>) = JsonObject(fields.toMap()).toString()
}
