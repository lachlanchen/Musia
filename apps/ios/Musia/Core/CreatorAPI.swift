import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// Authorization must never follow a redirect to a different host (or downgrade).
private final class CreatorRedirectPolicy: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    func urlSession(_ session: URLSession, task: URLSessionTask,
                    willPerformHTTPRedirection response: HTTPURLResponse, newRequest request: URLRequest,
                    completionHandler: @escaping (URLRequest?) -> Void) { completionHandler(nil) }
}

public final class CreatorAPI: @unchecked Sendable {
    public static let origin = URL(string: "https://musia.lazying.art")!
    private let session: URLSession
    public init(session: URLSession? = nil) {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.httpCookieStorage = nil
        configuration.urlCache = nil
        self.session = session ?? URLSession(configuration: configuration, delegate: CreatorRedirectPolicy(), delegateQueue: nil)
    }
    public static func segment(_ value: String) throws -> String {
        guard !value.isEmpty, value != ".", value != "..",
              let encoded = value.addingPercentEncoding(withAllowedCharacters:
                .alphanumerics.union(CharacterSet(charactersIn: "-_~"))) else { throw URLError(.badURL) }
        return encoded
    }
    public static func mediaURL(_ value: String) throws -> URL {
        guard let url = URL(string: value, relativeTo: origin)?.absoluteURL,
              url.scheme == "https", url.host == origin.host, url.port == nil,
              url.user == nil, url.password == nil, url.fragment == nil,
              url.path.hasPrefix("/creator/") else { throw CreatorError.unsafeURL }
        return url
    }
    public func request<T: Decodable>(_ path: String, method: String = "GET", token: String? = nil,
                                       body: Data? = nil, idempotencyKey: String? = nil) async throws -> T {
        let data = try await send(path, method: method, token: token, body: body, idempotencyKey: idempotencyKey)
        return try JSONDecoder().decode(T.self, from: data)
    }
    public func send(_ path: String, method: String = "POST", token: String? = nil,
                     body: Data? = Data("{}".utf8), idempotencyKey: String? = nil) async throws -> Data {
        guard path.hasPrefix("/api/") || path.hasPrefix("/auth/"),
              let url = URL(string: "/creator" + path, relativeTo: Self.origin)?.absoluteURL,
              url.host == Self.origin.host else { throw CreatorError.unsafeURL }
        var request = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 45)
        request.httpMethod = method
        request.httpBody = method == "GET" ? nil : body
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        request.setValue("1", forHTTPHeaderField: "X-Musia-Request")
        if let token { request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization") }
        if let idempotencyKey { request.setValue(idempotencyKey, forHTTPHeaderField: "Idempotency-Key") }
        let (data, response) = try await session.data(for: request)
        try Task.checkCancellation()
        try Self.validate(response, data: data)
        guard data.count < 12_000_000 else { throw APIError.tooLarge }
        return data
    }
    public func downloadAudio(_ url: URL, token: String?) async throws -> URL {
        _ = try Self.mediaURL(url.absoluteString)
        var request = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 120)
        request.setValue("1", forHTTPHeaderField: "X-Musia-Request")
        if let token { request.setValue("Bearer " + token, forHTTPHeaderField: "Authorization") }
        let (temporary, response) = try await session.download(for: request)
        do { try Self.validate(response, data: Data()); try Task.checkCancellation() }
        catch { try? FileManager.default.removeItem(at: temporary); throw error }
        return temporary
    }
    private static func validate(_ response: URLResponse, data: Data) throws {
        guard let http = response as? HTTPURLResponse else { throw URLError(.badServerResponse) }
        guard (200..<300).contains(http.statusCode) else {
            struct Detail: Decodable { let detail: String }
            let code = (try? JSONDecoder().decode(Detail.self, from: data).detail) ?? "request_failed"
            throw CreatorError.server(http.statusCode, String(code.prefix(180)))
        }
    }
    public static func body<T: Encodable>(_ value: T) throws -> Data {
        let encoder = JSONEncoder(); encoder.outputFormatting = [.sortedKeys]
        return try encoder.encode(value)
    }
}
