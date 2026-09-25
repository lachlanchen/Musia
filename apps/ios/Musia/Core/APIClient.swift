import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

public struct APIClient {
    public static let productionURL = URL(string: "https://musia.lazying.art/api/v1")!
    private let baseURL: URL
    private let session: URLSession

    public init(baseURL: URL = Self.productionURL, session: URLSession = .shared) {
        self.baseURL = baseURL; self.session = session
    }

    public func library() async throws -> [LibraryItem] {
        let response: LibraryResponse = try await get("library")
        return try response.validated().items
    }

    public func song(id: String) async throws -> Song {
        let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-._~"))
        guard !id.isEmpty, let segment = id.addingPercentEncoding(withAllowedCharacters: allowed)
        else { throw ContractError.invalid("song identifier") }
        let response: Song = try await get("songs/\(segment)")
        guard response.id == id else { throw ContractError.invalid("song identifier") }
        let song = try response.validated()
        guard song.assets.allSatisfy({ Self.isSecureRemoteURL($0.audioUrl) })
        else { throw APIError.insecureMedia }
        return song
    }

    public func lessons() async throws -> [Lesson] {
        let response: LessonsResponse = try await get("lessons")
        return try response.validated().lessons
    }

    public static func isSecureRemoteURL(_ url: URL) -> Bool {
        url.scheme?.lowercased() == "https" && url.host != nil && url.user == nil && url.password == nil
    }

    private func get<T: Decodable>(_ path: String) async throws -> T {
        guard Self.isSecureRemoteURL(baseURL),
              var components = URLComponents(url: baseURL, resolvingAgainstBaseURL: false)
        else { throw APIError.insecureMedia }
        components.percentEncodedPath += "/" + path
        guard let url = components.url else { throw URLError(.badURL) }
        var request = URLRequest(url: url, cachePolicy: .reloadIgnoringLocalCacheData, timeoutInterval: 25)
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        let (data, response) = try await session.data(for: request)
        try Task.checkCancellation()
        guard let http = response as? HTTPURLResponse else { throw URLError(.badServerResponse) }
        guard (200..<300).contains(http.statusCode) else { throw APIError.http(http.statusCode) }
        guard data.count <= 10_000_000 else { throw APIError.tooLarge }
        do { return try JSONDecoder().decode(T.self, from: data) }
        catch { throw APIError.invalidJSON }
    }
}

public enum APIError: LocalizedError {
    case http(Int), invalidJSON, insecureMedia, tooLarge

    public var errorDescription: String? {
        switch self {
        case .http(404): return "This item is not available on the server."
        case .http(429): return "The server is busy. Wait a moment, then retry."
        case .http(let status): return "The server returned HTTP \(status). Please retry."
        case .invalidJSON: return "The server response does not match the Musia v1 catalog."
        case .insecureMedia: return "This resource needs a secure HTTPS address."
        case .tooLarge: return "The catalog response is too large."
        }
    }
}
