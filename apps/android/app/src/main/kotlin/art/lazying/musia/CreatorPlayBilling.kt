package art.lazying.musia

import android.app.Activity
import android.content.Context
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import com.android.billingclient.api.*
import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.serialization.json.JsonPrimitive
import kotlin.coroutines.resume

data class MonthlyOffer(val product: BillingProduct, val details: ProductDetails,
    val offer: ProductDetails.SubscriptionOfferDetails, val price: String)

/** A purchase never grants locally. Only the backend verifies, grants durably and acknowledges. */
class CreatorPlayBilling(context: Context, private val vault: CreatorVault,
    private val scope: CoroutineScope, private val refreshAccount: () -> Unit) {
    var catalog by mutableStateOf<CreatorBilling?>(null); private set
    var offers by mutableStateOf<List<MonthlyOffer>>(emptyList()); private set
    var status by mutableStateOf("Sign in to view account subscriptions."); private set
    var working by mutableStateOf(false); private set
    var ownedQueryComplete by mutableStateOf(false); private set
    var hasOwned by mutableStateOf(false); private set
    private var bound: CreatorSession? = null
    private var epoch = 0L
    private var sales = false
    private var inFlight: PurchaseJournal? = null
    private var sheetOpen = false
    private val connectionMutex = Mutex()
    private val client = BillingClient.newBuilder(context.applicationContext)
        .setListener { result, _ ->
            // Callback payloads are not credited. Query Play again, retaining original ownership.
            sheetOpen = false
            if (result.responseCode == BillingClient.BillingResponseCode.USER_CANCELED) {
                val launch = inFlight
                if (launch != null) runCatching { vault.update { data -> data.copy(purchases = data.purchases.filterNot { it == launch }) } }
                status = "Purchase cancelled. Checking owned purchases."
            } else status = "Checking purchase status. Do not purchase again while verification is unresolved."
            inFlight = null
            restore()
        }
        .enablePendingPurchases(PendingPurchasesParams.newBuilder().enableOneTimeProducts().enablePrepaidPlans().build())
        .enableAutoServiceReconnection().build()

    val unresolved: Boolean get() = vault.state.value.purchases.any { it.owner == bound?.owner }
    val canPurchase: Boolean get() = !working && !sheetOpen && catalog?.let {
        CreatorRules.canBuy(sales, it.capabilities.google.purchase, ownedQueryComplete, hasOwned, unresolved, it.entitlement.state)
    } == true

    fun bind(session: CreatorSession, value: CreatorBilling, salesEnabled: Boolean) {
        require(runCatching { java.util.UUID.fromString(value.accountToken) }.isSuccess)
        val changed = bound != session || catalog?.accountToken != value.accountToken
        bound = session; catalog = value; sales = salesEnabled
        if (changed) {
            epoch++; ownedQueryComplete = false; hasOwned = false; offers = emptyList(); working = false
            refreshOffers(); restore()
        }
    }
    fun unbind() {
        epoch++; bound = null; catalog = null; offers = emptyList(); sales = false; working = false
        ownedQueryComplete = false; hasOwned = false; status = "Sign in to restore your subscription."
    }
    fun unavailable() { sales = false; status = "Subscription status unavailable. Refresh your account before purchasing." }
    fun onForeground() {
        // Returning from Play may precede (or outlive) its callback. Reconcile without
        // discarding the durable marker, even when the process missed a sheet result.
        sheetOpen = false
        restore()
    }
    private fun valid(e: Long, owner: CreatorSession): Boolean = epoch == e && bound == owner && vault.state.value.session == owner
    private fun checkOwner(e: Long, owner: CreatorSession) { if (!valid(e, owner)) throw CancellationException("Account changed") }
    private suspend fun connect(): Boolean = connectionMutex.withLock {
        if (client.isReady) return@withLock true
        suspendCancellableCoroutine { continuation ->
            client.startConnection(object : BillingClientStateListener {
                override fun onBillingSetupFinished(result: BillingResult) {
                    if (continuation.isActive) continuation.resume(result.responseCode == BillingClient.BillingResponseCode.OK)
                }
                override fun onBillingServiceDisconnected() {
                    ownedQueryComplete = false
                    if (continuation.isActive) continuation.resume(false)
                }
            })
        }
    }
    private suspend fun details(products: List<BillingProduct>): List<ProductDetails> {
        if (products.isEmpty()) return emptyList()
        return suspendCancellableCoroutine { continuation ->
            val params = QueryProductDetailsParams.newBuilder().setProductList(products.filter { it.googleProductId.isNotBlank() }.map {
                QueryProductDetailsParams.Product.newBuilder().setProductId(it.googleProductId).setProductType(BillingClient.ProductType.SUBS).build()
            }).build()
            client.queryProductDetailsAsync(params) { result, response ->
                if (continuation.isActive) continuation.resume(if (result.responseCode == BillingClient.BillingResponseCode.OK) response.productDetailsList else emptyList())
            }
        }
    }
    private fun monthly(products: List<BillingProduct>, details: List<ProductDetails>): List<MonthlyOffer> = products.mapNotNull { product ->
        val detail = details.firstOrNull { it.productId == product.googleProductId } ?: return@mapNotNull null
        // No inferred introductory pricing or arbitrary offer. Use the server's monthly base plan.
        val offer = detail.subscriptionOfferDetails?.firstOrNull {
            it.basePlanId == product.googleBasePlanId && it.offerId == null &&
                it.pricingPhases.pricingPhaseList.size == 1 && it.pricingPhases.pricingPhaseList[0].billingPeriod == "P1M" &&
                it.pricingPhases.pricingPhaseList[0].recurrenceMode == ProductDetails.RecurrenceMode.INFINITE_RECURRING
        } ?: return@mapNotNull null
        MonthlyOffer(product, detail, offer, offer.pricingPhases.pricingPhaseList.single().formattedPrice)
    }
    fun refreshOffers() {
        val owner = bound ?: return; val data = catalog ?: return; val e = epoch
        scope.launch {
            try {
                if (!connect()) { if (valid(e, owner)) status = "Google Play unavailable. You can still manage subscriptions in Play."; return@launch }
                val result = details(data.products)
                checkOwner(e, owner); offers = monthly(data.products, result)
            } catch (error: Exception) { if (error is CancellationException) throw error; if (valid(e, owner)) status = "Store prices unavailable. Refresh prices to retry." }
        }
    }
    private suspend fun owned(): Pair<BillingResult, List<Purchase>> = suspendCancellableCoroutine { continuation ->
        client.queryPurchasesAsync(QueryPurchasesParams.newBuilder().setProductType(BillingClient.ProductType.SUBS)
            .includeSuspendedSubscriptions(true).build()) { result, purchases ->
            if (continuation.isActive) continuation.resume(result to purchases)
        }
    }
    private suspend fun reconcile(owner: CreatorSession, data: CreatorBilling, e: Long): Boolean {
        if (!connect()) { checkOwner(e, owner); ownedQueryComplete = false; status = "Google Play unavailable. Restore again when connected."; return false }
        val (result, purchases) = owned()
        checkOwner(e, owner)
        if (result.responseCode != BillingClient.BillingResponseCode.OK) {
            ownedQueryComplete = false; status = "Owned purchases could not be checked. New purchases are paused."; return false
        }
        ownedQueryComplete = true
        // Any owned app subscription, including pending/suspended/another account, prevents duplicate sale.
        hasOwned = purchases.isNotEmpty()
        // An empty query is not proof that an interrupted purchase was cancelled. Retain
        // unknown launch markers until a matching owned purchase or an explicit cancel result.
        var mismatch = false
        var waiting = false
        for (purchase in purchases) {
            checkOwner(e, owner)
            if (!CreatorRules.purchaseBelongs(data.accountToken, purchase.accountIdentifiers?.obfuscatedAccountId)) {
                mismatch = true; continue
            }
            val pending = purchase.purchaseState != Purchase.PurchaseState.PURCHASED
            waiting = waiting || pending || purchase.isSuspended
            val journal = PurchaseJournal(owner.owner, data.accountToken, purchase.products.firstOrNull().orEmpty(), purchase.purchaseToken, pending)
            vault.update { state -> state.copy(purchases = state.purchases.filterNot {
                it.owner == owner.owner && (it.reference == journal.reference || it.reference.isEmpty() && it.product == journal.product)
            } + journal) }
        }
        var unknown = false
        if (data.capabilities.google.restore) {
            // Also retry durable verification references from an earlier unknown server response.
            for (journal in vault.state.value.purchases.filter { it.owner == owner.owner && it.accountToken == data.accountToken && it.reference.isNotEmpty() && !it.pending }) {
                checkOwner(e, owner)
                try {
                    val response = CreatorApi.request("/api/billing/verify", owner, "POST", CreatorApi.fields(
                        "provider" to JsonPrimitive("google"), "reference" to JsonPrimitive(journal.reference)))
                    checkOwner(e, owner)
                    if (MusiaJson.decodeFromString<BillingVerification>(response).verified) {
                        vault.update { state -> state.copy(purchases = state.purchases.filterNot { it.owner == owner.owner && it.reference == journal.reference }) }
                    } else unknown = true
                } catch (error: Exception) { if (error is CancellationException) throw error; unknown = true }
            }
            try { CreatorApi.request("/api/billing/restore", owner, "POST"); checkOwner(e, owner) }
            catch (error: Exception) { if (error is CancellationException) throw error; unknown = true }
        } else if (hasOwned || unresolved) unknown = true
        checkOwner(e, owner)
        status = when {
            mismatch -> "This Play purchase belongs to another Musia account, or its binding is unknown. Sign in to the original account; do not repurchase."
            waiting -> "A purchase is pending or suspended. No new allowance is granted here. Check Google Play and restore after payment completes."
            unknown || unresolved -> "Verification is unresolved. Your purchase is retained for restore. Do not buy again."
            hasOwned -> "Owned purchases checked. Access is shown from your verified server entitlement."
            else -> "No owned Play subscriptions found. Account entitlement is supplied by the server."
        }
        return !mismatch && !waiting && !unknown && !unresolved
    }
    fun restore() {
        val owner = bound ?: return; val data = catalog ?: return
        if (working || sheetOpen) return
        val e = epoch; working = true
        scope.launch {
            try { reconcile(owner, data, e); checkOwner(e, owner); refreshAccount() }
            catch (error: Exception) { if (error is CancellationException) throw error; if (valid(e, owner)) { ownedQueryComplete = false; status = "Restore interrupted. Retry restore; do not purchase again." } }
            finally { if (valid(e, owner)) working = false }
        }
    }
    fun purchase(activity: Activity, productId: String) {
        val owner = bound ?: return; val data = catalog ?: return
        if (!canPurchase) return
        val e = epoch; working = true
        scope.launch {
            try {
                if (!reconcile(owner, data, e)) return@launch
                checkOwner(e, owner)
                // Refresh both server permission and store offers immediately before the system sheet.
                val fresh = CreatorApi.get<CreatorBilling>("/api/billing", owner)
                val caps = CreatorApi.get<CreatorCapabilities>("/api/capabilities")
                checkOwner(e, owner)
                require(fresh.accountToken == data.accountToken)
                catalog = fresh; sales = caps.salesEnabled
                if (!CreatorRules.canBuy(sales, fresh.capabilities.google.purchase, ownedQueryComplete, hasOwned, unresolved, fresh.entitlement.state)) return@launch
                val available = monthly(fresh.products, details(fresh.products))
                checkOwner(e, owner); offers = available
                val offer = available.firstOrNull { it.product.googleProductId == productId } ?: run { status = "Monthly offer unavailable. Refresh prices."; return@launch }
                val journal = PurchaseJournal(owner.owner, fresh.accountToken, productId)
                vault.update { it.copy(purchases = it.purchases + journal) }
                inFlight = journal; sheetOpen = true
                val params = BillingFlowParams.newBuilder().setObfuscatedAccountId(fresh.accountToken)
                    .setProductDetailsParamsList(listOf(BillingFlowParams.ProductDetailsParams.newBuilder()
                        .setProductDetails(offer.details).setOfferToken(offer.offer.offerToken).build())).build()
                val result = client.launchBillingFlow(activity, params)
                if (result.responseCode != BillingClient.BillingResponseCode.OK) {
                    sheetOpen = false; status = "Purchase flow did not complete. Restore to reconcile before trying again."
                } else status = "Complete or cancel the purchase in Google Play."
            } catch (error: Exception) { if (error is CancellationException) throw error; if (valid(e, owner)) status = "Purchase result unknown. Restore before trying again." }
            finally { if (valid(e, owner)) working = false }
        }
    }
    fun close() { epoch++; client.endConnection() }
}
