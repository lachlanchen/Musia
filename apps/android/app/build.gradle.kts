import java.nio.file.Files
import java.nio.file.attribute.PosixFilePermission
import java.util.Properties

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
    id("org.jetbrains.kotlin.plugin.serialization")
}

val signingPath = System.getenv("MUSIA_SIGNING_PROPERTIES")
val privateSigning = signingPath?.takeIf { it.isNotBlank() }?.let { path ->
    val source = file(path).canonicalFile
    require(File(path).isAbsolute && source.isFile) { "MUSIA_SIGNING_PROPERTIES must be an existing absolute private path" }
    require(!source.toPath().startsWith(rootDir.canonicalFile.toPath())) { "Signing properties must be outside apps/android" }
    fun checkPrivate(f: File) {
        val permissions = Files.getPosixFilePermissions(f.toPath())
        require(permissions.none { it in setOf(
            PosixFilePermission.GROUP_READ, PosixFilePermission.GROUP_WRITE,
            PosixFilePermission.GROUP_EXECUTE, PosixFilePermission.OTHERS_READ,
            PosixFilePermission.OTHERS_WRITE, PosixFilePermission.OTHERS_EXECUTE
        ) }) { "Signing files must not be accessible by group or others (use chmod 600)" }
    }
    checkPrivate(source)
    Properties().apply {
        source.inputStream().use { load(it) }
        listOf("storeFile", "storePassword", "keyAlias", "keyPassword").forEach {
            require(!getProperty(it).isNullOrBlank()) { "Missing signing property: $it" }
        }
        val key = File(getProperty("storeFile")).canonicalFile
        require(File(getProperty("storeFile")).isAbsolute && key.isFile) { "storeFile must be an existing absolute private path" }
        require(!key.toPath().startsWith(rootDir.canonicalFile.toPath())) { "Keystore must be outside apps/android" }
        checkPrivate(key)
    }
}

android {
    namespace = "art.lazying.musia"
    compileSdk = 36
    defaultConfig {
        applicationId = "art.lazying.musia"
        minSdk = 26
        targetSdk = 36
        versionCode = 3
        versionName = "0.1.2"
    }
    signingConfigs {
        if (privateSigning != null) create("privateRelease") {
            storeFile = file(privateSigning.getProperty("storeFile"))
            storePassword = privateSigning.getProperty("storePassword")
            keyAlias = privateSigning.getProperty("keyAlias")
            keyPassword = privateSigning.getProperty("keyPassword")
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = false
            if (privateSigning != null) signingConfig = signingConfigs.getByName("privateRelease")
        }
    }
    buildFeatures { compose = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }
    packaging { resources.excludes += "/META-INF/{AL2.0,LGPL2.1}" }
}

// Inspect the resolved graph, not the requested spelling: aliases, build and
// abbreviated release tasks must not bypass the signing gate.
gradle.taskGraph.whenReady {
    if (allTasks.any { it.project == project && it.name.contains("release", ignoreCase = true) }) {
        check(privateSigning != null) { "Release disabled: set MUSIA_SIGNING_PROPERTIES to protected signing properties" }
    }
}

dependencies {
    implementation(platform("androidx.compose:compose-bom:2025.09.00"))
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.compose.ui:ui")
    implementation("androidx.activity:activity-compose:1.10.1")
    implementation("androidx.lifecycle:lifecycle-runtime-compose:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-compose:2.8.7")
    implementation("androidx.media3:media3-exoplayer:1.8.0")
    implementation("androidx.media3:media3-session:1.8.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:1.7.3")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    testImplementation("junit:junit:4.13.2")
}
