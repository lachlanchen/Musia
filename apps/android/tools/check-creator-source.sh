#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
cache="${GRADLE_USER_HOME:-$HOME/.gradle}/caches/modules-2/files-2.1"
out="app/build/creator-source-check"
mkdir -p "$out"
jar() { find "$cache/$1/$2/$3" -name '*.jar' -type f -print -quit; }
compiler="$(jar org.jetbrains.kotlin kotlin-compiler-embeddable 2.1.0)"
stdlib="$(jar org.jetbrains.kotlin kotlin-stdlib 2.1.0)"
script="$(jar org.jetbrains.kotlin kotlin-script-runtime 2.1.0)"
reflect="$(find "$cache/org.jetbrains.kotlin/kotlin-reflect" -name '*.jar' -type f -print -quit)"
trove="$(jar org.jetbrains.intellij.deps trove4j 1.0.20200330)"
annotations="$(jar org.jetbrains annotations 13.0)"
coroutines="$(jar org.jetbrains.kotlinx kotlinx-coroutines-core-jvm 1.9.0)"
compiler_cp="$compiler:$stdlib:$script:$reflect:$trove:$annotations:$coroutines"
javac -cp "$compiler_cp" -d "$out" tools/KotlinSyntaxCheck.java
java -Xmx256m -cp "$out:$compiler_cp" KotlinSyntaxCheck app/src
serialization="$(jar org.jetbrains.kotlinx kotlinx-serialization-core-jvm 1.7.3):$(jar org.jetbrains.kotlinx kotlinx-serialization-json-jvm 1.7.3)"
junit="$(jar junit junit 4.13.2):$(jar org.hamcrest hamcrest-core 1.3)"
plugin="$(jar org.jetbrains.kotlin kotlin-serialization-compiler-plugin-embeddable 2.1.0)"
source="app/src/main/kotlin/art/lazying/musia"
java -Xmx384m -cp "$compiler_cp" org.jetbrains.kotlin.cli.jvm.K2JVMCompiler \
  -no-stdlib -no-reflect -jvm-target 17 -classpath "$stdlib:$serialization:$junit:$annotations" \
  -Xplugin="$plugin" -d "$out/core-tests.jar" \
  "$source/Models.kt" "$source/Timeline.kt" "$source/LyricParts.kt" \
  "$source/CreatorModels.kt" "$source/CreatorRules.kt" \
  app/src/test/kotlin/art/lazying/musia/CreatorContractTest.kt
java -Xmx128m -cp "$out/core-tests.jar:$stdlib:$serialization:$junit" org.junit.runner.JUnitCore art.lazying.musia.CreatorContractTest
if [[ "${1:-}" == "--controllers" ]]; then
  # Isolated source type check using existing cached Android APIs; still no Gradle/APK.
  aar() {
    local archive
    archive="$(find "$cache/$1/$2/$3" -name '*.aar' -type f -print -quit)"
    unzip -p "$archive" classes.jar > "$out/$2-api.jar"
    echo "$out/$2-api.jar"
  }
  controller_cp="$stdlib:$serialization:$annotations:$coroutines"
  controller_cp+=":$(jar com.squareup.okhttp3 okhttp 4.12.0):$(jar com.squareup.okio okio-jvm 3.6.0)"
  controller_cp+=":$(aar androidx.compose.runtime runtime-android 1.9.1)"
  controller_cp+=":$(aar androidx.lifecycle lifecycle-viewmodel-android 2.9.0)"
  controller_cp+=":$(aar androidx.browser browser 1.9.0):$(aar com.android.billingclient billing 9.1.0)"
  controller_cp+=":${ANDROID_HOME:-$HOME/Android/Sdk}/platforms/android-36/android.jar"
  java -Xmx384m -cp "$compiler_cp" org.jetbrains.kotlin.cli.jvm.K2JVMCompiler \
    -no-stdlib -no-reflect -jvm-target 17 -classpath "$controller_cp" -Xplugin="$plugin" \
    -d "$out/controllers.jar" "$source/Models.kt" "$source/Timeline.kt" "$source/LyricParts.kt" \
    "$source/Api.kt" "$source/CreatorModels.kt" "$source/CreatorRules.kt" "$source/CreatorApi.kt" \
    "$source/CreatorVault.kt" "$source/CreatorPlayBilling.kt" "$source/CreatorViewModel.kt"
fi
git diff --check -- .
