package art.lazying.musia

import android.os.Bundle
import android.content.Intent
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import androidx.activity.viewModels

class MainActivity : ComponentActivity() {
    private val creator: CreatorViewModel by viewModels()
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        intent?.dataString?.let(creator::completeLogin)
        setContent { MusiaTheme { MusiaApp(creator = creator) } }
    }
    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        intent.dataString?.let(creator::completeLogin)
    }
    override fun onResume() {
        super.onResume()
        creator.refreshAccount()
        creator.billing.onForeground()
    }
}
