@file:OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)

package art.lazying.musia

import android.app.Activity
import android.content.Context
import android.content.ContextWrapper
import android.content.Intent
import androidx.activity.compose.BackHandler
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalUriHandler
import androidx.compose.ui.semantics.contentDescription
import androidx.compose.ui.semantics.semantics
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import androidx.lifecycle.compose.collectAsStateWithLifecycle

private fun Context.activity(): Activity? = when (this) {
    is Activity -> this
    is ContextWrapper -> baseContext.activity()
    else -> null
}

@Composable private fun CreatorNotice(vm: CreatorViewModel) {
    if (vm.busy) LinearProgressIndicator(Modifier.fillMaxWidth())
    vm.message?.let { Text(it, style = MaterialTheme.typography.bodyLarge) }
    vm.vault.warning?.let { Text(it, color = MaterialTheme.colorScheme.error) }
}

@Composable private fun AccountSummary(vm: CreatorViewModel, openAccount: () -> Unit) {
    ElevatedCard(Modifier.fillMaxWidth()) {
        Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            Text(vm.account?.name ?: "Listen freely. Create with an account.", style = MaterialTheme.typography.titleLarge)
            vm.account?.usage?.let { Text("${it.tier.replaceFirstChar(Char::uppercase)} · ${it.remaining} of ${it.limit} renders remaining · ${it.period}") }
            Text("Public songs and practice never require sign-in.")
            OutlinedButton(onClick = openAccount, modifier = Modifier.heightIn(min = 48.dp)) {
                Icon(Icons.Default.AccountCircle, null); Spacer(Modifier.width(8.dp)); Text("Account & subscriptions")
            }
        }
    }
}

