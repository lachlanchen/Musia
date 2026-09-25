package art.lazying.musia

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

private val Colors = lightColorScheme(
    primary = Color(0xFF007E80), onPrimary = Color.White,
    primaryContainer = Color(0xFFD7F4F0), onPrimaryContainer = Color(0xFF005355),
    secondary = Color(0xFFB74334), onSecondary = Color.White,
    secondaryContainer = Color(0xFFFFDCD6), onSecondaryContainer = Color(0xFF692218),
    tertiary = Color(0xFF4D6541), background = Color.White, surface = Color.White,
    surfaceVariant = Color(0xFFF0F3F2), onSurface = Color(0xFF1A2828),
    onSurfaceVariant = Color(0xFF4D5E5D), outline = Color(0xFF738582),
    error = Color(0xFFAE302B)
)
private val Type = Typography(
    headlineLarge = TextStyle(fontSize = 30.sp, lineHeight = 36.sp, fontWeight = FontWeight.Bold, letterSpacing = 0.sp),
    headlineMedium = TextStyle(fontSize = 26.sp, lineHeight = 32.sp, fontWeight = FontWeight.Bold, letterSpacing = 0.sp),
    titleLarge = TextStyle(fontSize = 22.sp, lineHeight = 28.sp, fontWeight = FontWeight.SemiBold, letterSpacing = 0.sp),
    titleMedium = TextStyle(fontSize = 18.sp, lineHeight = 25.sp, fontWeight = FontWeight.SemiBold, letterSpacing = 0.sp),
    bodyLarge = TextStyle(fontSize = 18.sp, lineHeight = 26.sp, letterSpacing = 0.sp),
    bodyMedium = TextStyle(fontSize = 16.sp, lineHeight = 23.sp, letterSpacing = 0.sp),
    bodySmall = TextStyle(fontSize = 14.sp, lineHeight = 20.sp, letterSpacing = 0.sp),
    labelLarge = TextStyle(fontSize = 16.sp, lineHeight = 21.sp, fontWeight = FontWeight.Medium, letterSpacing = 0.sp),
    labelMedium = TextStyle(fontSize = 13.sp, lineHeight = 18.sp, fontWeight = FontWeight.Medium, letterSpacing = 0.sp),
    labelSmall = TextStyle(fontSize = 12.sp, lineHeight = 16.sp, letterSpacing = 0.sp)
)
@Composable fun MusiaTheme(content: @Composable () -> Unit) { MaterialTheme(colorScheme = Colors, typography = Type, content = content) }
