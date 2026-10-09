import AuthenticationServices
import CryptoKit
import Foundation
import MusiaCore
import Security
#if os(iOS)
import UIKit
#else
import AppKit
#endif

enum CreatorKeychain {
    private static func query(_ key: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: "art.lazying.musia.creator",
         kSecAttrAccount as String: key,
         kSecUseDataProtectionKeychain as String: true]
    }
    static func read<T: Decodable>(_ type: T.Type, key: String) throws -> T? {
        var request = query(key)
        request[kSecReturnData as String] = true
        request[kSecMatchLimit as String] = kSecMatchLimitOne
        var result: CFTypeRef?
        let status = SecItemCopyMatching(request as CFDictionary, &result)
        if status == errSecItemNotFound { return nil }
        guard status == errSecSuccess, let data = result as? Data else { throw CreatorError.storage }
        do { return try JSONDecoder().decode(type, from: data) }
        catch { throw CreatorError.storage }
    }
    static func write<T: Encodable>(_ value: T, key: String) throws {
        let data = try JSONEncoder().encode(value)
        let attributes: [String: Any] = [kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly]
        let status = SecItemUpdate(query(key) as CFDictionary, attributes as CFDictionary)
        if status == errSecItemNotFound {
            var request = query(key); attributes.forEach { request[$0.key] = $0.value }
            guard SecItemAdd(request as CFDictionary, nil) == errSecSuccess else { throw CreatorError.storage }
        } else if status != errSecSuccess { throw CreatorError.storage }
    }
    static func remove(_ key: String) throws {
        let status = SecItemDelete(query(key) as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else { throw CreatorError.storage }
    }
}

/// The visible foreground window is resolved only at a user gesture, never a
/// synthetic window or a scene retained across background/account transitions.
@MainActor
enum CreatorPresentation {
    static func anchor() throws -> ASPresentationAnchor {
#if os(iOS)
        guard let window = UIApplication.shared.connectedScenes.compactMap({ $0 as? UIWindowScene })
            .filter({ $0.activationState == .foregroundActive })
            .flatMap(\.windows).first(where: \.isKeyWindow) else {
            throw CreatorError.unavailable("Open Musia in the foreground to continue.")
        }
#else
        guard NSApp.isActive, let window = NSApp.keyWindow, window.isVisible else {
            throw CreatorError.unavailable("Select the Musia window to continue.")
        }
#endif
        return window
    }
}

@MainActor
private final class CreatorAuthContext: NSObject, ASWebAuthenticationPresentationContextProviding {
    let window: ASPresentationAnchor
    init(window: ASPresentationAnchor) { self.window = window }
    func presentationAnchor(for session: ASWebAuthenticationSession) -> ASPresentationAnchor { window }
}

@MainActor
final class CreatorAuthentication {
    private var session: ASWebAuthenticationSession?
    private var context: CreatorAuthContext?
    private var continuation: CheckedContinuation<URL, Error>?
    private var operation = UUID()

    func signIn(api: CreatorAPI) async throws -> NativeAuthToken {
        guard session == nil else { throw CreatorError.unavailable("Sign-in is already open.") }
        let operation = UUID(); self.operation = operation
        context = CreatorAuthContext(window: try CreatorPresentation.anchor())
        var bytes = [UInt8](repeating: 0, count: 32)
        guard SecRandomCopyBytes(kSecRandomDefault, bytes.count, &bytes) == errSecSuccess else { throw CreatorError.storage }
        let verifier = Self.base64url(Data(bytes))
        let challenge = Self.base64url(Data(SHA256.hash(data: Data(verifier.utf8))))
        let start: NativeAuthStart = try await api.request("/auth/native/start", method: "POST",
            body: CreatorAPI.body(["challenge": challenge, "platform": "apple"]))
        guard operation == self.operation else { throw CancellationError() }
        guard APIClient.isSecureRemoteURL(start.url), !start.attempt.isEmpty,
              start.expiresIn > 0, start.expiresIn <= 600 else { throw CreatorError.invalidCallback }
        let attempt = NativeAuthAttempt(attempt: start.attempt, verifier: verifier,
                                       expiresAt: Date().addingTimeInterval(start.expiresIn))
        try CreatorKeychain.write(attempt, key: "auth-attempt")
        defer {
            if operation == self.operation {
                try? CreatorKeychain.remove("auth-attempt")
                session = nil; context = nil
            }
        }
        let callback = try await withTaskCancellationHandler {
            try await withCheckedThrowingContinuation { continuation in
                self.continuation = continuation
                let auth = ASWebAuthenticationSession(url: start.url, callbackURLScheme: "art.lazying.musia") { [weak self] url, error in
                    Task { @MainActor in
                        guard let self, operation == self.operation else { return }
                        let waiting = self.continuation; self.continuation = nil
                        if let url { waiting?.resume(returning: url) }
                        else { waiting?.resume(throwing: error ?? CreatorError.invalidCallback) }
                    }
                }
                auth.presentationContextProvider = self.context
                auth.prefersEphemeralWebBrowserSession = true
                self.session = auth
                if !auth.start() {
                    self.continuation = nil
                    continuation.resume(throwing: CreatorError.unavailable("The system browser could not open. Try again."))
                }
            }
        } onCancel: { Task { @MainActor [weak self] in self?.cancel() } }
        guard operation == self.operation,
              let saved = try CreatorKeychain.read(NativeAuthAttempt.self, key: "auth-attempt"),
              saved.attempt == attempt.attempt, saved.verifier == verifier else { throw CreatorError.invalidCallback }
        let code = try saved.code(from: callback)
        let token: NativeAuthToken = try await api.request("/auth/native/exchange", method: "POST",
            body: CreatorAPI.body(["attempt": saved.attempt, "code": code, "verifier": saved.verifier, "platform": "apple"]))
        guard operation == self.operation, !token.token.isEmpty, token.expiresIn > 0 else { throw CreatorError.invalidCallback }
        return token
    }
    func cancel() {
        operation = UUID()
        let waiting = continuation; continuation = nil
        session?.cancel(); session = nil; context = nil
        try? CreatorKeychain.remove("auth-attempt")
        waiting?.resume(throwing: CancellationError())
    }
    private static func base64url(_ data: Data) -> String {
        data.base64EncodedString().replacingOccurrences(of: "+", with: "-")
            .replacingOccurrences(of: "/", with: "_").replacingOccurrences(of: "=", with: "")
    }
}