@Composable fun CreatorScreen(vm: CreatorViewModel, openAccount: () -> Unit, modifier: Modifier = Modifier) {
    var studio by rememberSaveable(vm.accountEpoch) { mutableStateOf(false) }
    var visibility by rememberSaveable(vm.accountEpoch) { mutableStateOf("private") }
    var confirm by remember(vm.accountEpoch) { mutableStateOf(false) }
    var rights by remember(vm.accountEpoch) { mutableStateOf(false) }
    LaunchedEffect(vm.accountEpoch) { vm.refreshJobs() }
    LazyColumn(modifier, contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Text("Create", style = MaterialTheme.typography.titleLarge)
                OutlinedButton(onClick = openAccount) { Icon(Icons.Default.AccountCircle, null); Spacer(Modifier.width(8.dp)); Text("Account") }
            }
            TabRow(selectedTabIndex = if (studio) 1 else 0) {
                Tab(selected = !studio, onClick = { studio = false }, text = { Text("Agent") }, icon = { Icon(Icons.Default.ChatBubbleOutline, null) })
                Tab(selected = studio, onClick = { studio = true }, text = { Text("Studio") }, icon = { Icon(Icons.Default.Tune, null) })
            }
        }
        item { CreatorNotice(vm) }
        if (!studio) {
            if (vm.agentMessages.isEmpty()) item { Text("What would you like to make?", style = MaterialTheme.typography.titleLarge) }
            items(vm.agentMessages) { entry ->
                Column(verticalArrangement = Arrangement.spacedBy(6.dp)) {
                    Text(if (entry.role == "user") "You" else "Musia", style = MaterialTheme.typography.labelLarge,
                        color = MaterialTheme.colorScheme.primary)
                    Text(entry.content)
                }
            }
            item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(vm.agentInput, vm::editAgentInput, Modifier.fillMaxWidth(), label = { Text("Message Musia") }, minLines = 3)
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.End) {
                        FilledIconButton(onClick = vm::askAgent,
                            enabled = vm.canCreate && vm.capabilities?.agent == true && vm.agentInput.isNotBlank() && vm.brief.valid(true),
                            modifier = Modifier.semantics { contentDescription = "Send message" }) { Icon(Icons.Default.ArrowUpward, null) }
                    }
                    if (vm.account == null) OutlinedButton(onClick = openAccount) { Text("Sign in to chat") }
                    if (!vm.brief.valid(true)) Text("Check the duration, tempo and key in Studio before sending.")
                }
            }
        }
        if (studio) item {
            val brief = vm.brief
            val locked = vm.busy && !vm.agentBusy
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                BriefField("Title", brief.title, 120, locked) { vm.edit(vm.brief.copy(title = it)) }
                BriefField("Idea", brief.idea, 4000, locked, 2) { vm.edit(vm.brief.copy(idea = it)) }
                BriefField("Lyrics", brief.lyrics, 6000, locked, 5) { vm.edit(vm.brief.copy(lyrics = it)) }
                BriefField("Arrangement and voice direction", brief.caption, 1600, locked, 3) { vm.edit(vm.brief.copy(caption = it)) }
                Text("Vocal language", style = MaterialTheme.typography.titleMedium)
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf("en" to "English", "zh" to "中文", "ja" to "日本語", "mixed" to "Mixed").forEach { (code, label) ->
                        FilterChip(selected = brief.language == code, onClick = { vm.edit(vm.brief.copy(language = code)) }, label = { Text(label) }, enabled = !locked)
                    }
                }
                NumberField("Duration in seconds (30–180)", brief.duration, brief.duration in 30..180, !locked) { vm.edit(vm.brief.copy(duration = it)) }
                NumberField("Tempo in BPM (40–200)", brief.bpm, brief.bpm in 40..200, !locked) { vm.edit(vm.brief.copy(bpm = it)) }
                BriefField("Key, for example C major or A minor", brief.key, 12, locked) { vm.edit(vm.brief.copy(key = it)) }
            }
        }
        item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                if (vm.capabilities == null) Text("Creator availability has not been confirmed. Refresh to connect.")
                if (vm.capabilities?.agent == false) Text("The song assistant is not connected.")
                if (vm.capabilities?.generation == false) Text("Song rendering is not available yet.")
                if (vm.account != null && !CreatorRules.canCreate(vm.account, vm.capabilities)) Text("Open Account to accept the current terms or redeem a creator invitation.")
                OutlinedButton(onClick = { vm.refresh(); vm.refreshJobs() }) { Icon(Icons.Default.Refresh, null); Spacer(Modifier.width(8.dp)); Text("Refresh availability & jobs") }
            }
        }
        item {
            val brief = vm.brief
            Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                if (!studio && brief.title.isNotBlank()) Text(brief.title, style = MaterialTheme.typography.titleMedium)
                vm.account?.usage?.let { Text("${it.remaining} of ${it.limit} renders remaining", style = MaterialTheme.typography.bodySmall) }
                Text("Visibility", style = MaterialTheme.typography.titleMedium)
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilterChip(visibility == "private", { visibility = "private" }, label = { Text("Private") }, leadingIcon = { Icon(Icons.Default.Lock, null) })
                    FilterChip(visibility == "public", { visibility = "public" }, label = { Text("Public after review") }, leadingIcon = { Icon(Icons.Default.Public, null) })
                }
                if (!brief.valid()) Text("Complete the title, lyrics, arrangement, valid key, duration and tempo before rendering.")
                Button(onClick = { rights = false; confirm = true }, modifier = Modifier.fillMaxWidth().heightIn(min = 52.dp),
                    enabled = vm.canCreate && vm.capabilities?.generation == true && (vm.account?.usage?.remaining ?: 0) > 0 && brief.valid() && vm.pending == null) {
                    Icon(Icons.Default.MusicNote, null); Spacer(Modifier.width(8.dp)); Text("Generate song")
                }
            }
        }
        vm.pending?.let { pending -> item {
            ElevatedCard {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text("Render result not yet confirmed", style = MaterialTheme.typography.titleLarge)
                    Text("The original request is saved for this account. Retrying checks the same render, even if you have edited the draft since then. A new render is paused until this is resolved.")
                    val title = runCatching { MusiaJson.decodeFromString<RenderRequest>(pending.body).brief.title }.getOrDefault("Saved song")
                    Text(title)
                    Button(onClick = vm::retryRender, enabled = !vm.busy) { Text("Retry original request") }
                }
            }
        } }
        item { Text("Your render jobs", style = MaterialTheme.typography.titleLarge) }
        if (vm.jobs.isEmpty()) item { Text("No jobs loaded. Refresh to check your account.") }
        items(vm.jobs, key = { it.id }) { job ->
            OutlinedCard(Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(job.brief.title.ifEmpty { "Song" }, style = MaterialTheme.typography.titleMedium)
                    Text("${job.state} · ${job.visibility} · allowance ${job.credit}")
                    job.error?.let { Text(it.replace('_', ' ')) }
                    if (job.state == "queued") OutlinedButton(onClick = { vm.cancel(job) }, enabled = !vm.busy) { Text("Cancel queued render") }
                    if (job.state == "ready") Text("Open Community → My songs to listen.")
                }
            }
        }
    }
    if (confirm) AlertDialog(onDismissRequest = { confirm = false }, title = { Text("Render this song?") }, text = {
        Column(Modifier.verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text("${vm.brief.title} · ${vm.brief.duration} seconds · $visibility")
            Text("This sends your brief to the creator service and reserves one render from your allowance. Public songs enter moderation before sharing.")
            Row(verticalAlignment = Alignment.CenterVertically) {
                Checkbox(rights, { rights = it }, modifier = Modifier.semantics { contentDescription = "Confirm rights and creator terms" })
                Text("I have the rights to these lyrics and instructions, including any voice permissions. I accept the creator terms.", Modifier.weight(1f))
            }
        }
    }, confirmButton = { TextButton(onClick = { confirm = false; vm.render(visibility) }, enabled = rights && vm.canCreate && vm.brief.valid()) { Text("Confirm render") } },
        dismissButton = { TextButton(onClick = { confirm = false }) { Text("Keep editing") } })
}

