import Combine
import Foundation
import MusiaCore
import StoreKit
#if os(iOS)
import UIKit
#else
import AppKit
#endif

@MainActor
final class CreatorBillingStore: ObservableObject {
    static let productIDs = ["art.lazying.musia.creator.monthly", "art.lazying.musia.studio.monthly"]
    private struct PendingPurchase: Codable {
        let owner: String
        let accountToken: UUID
        let productID: String
        var reference: String?
    }
    @Published private(set) var products: [Product] = []
    @Published private(set) var billing: CreatorBilling?
    @Published private(set) var busy = false
    @Published private(set) var pending = false
    @Published private(set) var message: String?
    private weak var creator: CreatorStore?
    private var listener: Task<Void, Never>?
    private var boundIdentity: CreatorIdentity?
    private var purchaseRecords: [String: PendingPurchase] = [:]
    private var storageReady = false
    private var verifying: Set<String> = []

    func start(creator: CreatorStore) {
        self.creator = creator
        guard listener == nil else { return }
        do {
            purchaseRecords = try CreatorKeychain.read([String: PendingPurchase].self, key: "pending-purchases") ?? [:]
            storageReady = true
        } catch { message = error.localizedDescription }
        listener = Task { [weak self] in
            for await result in Transaction.updates {
                guard !Task.isCancelled else { return }
                await self?.receive(result)
            }
        }
    }
    func accountChanged() async {
        guard let creator else { return }
        let capturedIdentity = creator.identity
        boundIdentity = capturedIdentity
        billing = nil; busy = false; message = nil
        pending = creator.account.map { account in purchaseRecords.values.contains { $0.owner == account.id } } ?? false
        await loadProducts()
        guard creator.identity == capturedIdentity else { return }
        // Ordinary reconciliation is silent. It never calls AppStore.sync().
        if creator.account != nil { await restore() }
    }
    func loadProducts() async {
        do {
            products = try await Product.products(for: Self.productIDs).sorted { $0.price < $1.price }
            if products.isEmpty { message = "Subscription prices are unavailable from the App Store. Restore and Manage remain available." }
        } catch { message = "App Store prices could not load. Try again when connected." }
    }
    private func loadBilling(_ captured: CreatorStore.SessionSnapshot) async throws -> CreatorBilling {
        guard let creator else { throw CreatorError.signInRequired }
        let loaded: CreatorBilling = try await creator.api.request("/api/billing", token: captured.token)
        try creator.requireCurrent(captured)
        billing = loaded; boundIdentity = captured.identity
        pending = purchaseRecords.values.contains { $0.owner == captured.identity.owner }
        return loaded
    }
    var purchaseAllowed: Bool {
        guard let creator, let billing, (try? creator.snapshot()) != nil else { return false }
        return !busy && storageReady && CreatorPurchaseGate.allows(state: billing.entitlement.state,
            purchaseEnabled: billing.capabilities.apple.purchase, salesEnabled: creator.capabilities?.salesEnabled == true,
            hasPending: pending, identity: creator.identity, binding: boundIdentity)
    }
    var purchaseExplanation: String {
        guard let creator, creator.account != nil else { return "Sign in to check purchase availability. Restore your purchases after signing in to their original Musia account." }
        if pending { return "A previous purchase is awaiting confirmation. Restore to check it." }
        guard let billing else { return "Refresh your account to check subscription availability." }
        if !["none", "free", "inactive", "expired", "revoked"].contains(billing.entitlement.state) {
            return "Review your existing subscription with Restore or Manage below."
        }
        return "New subscriptions are currently unavailable for this account. Restore and Manage remain available."
    }
    func restore() async {
        guard !busy, let creator, let captured = try? creator.snapshot() else { return }
        busy = true; message = nil
        defer { if captured.identity == creator.identity { busy = false } }
        do {
            let loaded = try await loadBilling(captured)
            for await result in Transaction.currentEntitlements {
                try creator.requireCurrent(captured)
                try await verify(result, captured: captured, billing: loaded)
            }
            for await result in Transaction.unfinished {
                try creator.requireCurrent(captured)
                try await verify(result, captured: captured, billing: loaded)
            }
            _ = try await creator.api.send("/api/billing/restore", token: captured.token)
            try creator.requireCurrent(captured)
            _ = try await loadBilling(captured)
            message = pending
                ? "A purchase is still awaiting confirmation. Check again later; no new purchase will be started."
                : "Current purchases were checked with Musia."
            await creator.refresh()
        } catch { if captured.identity == creator.identity { message = error.localizedDescription } }
    }
    /// Only the explicit, confirmed "Find missing purchases" gesture calls this.
    func findMissingPurchases() async {
        guard !busy, let creator, let captured = try? creator.snapshot() else { return }
        busy = true; message = nil
        do {
            _ = try CreatorPresentation.anchor()
            try await AppStore.sync()
            try creator.requireCurrent(captured)
            busy = false
            await restore()
        } catch {
            if captured.identity == creator.identity { busy = false; message = error.localizedDescription }
        }
    }
    func purchase(_ product: Product) async {
        guard purchaseAllowed, let creator, let captured = try? creator.snapshot() else { return }
        busy = true; message = nil
        defer { if captured.identity == creator.identity { busy = false } }
        do {
            // Recheck server eligibility and local ownership at the purchase gesture.
            let loaded = try await loadBilling(captured)
            guard CreatorPurchaseGate.allows(state: loaded.entitlement.state,
                  purchaseEnabled: loaded.capabilities.apple.purchase, salesEnabled: creator.capabilities?.salesEnabled == true,
                  hasPending: pending, identity: creator.identity, binding: captured.identity),
                  loaded.products.contains(where: { $0.appleProductId == product.id }),
                  product.type == .autoRenewable else {
                throw CreatorError.unavailable("New purchases are unavailable. Restore or manage your existing subscription.")
            }
            for await result in Transaction.currentEntitlements {
                if case .verified(let transaction) = result, Self.productIDs.contains(transaction.productID) {
                    try await verify(result, captured: captured, billing: loaded)
                    throw CreatorError.unavailable("An Apple subscription already exists. Restore or Manage to review it.")
                }
                if case .unverified = result {
                    throw CreatorError.unavailable("Apple purchase history could not be verified. Try Restore before purchasing.")
                }
            }
            for await result in Transaction.unfinished {
                if case .verified(let transaction) = result, Self.productIDs.contains(transaction.productID) {
                    try await verify(result, captured: captured, billing: loaded)
                    throw CreatorError.unavailable("A previous purchase was found. Use Restore to review its status before purchasing.")
                }
                if case .unverified = result {
                    throw CreatorError.unavailable("An unfinished purchase could not be verified. Use Restore before purchasing.")
                }
            }
            try creator.requireCurrent(captured)
            let window = try CreatorPresentation.anchor()
#if os(iOS)
            guard let scene = window.windowScene, var controller = window.rootViewController else {
                throw CreatorError.unavailable("Reopen the account screen to purchase.")
            }
            while let presented = controller.presentedViewController { controller = presented }
#endif
            let record = PendingPurchase(owner: captured.identity.owner, accountToken: loaded.accountToken,
                                         productID: product.id, reference: nil)
            try save(record)
            let options: Set<Product.PurchaseOption> = [.appAccountToken(loaded.accountToken)]
            let result: Product.PurchaseResult
#if os(iOS)
            if #available(iOS 18.2, *) {
                result = try await product.purchase(confirmIn: controller, options: options)
            } else {
                result = try await product.purchase(confirmIn: scene, options: options)
            }
#else
            if #available(macOS 15.2, *) {
                result = try await product.purchase(confirmIn: window, options: options)
            } else { result = try await product.purchase(options: options) }
#endif
            switch result {
            case .success(let verification):
                try creator.requireCurrent(captured)
                try await verify(verification, captured: captured, billing: loaded)
                _ = try await loadBilling(captured)
                message = "Purchase verified by Musia."
                await creator.refresh()
            case .userCancelled:
                // A cancellation is the only no-transaction outcome that clears the attempt.
                if let stored = purchaseRecords[loaded.accountToken.uuidString],
                   stored.owner == captured.identity.owner, stored.productID == product.id, stored.reference == nil {
                    try remove(accountToken: loaded.accountToken)
                }
                if captured.identity == creator.identity { message = "Purchase cancelled." }
            case .pending:
                if captured.identity == creator.identity { message = "Awaiting Apple approval. Musia will check the transaction when it arrives." }
            @unknown default:
                if captured.identity == creator.identity { message = "Purchase outcome is unknown. Use Restore to reconcile before trying again." }
            }
        } catch { if captured.identity == creator.identity { message = error.localizedDescription } }
    }
    private func receive(_ result: VerificationResult<Transaction>) async {
        guard let creator, let captured = try? creator.snapshot() else { return }
        do {
            let loaded = try await loadBilling(captured)
            try await verify(result, captured: captured, billing: loaded)
            _ = try await loadBilling(captured)
            await creator.refresh()
        } catch { if captured.identity == creator.identity { message = error.localizedDescription } }
    }
    private func verify(_ result: VerificationResult<Transaction>, captured: CreatorStore.SessionSnapshot,
                        billing: CreatorBilling) async throws {
        guard let creator else { throw CreatorError.signInRequired }
        try creator.requireCurrent(captured)
        guard case .verified(let transaction) = result else {
            throw CreatorError.unavailable("Apple could not verify a purchase. It remains unfinished; use Restore to check again.")
        }
        guard Self.productIDs.contains(transaction.productID) else { return }
        guard transaction.appAccountToken == billing.accountToken else {
            throw CreatorError.unavailable("This Apple purchase belongs to a different Musia account. Sign in to its original account to restore it.")
        }
        let reference = String(transaction.id)
        guard !verifying.contains(reference) else {
            throw CreatorError.unavailable("This purchase is being verified. Check again in a moment.")
        }
        verifying.insert(reference); defer { verifying.remove(reference) }
        try save(PendingPurchase(owner: captured.identity.owner, accountToken: billing.accountToken,
                                 productID: transaction.productID, reference: reference))
        let response: CreatorVerification = try await creator.api.request("/api/billing/verify", method: "POST", token: captured.token,
            body: CreatorAPI.body(["provider": "apple", "reference": reference]))
        try creator.requireCurrent(captured)
        guard response.verified else {
            throw CreatorError.unavailable("Musia has not verified this purchase yet. Use Restore later; do not purchase again.")
        }
        // Server has fetched provider truth and durably bound this transaction to
        // the captured owner. Never finish an unverified or switched-account result.
        await transaction.finish()
        try creator.requireCurrent(captured)
        if purchaseRecords[billing.accountToken.uuidString]?.reference == reference {
            try remove(accountToken: billing.accountToken)
        }
    }
    private func save(_ record: PendingPurchase) throws {
        guard storageReady else { throw CreatorError.storage }
        var next = purchaseRecords; next[record.accountToken.uuidString] = record
        try CreatorKeychain.write(next, key: "pending-purchases")
        purchaseRecords = next
        pending = purchaseRecords.values.contains { $0.owner == creator?.account?.id }
    }
    private func remove(accountToken: UUID) throws {
        var next = purchaseRecords; next.removeValue(forKey: accountToken.uuidString)
        try CreatorKeychain.write(next, key: "pending-purchases")
        purchaseRecords = next
        pending = purchaseRecords.values.contains { $0.owner == creator?.account?.id }
    }
    static func period(_ product: Product) -> String {
        guard let period = product.subscription?.subscriptionPeriod else { return "billing period unavailable" }
        let unit: String
        switch period.unit {
        case .day: unit = period.value == 1 ? "day" : "days"
        case .week: unit = period.value == 1 ? "week" : "weeks"
        case .month: unit = period.value == 1 ? "month" : "months"
        case .year: unit = period.value == 1 ? "year" : "years"
        @unknown default: unit = "period"
        }
        return "\(period.value) \(unit)"
    }
    deinit { listener?.cancel() }
}
