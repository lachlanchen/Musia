package art.lazying.musia

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.LruCache
import androidx.compose.foundation.Image
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.size
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.MusicNote
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.Request

private val coverMemory = object : LruCache<String, Bitmap>(12 * 1024 * 1024) {
    override fun sizeOf(key: String, value: Bitmap): Int = value.byteCount
}

@Composable fun Cover(url: String?, title: String, modifier: Modifier = Modifier) {
    val bitmap by produceState<Bitmap?>(null, url) {
        value = null
        if (!url.isNullOrBlank()) {
            value = try {
                withContext(Dispatchers.IO) {
                    coverMemory.get(url) ?: MusiaApi.client.newCall(Request.Builder().url(MusiaApi.httpsUrl(url)).build()).execute().use { response ->
                        if (!response.isSuccessful) return@use null
                        val source = response.body?.source() ?: return@use null
                        source.request(5L * 1024 * 1024 + 1)
                        if (source.buffer.size > 5L * 1024 * 1024) return@use null
                        val bytes = source.readByteArray()
                        val bounds = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, bounds)
                        val options = BitmapFactory.Options().apply {
                            inSampleSize = 1
                            while (bounds.outWidth / inSampleSize > 768 || bounds.outHeight / inSampleSize > 768) inSampleSize *= 2
                        }
                        BitmapFactory.decodeByteArray(bytes, 0, bytes.size, options)?.also { coverMemory.put(url, it) }
                    }
                }
            } catch (e: Exception) {
                if (e is CancellationException) throw e
                null
            }
        }
    }
    Box(modifier.background(MaterialTheme.colorScheme.surfaceVariant), contentAlignment = Alignment.Center) {
        bitmap?.let { Image(it.asImageBitmap(), "Cover for $title", Modifier.matchParentSize(), contentScale = ContentScale.Fit) }
            ?: Icon(Icons.Default.MusicNote, "Cover unavailable", Modifier.size(32.dp), tint = MaterialTheme.colorScheme.primary)
    }
}