@Composable private fun BriefField(label: String, value: String, limit: Int, busy: Boolean, lines: Int = 1, change: (String) -> Unit) {
    OutlinedTextField(value, { if (it.length <= limit) change(it) }, Modifier.fillMaxWidth(), enabled = !busy,
        label = { Text(label) }, minLines = lines, singleLine = lines == 1)
}
@Composable private fun NumberField(label: String, value: Int, valid: Boolean, enabled: Boolean, change: (Int) -> Unit) {
    OutlinedTextField(if (value == 0) "" else value.toString(), { text -> if (text.length <= 3 && text.all(Char::isDigit)) change(text.toIntOrNull() ?: 0) },
        Modifier.fillMaxWidth(), label = { Text(label) }, isError = !valid, enabled = enabled, singleLine = true,
        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number))
}

@Composable fun CreatorAccountScreen(vm: CreatorViewModel, modifier: Modifier = Modifier) {
    val context = LocalContext.current
    val links = LocalUriHandler.current
    val account = vm.account
    val secrets by vm.vault.state.collectAsStateWithLifecycle()
    var invitation by rememberSaveable(vm.accountEpoch) { mutableStateOf("") }
    var delete by remember(vm.accountEpoch) { mutableStateOf(false) }
    var accept by remember(vm.accountEpoch, vm.capabilities?.termsVersion) { mutableStateOf(false) }
    LaunchedEffect(vm.accountEpoch) { vm.refreshBlocks() }
    LazyColumn(modifier, contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item {
            Text("Account & subscriptions", style = MaterialTheme.typography.headlineLarge)
            Text("An account is optional. Your practice history stays on this device.")
        }
        item { CreatorNotice(vm) }
        item {
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedButton(onClick = vm::refresh) { Icon(Icons.Default.Refresh, null); Spacer(Modifier.width(8.dp)); Text("Refresh account") }
                TextButton(onClick = { links.openUri("${MusiaApi.ORIGIN}/creator/terms") }) { Text("Creator terms") }
                TextButton(onClick = { links.openUri("${MusiaApi.ORIGIN}/privacy") }) { Text("Privacy") }
            }
        }
        if (account == null) item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("Sign in securely in your browser to create, save and comment.")
                if (vm.capabilities?.login != true) Text("Sign-in is not currently available from the service.")
                Button(onClick = { vm.startLogin(context) }, enabled = !vm.busy && vm.capabilities?.login == true && vm.vault.warning == null && secrets.session == null) {
                    Icon(Icons.Default.AccountCircle, null); Spacer(Modifier.width(8.dp)); Text("Sign in with browser")
                }
                if (secrets.session != null) OutlinedButton(onClick = vm::logout) { Text("Clear saved sign-in") }
            }
        }
        if (account != null) {
            item {
                Text(account.name, style = MaterialTheme.typography.titleLarge)
                Text("${account.usage.tier} · ${account.usage.remaining} of ${account.usage.limit} renders remaining · ${account.usage.period}")
                Text("Allowance source: ${account.usage.source.ifEmpty { "server" }}")
            }
            if (!account.termsAccepted) item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text("Review the creator terms (${vm.capabilities?.termsVersion.orEmpty()}) before creating or posting.")
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Checkbox(accept, { accept = it }, modifier = Modifier.semantics { contentDescription = "Accept current creator terms" }); Text("I accept the current creator terms.", Modifier.weight(1f))
                    }
                    Button(onClick = vm::acceptTerms, enabled = accept && !vm.busy && vm.capabilities?.termsVersion?.isNotBlank() == true) { Text("Accept terms") }
                }
            }
            if (vm.capabilities?.invitationRequired == true && !account.invited) item {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedTextField(invitation, { if (it.length <= 128) invitation = it }, Modifier.fillMaxWidth(), label = { Text("Creator invitation code") }, singleLine = true)
                    Button(onClick = { vm.redeem(invitation); invitation = "" }, enabled = invitation.trim().length in 20..128 && !vm.busy) { Text("Redeem invitation") }
                }
            }
        }
        item { HorizontalDivider(); Text("Monthly plans", style = MaterialTheme.typography.titleLarge) }
        items(vm.capabilities?.plans.orEmpty(), key = { it.id }) { plan ->
            Text("${plan.name} · ${plan.renders} renders per allowance period", style = MaterialTheme.typography.titleMedium)
        }
        if (account != null) {
            val billing = vm.billing
            item {
                billing.catalog?.entitlement?.let { entitlement ->
                    Text("${entitlement.tier} · ${entitlement.state}", style = MaterialTheme.typography.titleMedium)
                    entitlement.expiresAt?.let { Text("Entitlement expiry: ${java.text.DateFormat.getDateTimeInstance().format(java.util.Date(it * 1000))}") }
                    entitlement.environment?.let { Text("Store environment: $it") }
                }
                Text(billing.status)
                if (billing.working) LinearProgressIndicator(Modifier.fillMaxWidth())
                if (vm.capabilities?.salesEnabled != true || billing.catalog?.capabilities?.google?.purchase != true) {
                    Text("New purchases are unavailable. Existing subscriptions can still be restored or managed.")
                    billing.catalog?.capabilities?.google?.reason?.takeIf { it.isNotEmpty() }?.let { Text(it.replace('_', ' ')) }
                }
            }
            items(billing.catalog?.products.orEmpty(), key = { it.googleProductId }) { product ->
                val offer = billing.offers.firstOrNull { it.product.googleProductId == product.googleProductId }
                OutlinedCard(Modifier.fillMaxWidth()) {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                        Text(product.tier.replaceFirstChar(Char::uppercase), style = MaterialTheme.typography.titleLarge)
                        Text(offer?.let { "${it.price} / month" } ?: "Localized Play price unavailable")
                        Text("Auto-renews monthly until cancelled in Google Play. The store confirms the price before payment.")
                        Button(onClick = { context.activity()?.let { billing.purchase(it, product.googleProductId) } },
                            enabled = offer != null && billing.canPurchase && secrets.purchases.none { it.owner == account.id }) { Text("Subscribe monthly") }
                    }
                }
            }
            item {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    OutlinedButton(onClick = billing::restore, enabled = !billing.working) { Icon(Icons.Default.Restore, null); Spacer(Modifier.width(8.dp)); Text("Restore purchases") }
                    OutlinedButton(onClick = billing::refreshOffers) { Text("Refresh Play prices") }
                }
                Text("Restore checks owned Play purchases and asks the server to verify them. It never buys a subscription.")
            }
            item {
                HorizontalDivider(); Text("Blocked accounts", style = MaterialTheme.typography.titleLarge)
                OutlinedButton(onClick = vm::refreshBlocks) { Text("Refresh blocked accounts") }
            }
            items(vm.blocks, key = { it.id }) { blocked ->
                ListItem(headlineContent = { Text(blocked.name) }, trailingContent = {
                    TextButton(onClick = { vm.block(blocked.id, false) }, enabled = !vm.busy) { Text("Unblock") }
                })
            }
            item {
                FlowRow(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                    OutlinedButton(onClick = vm::logout) { Text("Sign out") }
                    TextButton(onClick = { delete = true }, enabled = !vm.busy) { Text("Delete creator account", color = MaterialTheme.colorScheme.error) }
                }
            }
        }
        item {
            OutlinedButton(onClick = { links.openUri("https://play.google.com/store/account/subscriptions?package=art.lazying.musia") }) {
                Icon(Icons.Default.ManageAccounts, null); Spacer(Modifier.width(8.dp)); Text("Manage in Google Play")
            }
            Text("Deleting your Musia account does not cancel a store subscription. Manage or cancel it in Google Play.")
        }
    }
    if (delete) AlertDialog(onDismissRequest = { delete = false }, title = { Text("Delete your creator account?") },
        text = { Text("Your creator profile, drafts on this device, songs and community activity will be removed or hidden by the service. Media cleanup may take time. This cannot be undone. Store subscriptions are cancelled separately in Google Play. Local practice history is kept.", Modifier.verticalScroll(rememberScrollState())) },
        confirmButton = { TextButton(onClick = { delete = false; vm.deleteAccount() }) { Text("Delete account") } },
        dismissButton = { TextButton(onClick = { delete = false }) { Text("Keep account") } })
}

