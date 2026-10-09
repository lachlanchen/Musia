import MusiaCore
import StoreKit
import SwiftUI

struct CreatorLegalLinks: View {
    var body: some View {
        Link("Creator terms", destination: URL(string: "https://musia.lazying.art/creator/terms")!)
        Link("Privacy policy", destination: URL(string: "https://musia.lazying.art/privacy")!)
        Link("Apple standard license agreement", destination: URL(string: "https://www.apple.com/legal/internet-services/itunes/dev/stdeula/")!)
    }
}

struct CreatorAccountView: View {
    @EnvironmentObject private var creator: CreatorStore
    @EnvironmentObject private var billing: CreatorBillingStore
    @State private var invitation = ""
    @State private var acceptTerms = false
    @State private var confirmDelete = false
    @State private var confirmLogout = false
    @State private var confirmSync = false

    var body: some View {
        Form {
            Section("Musia account") {
                if let account = creator.account {
                    Label(account.name, systemImage: "person.crop.circle.fill").font(.headline)
                    LabeledContent("Plan", value: account.usage.tier.capitalized)
                    LabeledContent("Usage period", value: account.usage.period)
                    LabeledContent("Renders used", value: "\(account.usage.used) of \(account.usage.limit)")
                    LabeledContent("Renders remaining", value: String(account.usage.remaining))
                    Text("Usage is provided by the Musia server.").font(.caption).foregroundStyle(.secondary)
                } else {
                    Text("An account is optional. Sign in to create, save songs, and join the community.")
                    Button("Sign in with your browser", systemImage: "person.crop.circle.badge.checkmark") {
                        Task { await creator.signIn() }
                    }.buttonStyle(.borderedProminent)
                        .disabled(creator.busy || creator.hasSession || creator.capabilities?.login != true)
                    if creator.hasSession { Text("Reconnecting your existing session. Refresh to try again.").font(.caption) }
                    else if creator.capabilities?.login != true { Text("Sign-in is unavailable. Refresh to check service status.").font(.caption) }
                }
                Button("Refresh account", systemImage: "arrow.clockwise") { Task { await creator.refresh() } }
                    .disabled(creator.refreshing || creator.busy)
            }
            CreatorNotice()
            if let account = creator.account {
                if !account.termsAccepted {
                    Section("Creator terms") {
                        CreatorLegalLinks()
                        Text("Version: \(creator.capabilities?.termsVersion ?? "Unavailable")").font(.caption)
                        Toggle("I have read and accept the creator terms.", isOn: $acceptTerms)
                        Button("Accept terms") { Task { await creator.accountAction("/api/terms") } }
                            .disabled(!acceptTerms || creator.busy || creator.capabilities == nil)
                    }
                }
                if !account.invited {
                    Section("Invitation") {
                        CreatorTextField(title: "Invitation code", text: $invitation)
                            .autocorrectionDisabled()
#if os(iOS)
                            .textInputAutocapitalization(.never)
#endif
                        Button("Redeem invitation") {
                            Task {
                                if let body = try? CreatorAPI.body(["code": invitation.trimmingCharacters(in: .whitespacesAndNewlines)]) {
                                    await creator.accountAction("/api/invitations/redeem", body: body)
                                }
                            }
                        }.disabled(invitation.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || creator.busy)
                    }
                }
                Section {
                    NavigationLink { CreatorBlocksView() } label: { Label("Blocked accounts", systemImage: "person.crop.circle.badge.xmark") }
                }
            }
            Section("Subscriptions") {
                if let entitlement = billing.billing?.entitlement {
                    LabeledContent("Server entitlement", value: entitlement.tier.capitalized)
                    LabeledContent("Status", value: entitlement.state.replacingOccurrences(of: "_", with: " ").capitalized)
                    if let expiry = entitlement.expiresAt {
                        LabeledContent("Valid until", value: Date(timeIntervalSince1970: expiry).formatted(date: .abbreviated, time: .shortened))
                    }
                    if let environment = entitlement.environment { LabeledContent("Store environment", value: environment.capitalized) }
                }
                Text("Free includes 2 renders per period. Creator includes 20; Studio includes 80. Your account shows the current server allowance.")
                    .font(.subheadline).foregroundStyle(.secondary)
                if billing.products.isEmpty {
                    Text("App Store pricing is unavailable. No purchase will start until products and account eligibility are confirmed.")
                        .foregroundStyle(.secondary)
                    Button("Reload App Store prices") { Task { await billing.loadProducts() } }
                }
                ForEach(billing.products, id: \.id) { product in
                    VStack(alignment: .leading, spacing: 8) {
                        Text(product.displayName).font(.headline)
                        Text(product.description).foregroundStyle(.secondary)
                        Text("\(product.displayPrice) / \(CreatorBillingStore.period(product))").font(.title3.bold()).foregroundStyle(Palette.teal)
                        Button("Subscribe to \(product.displayName)") { Task { await billing.purchase(product) } }
                            .buttonStyle(.borderedProminent)
                            .disabled(!billing.purchaseAllowed)
                    }.padding(.vertical, 6)
                }
                if !billing.purchaseAllowed {
                    Text(billing.purchaseExplanation)
                        .font(.caption).foregroundStyle(.secondary)
                }
                if billing.busy { ProgressView("Checking purchases…") }
                if let message = billing.message { Text(message).foregroundStyle(.secondary).fixedSize(horizontal: false, vertical: true) }
                Button("Restore / check purchases", systemImage: "arrow.clockwise") { Task { await billing.restore() } }
                    .disabled(creator.account == nil || billing.busy)
                Button("Find missing Apple purchases…") { confirmSync = true }
                    .disabled(creator.account == nil || billing.busy)
                Link(destination: URL(string: "https://apps.apple.com/account/subscriptions")!) {
                    Label("Manage Apple subscriptions", systemImage: "arrow.up.right.square")
                }
                Text("Subscriptions renew automatically unless cancelled in your Apple account before the renewal date. Payment is charged to your Apple account. Deleting a Musia account does not cancel an Apple subscription.")
                    .font(.caption).foregroundStyle(.secondary)
                CreatorLegalLinks()
                Link("Subscription support", destination: URL(string: "https://musia.lazying.art/support")!)
            }
            if creator.hasSession {
                Section("Account controls") {
                    Button("Sign out", role: .destructive) { confirmLogout = true }.disabled(creator.busy)
                    Button("Delete creator account", role: .destructive) { confirmDelete = true }
                        .disabled(creator.account == nil || creator.busy || billing.busy)
                }
            }
        }
        .formStyle(.grouped)
        .navigationTitle("Account & subscriptions")
        .onChange(of: creator.identity) { _, _ in invitation = ""; acceptTerms = false }
        .onChange(of: creator.capabilities?.termsVersion) { _, _ in acceptTerms = false }
        .confirmationDialog("Sign out of Musia?", isPresented: $confirmLogout, titleVisibility: .visible) {
            Button("Sign out", role: .destructive) { Task { await creator.logout() } }
        } message: { Text("Private playback and local account data will be cleared. Any unconfirmed render stays securely linked to its original account for recovery.") }
        .confirmationDialog("Ask Apple to find missing purchases?", isPresented: $confirmSync, titleVisibility: .visible) {
            Button("Continue with Apple") { Task { await billing.findMissingPurchases() } }
        } message: { Text("Apple may ask you to sign in. Use this only when ordinary Restore cannot find an existing purchase. This does not start a new purchase.") }
        .confirmationDialog("Delete your creator account?", isPresented: $confirmDelete, titleVisibility: .visible) {
            Button("Permanently delete account", role: .destructive) { Task { await creator.deleteAccount() } }
        } message: {
            Text("This removes your creator account and its server data. It cannot be undone. Manage your Apple subscription separately to stop renewal. Your local learning history is kept.")
        }
    }
}
