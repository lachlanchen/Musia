import XCTest
@testable import MusiaCore
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

private final class StubProtocol: URLProtocol {
    static var responseCode = 200
    static var responseData = Data()
    static var capturedRequest: URLRequest?

    override class func canInit(with request: URLRequest) -> Bool { true }
    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }
    override func startLoading() {
        Self.capturedRequest = request
        let response = HTTPURLResponse(url: request.url!, statusCode: Self.responseCode,
                                       httpVersion: nil, headerFields: ["Content-Type": "application/json"])!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: Self.responseData)
        client?.urlProtocolDidFinishLoading(self)
    }
    override func stopLoading() { }
}

final class APIClientTests: XCTestCase {
    private var session: URLSession!
    private var api: APIClient!

    override func setUp() {
        super.setUp()
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StubProtocol.self]
        session = URLSession(configuration: configuration)
        api = APIClient(session: session)
        StubProtocol.responseCode = 200
        StubProtocol.capturedRequest = nil
    }

    override func tearDown() {
        session.invalidateAndCancel()
        super.tearDown()
    }

    func testLibraryUsesPublicGETContract() async throws {
        StubProtocol.responseData = Data("{\"version\":1,\"items\":[]}".utf8)
        let items = try await api.library()
        XCTAssertTrue(items.isEmpty)
        XCTAssertEqual(StubProtocol.capturedRequest?.url?.absoluteString, "https://musia.lazying.art/api/v1/library")
        XCTAssertEqual(StubProtocol.capturedRequest?.httpMethod, "GET")
        XCTAssertNil(StubProtocol.capturedRequest?.value(forHTTPHeaderField: "Authorization"))
    }

    func testHTTPFailureIsNotTreatedAsEmptyLibrary() async {
        StubProtocol.responseCode = 503
        StubProtocol.responseData = Data("service unavailable".utf8)
        do { _ = try await api.library(); XCTFail("Expected HTTP error") }
        catch APIError.http(let status) { XCTAssertEqual(status, 503) }
        catch { XCTFail("Unexpected error: \(error)") }
    }

    func testInvalidJSONIsReported() async {
        StubProtocol.responseData = Data("<html>not the API</html>".utf8)
        do { _ = try await api.library(); XCTFail("Expected decoding error") }
        catch APIError.invalidJSON { }
        catch { XCTFail("Unexpected error: \(error)") }
    }

    func testSongIDIsEncodedAsOnePathSegment() async {
        StubProtocol.responseCode = 404
        do { _ = try await api.song(id: "a/b?c"); XCTFail("Expected 404") } catch { }
        XCTAssertEqual(StubProtocol.capturedRequest?.url?.absoluteString,
                       "https://musia.lazying.art/api/v1/songs/a%2Fb%3Fc")
    }

    func testLessonsContract() async throws {
        StubProtocol.responseData = Data("""
        {"lessons":[{"id":"listen","title":"Listen","focus":"pulse","body":"Body",
        "exerciseId":"first-pulse","steps":["Listen once"]}]}
        """.utf8)
        let lessons = try await api.lessons()
        XCTAssertEqual(lessons.first?.exerciseId, "first-pulse")
        XCTAssertEqual(StubProtocol.capturedRequest?.url?.path, "/api/v1/lessons")
    }
}