@Composable fun CreatorCommunityScreen(vm: CreatorViewModel, openAccount: () -> Unit,
    play: (CreatorSong, CreatorSession?) -> Unit, modifier: Modifier = Modifier) {
    val song = vm.selected
    BackHandler(song != null) { vm.select(null) }
    if (song != null) { CreatorSongScreen(vm, song, play, modifier); return }
    LazyColumn(modifier, contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item { Text("Community", style = MaterialTheme.typography.headlineLarge); Text("Songs shared by Musia creators.") }
        item { CreatorNotice(vm) }
        item {
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                listOf("public" to "Discover", "mine" to "My songs", "saved" to "Saved").forEach { (mode, name) ->
                    FilterChip(vm.mode == mode, { vm.refreshSongs(mode) }, label = { Text(name) }, enabled = mode == "public" || vm.account != null)
                }
                OutlinedButton(onClick = { vm.refreshSongs() }) { Icon(Icons.Default.Refresh, null); Spacer(Modifier.width(8.dp)); Text("Refresh songs") }
            }
        }
        if (vm.account == null) item { OutlinedButton(onClick = openAccount) { Text("Optional sign-in to save or create") } }
        if (vm.songs.loading) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
        vm.songs.error?.let { item { Text(it, color = MaterialTheme.colorScheme.error) } }
        if (vm.songs.value?.isEmpty() == true) item { Text("No songs to show yet.") }
        items(vm.songs.value.orEmpty(), key = { it.id }) { entry ->
            ElevatedCard(onClick = { vm.select(entry) }, modifier = Modifier.fillMaxWidth()) {
                Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(entry.title, style = MaterialTheme.typography.titleLarge)
                    Text("${entry.author.name} · ${entry.language} · ${entry.duration.toInt()} seconds")
                    Text("${entry.visibility} · ${entry.moderation} · ${entry.likes} hearts")
                    Button(onClick = { vm.openAudio(entry, play) }, enabled = !vm.busy, modifier = Modifier.heightIn(min = 48.dp)) {
                        Icon(Icons.Default.PlayArrow, null); Spacer(Modifier.width(8.dp)); Text("Listen")
                    }
                }
            }
        }
    }
}

