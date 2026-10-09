import java.nio.file.*;
import java.util.stream.Stream;
import org.jetbrains.kotlin.cli.jvm.compiler.EnvironmentConfigFiles;
import org.jetbrains.kotlin.cli.jvm.compiler.KotlinCoreEnvironment;
import org.jetbrains.kotlin.config.CompilerConfiguration;
import org.jetbrains.kotlin.com.intellij.openapi.util.Disposer;
import org.jetbrains.kotlin.com.intellij.psi.PsiErrorElement;
import org.jetbrains.kotlin.com.intellij.psi.util.PsiTreeUtil;
import org.jetbrains.kotlin.psi.KtPsiFactory;

/** Cheap parser check only: no Gradle, Android build, emulator or network. */
public class KotlinSyntaxCheck {
    public static void main(String[] args) throws Exception {
        var disposable = Disposer.newDisposable();
        int errors = 0, count = 0;
        try {
            var env = KotlinCoreEnvironment.createForProduction(disposable, new CompilerConfiguration(), EnvironmentConfigFiles.JVM_CONFIG_FILES);
            var factory = new KtPsiFactory(env.getProject(), false);
            try (Stream<Path> files = Files.walk(Path.of(args[0]))) {
                for (Path path : files.filter(p -> p.toString().endsWith(".kt")).toList()) {
                    count++;
                    var parsed = factory.createFile(path.getFileName().toString(), Files.readString(path));
                    for (var error : PsiTreeUtil.findChildrenOfType(parsed, PsiErrorElement.class)) {
                        System.err.println(path + ":" + error.getTextOffset() + ": " + error.getErrorDescription());
                        errors++;
                    }
                }
            }
        } finally { Disposer.dispose(disposable); }
        System.out.println("Parsed " + count + " Kotlin files; syntax errors: " + errors);
        if (errors != 0) System.exit(1);
    }
}
