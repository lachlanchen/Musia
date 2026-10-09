import XCTest
@testable import MusiaCore
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

private final class CreatorTestProtocol: URLProtocol {
    static var responseCode = 200
    static var responseData = Data()
    static var request: URLRequest?
    static var requestBody: Data?
    static var requestCount = 0
    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        Self.request = request
        Self.requestCount += 1
        Self.requestBody = request.httpBody
        if Self.requestBody == nil, let stream = request.httpBodyStream {
            stream.open(); defer { stream.close() }
            var data = Data()
            var buffer = [UInt8](repeating: 0, count: 4096)
            while stream.hasBytesAvailable {
                let count = stream.read(&buffer, maxLength: buffer.count)
                if count <= 0 { break }
                data.append(contentsOf: buffer.prefix(count))
            }
            Self.requestBody = data
        }
        let response = HTTPURLResponse(url: request.url!, statusCode: Self.responseCode,
                                       httpVersion: nil, headerFields: ["Content-Type": "application/json"])!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: Self.responseData)
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() {}
}

final class CreatorAPITests: XCTestCase {
    private var session: URLSession!
    private var api: CreatorAPI!
    override func setUp() {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [CreatorTestProtocol.self]
        session = URLSession(configuration: configuration)
        api = CreatorAPI(session: session)
        CreatorTestProtocol.responseCode = 200
        CreatorTestProtocol.responseData = Data()
        CreatorTestProtocol.request = nil
        CreatorTestProtocol.requestBody = nil
        CreatorTestProtocol.requestCount = 0
    }
    override func tearDown() { session.invalidateAndCancel() }
    func testAnonymousCommunityHasNoBearerAndGETHasNoBody() async throws {
        CreatorTestProtocol.responseData = Data("{\"songs\":[]}".utf8)
        let result: CreatorSongs = try await api.request("/api/songs?mode=public")
        XCTAssertTrue(result.songs.isEmpty)
        XCTAssertEqual(CreatorTestProtocol.request?.url?.absoluteString, "https://musia.lazying.art/creator/api/songs?mode=public")
        XCTAssertEqual(CreatorTestProtocol.request?.httpMethod, "GET")
        XCTAssertEqual(CreatorTestProtocol.request?.value(forHTTPHeaderField: "X-Musia-Request"), "1")
        XCTAssertNil(CreatorTestProtocol.request?.value(forHTTPHeaderField: "Authorization"))
        XCTAssertNil(CreatorTestProtocol.request?.httpBody)
    }
    func testRenderReconnectionUsesFrozenBodyAndIdempotencyHeader() async throws {
        var brief = CreatorBrief(); brief.title = "Draft"; brief.lyrics = "Line"; brief.caption = "Piano"
        let pending = PendingCreatorRender(owner: "owner", request: .init(brief: brief, visibility: .private))
        let payload = try CreatorAPI.body(pending.request)
        _ = try await api.send("/api/jobs", token: "unit-test-token", body: payload, idempotencyKey: pending.key)
        let firstBody = CreatorTestProtocol.requestBody
        CreatorTestProtocol.responseCode = 503
        do {
            _ = try await api.send("/api/jobs", token: "unit-test-token", body: payload, idempotencyKey: pending.key)
            XCTFail("Unknown response must remain an error")
        } catch {}
        XCTAssertEqual(CreatorTestProtocol.requestCount, 2)
        XCTAssertEqual(firstBody, payload)
        XCTAssertEqual(firstBody, CreatorTestProtocol.requestBody)
        XCTAssertEqual(CreatorTestProtocol.request?.value(forHTTPHeaderField: "Idempotency-Key"), pending.key)
        XCTAssertEqual(CreatorTestProtocol.request?.value(forHTTPHeaderField: "Authorization"), "Bearer unit-test-token")
    }
    func testServerErrorIsNotAnEmptySuccess() async throws {
        CreatorTestProtocol.responseCode = 403
        CreatorTestProtocol.responseData = Data("{\"detail\":\"invitation_required\"}".utf8)
        do {
            let _: CreatorJobs = try await api.request("/api/jobs", token: "unit-test-token")
            XCTFail("Expected a permission error")
        } catch CreatorError.server(let status, let code) {
            XCTAssertEqual(status, 403); XCTAssertEqual(code, "invitation_required")
        }
    }
    func testSuccessfulEmptyMutationResponseIsAccepted() async throws {
        CreatorTestProtocol.responseCode = 204
        let data = try await api.send("/api/comments/comment-1", method: "DELETE", token: "unit-test-token")
        XCTAssertTrue(data.isEmpty)
        XCTAssertEqual(CreatorTestProtocol.request?.httpMethod, "DELETE")
    }
}