@Composable private fun CreatorSongScreen(vm: CreatorViewModel, song: CreatorSong,
    play: (CreatorSong, CreatorSession?) -> Unit, modifier: Modifier) {
    val context = LocalContext.current
    var comment by rememberSaveable(song.id, vm.accountEpoch) { mutableStateOf("") }
    var report by remember(song.id, vm.accountEpoch) { mutableStateOf(false) }
    var reason by remember(song.id, vm.accountEpoch) { mutableStateOf("") }
    var block by remember(song.id, vm.accountEpoch) { mutableStateOf(false) }
    var publish by remember(song.id, vm.accountEpoch) { mutableStateOf(false) }
    LazyColumn(modifier, contentPadding = PaddingValues(20.dp), verticalArrangement = Arrangement.spacedBy(16.dp)) {
        item { OutlinedButton(onClick = { vm.select(null) }) { Text("Back to community") } }
        item {
            Text(song.title, style = MaterialTheme.typography.headlineLarge)
            Text("${song.author.name} · ${song.visibility} · ${song.moderation}")
            CreatorNotice(vm)
        }
        item {
            FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(onClick = { vm.openAudio(song, play) }, enabled = !vm.busy) { Icon(Icons.Default.PlayArrow, null); Spacer(Modifier.width(8.dp)); Text("Listen") }
                OutlinedButton(onClick = { vm.react(song, "like") }, enabled = vm.account != null && !vm.busy) {
                    Icon(if (song.liked) Icons.Default.Favorite else Icons.Default.FavoriteBorder, null)
                    Spacer(Modifier.width(8.dp)); Text("${if (song.liked) "Unheart" else "Heart"} (${song.likes})")
                }
                OutlinedButton(onClick = { vm.react(song, "save") }, enabled = vm.account != null && !vm.busy) {
                    Icon(if (song.saved) Icons.Default.Bookmark else Icons.Default.BookmarkBorder, null)
                    Spacer(Modifier.width(8.dp)); Text(if (song.saved) "Unsave" else "Save")
                }
                if (song.visibility == "public" && song.moderation == "approved" && song.sharePath != null) {
                    OutlinedButton(onClick = {
                        runCatching { CreatorApi.originUrl(song.sharePath) }.getOrNull()?.let { url ->
                            context.startActivity(Intent.createChooser(Intent(Intent.ACTION_SEND).setType("text/plain").putExtra(Intent.EXTRA_TEXT, url), "Share song"))
                        }
                    }) { Icon(Icons.Default.Share, null); Spacer(Modifier.width(8.dp)); Text("Share") }
                }
            }
        }
        if (song.mine) item {
            OutlinedButton(onClick = { if (song.visibility == "private") publish = true else vm.visibility(song, "private") }, enabled = !vm.busy) {
                Text(if (song.visibility == "private") "Submit for public sharing" else "Make private")
            }
        }
        if (song.lyrics.isNotBlank()) item { Text("Song lyrics", style = MaterialTheme.typography.titleLarge); Text(song.lyrics); Text("Timed lyrics appear in the player only when supplied for the finished audio.") }
        item { HorizontalDivider(); Text("Comments", style = MaterialTheme.typography.titleLarge); OutlinedButton(onClick = vm::refreshComments) { Text("Refresh comments") } }
        if (vm.comments.loading) item { LinearProgressIndicator(Modifier.fillMaxWidth()) }
        vm.comments.error?.let { item { Text(it) } }
        items(vm.comments.value.orEmpty(), key = { it.id }) { entry ->
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("${entry.author} · ${entry.state}", style = MaterialTheme.typography.titleMedium)
                Text(entry.text)
                if (entry.mine) TextButton(onClick = { vm.deleteComment(entry.id) }, enabled = !vm.busy) { Text("Delete comment") }
            }
        }
        if (vm.account != null) item {
            Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(comment, { if (it.length <= 1000) comment = it }, Modifier.fillMaxWidth(), label = { Text("Write a comment") }, minLines = 2)
                Text("Comments are moderated. If sending is interrupted, refresh before posting again.")
                Button(onClick = { vm.comment(song, comment); comment = "" }, enabled = comment.isNotBlank() && !vm.busy && vm.account?.termsAccepted == true) { Text("Post comment") }
                FlowRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TextButton(onClick = { report = true }) { Icon(Icons.Default.Flag, null); Spacer(Modifier.width(8.dp)); Text("Report song") }
                    if (!song.mine) TextButton(onClick = { block = true }) { Icon(Icons.Default.Block, null); Spacer(Modifier.width(8.dp)); Text("Block creator") }
                }
            }
        } else item { Text("Sign in from Account to heart, save or comment.") }
    }
    if (report) AlertDialog(onDismissRequest = { report = false }, title = { Text("Report song") },
        text = { OutlinedTextField(reason, { if (it.length <= 1000) reason = it }, label = { Text("Reason for reporting") }, minLines = 3) },
        confirmButton = { TextButton(onClick = { vm.report(song, reason); report = false; reason = "" }, enabled = reason.trim().length >= 3 && !vm.busy) { Text("Send report") } },
        dismissButton = { TextButton(onClick = { report = false }) { Text("Cancel") } })
    if (block) AlertDialog(onDismissRequest = { block = false }, title = { Text("Block ${song.author.name}?") },
        text = { Text("Their songs and comments will be hidden for your account. You can unblock them from Account.") },
        confirmButton = { TextButton(onClick = { block = false; vm.block(song.author.id, true) }) { Text("Block") } },
        dismissButton = { TextButton(onClick = { block = false }) { Text("Cancel") } })
    if (publish) AlertDialog(onDismissRequest = { publish = false }, title = { Text("Share publicly after review?") },
        text = { Text("I confirm I have the rights to share this song and accept the creator terms. The song will enter moderation before it is publicly listed.") },
        confirmButton = { TextButton(onClick = { publish = false; vm.visibility(song, "public") }) { Text("Confirm public sharing") } },
        dismissButton = { TextButton(onClick = { publish = false }) { Text("Keep private") } })
}
