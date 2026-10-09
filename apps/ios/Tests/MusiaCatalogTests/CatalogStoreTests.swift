import XCTest
import MusiaCore
@testable import MusiaCatalog

@MainActor
private final class ControlledLoader<Value> {
    private(set) var calls = 0
    private var continuation: CheckedContinuation<Value, Error>?
    private var started: CheckedContinuation<Void, Never>?

    func load() async throws -> Value {
        calls += 1
        let result = try await withCheckedThrowingContinuation { continuation in
            self.continuation = continuation
            started?.resume(); started = nil
        }
        try Task.checkCancellation()
        return result
    }

    func waitForStart() async {
        if continuation != nil { return }
        await withCheckedContinuation { started = $0 }
    }

    func finish(_ result: Result<Value, Error>) {
        let waiting = continuation; continuation = nil
        waiting?.resume(with: result)
    }
}

@MainActor
final class CatalogStoreTests: XCTestCase {
    private func item() throws -> MusiaCore.LibraryItem {
        try JSONDecoder().decode(MusiaCore.LibraryItem.self, from: Data("""
        {"id":"tone","title":"Tone","artist":"Musia","duration":30,"kind":"song"}
        """.utf8))
    }

    func testCancelledViewWaiterDoesNotCancelSharedLibraryLoad() async throws {
        let loader = ControlledLoader<[MusiaCore.LibraryItem]>()
        let store = CatalogStore(libraryLoader: loader.load)
        let first = Task { await store.loadLibrary() }
        await loader.waitForStart()
        first.cancel()
        let second = Task { await store.loadLibrary(force: true) }
        await Task.yield()
        XCTAssertEqual(loader.calls, 1)
        XCTAssertTrue(store.loadingLibrary)
        loader.finish(.success([try item()]))
        await first.value; await second.value
        XCTAssertEqual(store.items.map(\.id), ["tone"])
        XCTAssertFalse(store.loadingLibrary)
        XCTAssertNil(store.libraryError)
        await store.loadLibrary()
        XCTAssertEqual(loader.calls, 1)
    }

    func testAlreadyCancelledCallerStillStartsIndependentLoad() async throws {
        let loader = ControlledLoader<[MusiaCore.LibraryItem]>()
        let store = CatalogStore(libraryLoader: loader.load)
        let caller = Task { await store.loadLibrary() }
        caller.cancel()
        await loader.waitForStart()
        loader.finish(.success([try item()]))
        await caller.value
        XCTAssertEqual(store.items.count, 1)
        XCTAssertNil(store.libraryError)
    }

    func testFailureCanRetryAndForceRefreshPreservesExistingItemsOnFailure() async throws {
        var calls = 0
        let expected = try item()
        let store = CatalogStore(libraryLoader: {
            calls += 1
            if calls != 2 { throw URLError(.notConnectedToInternet) }
            return [expected]
        })
        await store.loadLibrary()
        XCTAssertNotNil(store.libraryError)
        XCTAssertFalse(store.loadingLibrary)
        await store.loadLibrary()
        XCTAssertNil(store.libraryError)
        XCTAssertEqual(store.items.count, 1)
        await store.loadLibrary()
        XCTAssertEqual(calls, 2)
        await store.loadLibrary(force: true)
        XCTAssertEqual(calls, 3)
        XCTAssertNotNil(store.libraryError)
        XCTAssertEqual(store.items.map(\.id), ["tone"])
    }

    func testTransportCancellationClearsLoadingAndAllowsRetry() async {
        var calls = 0
        let store = CatalogStore(libraryLoader: {
            calls += 1
            if calls == 1 { throw CancellationError() }
            if calls == 2 { throw URLError(.cancelled) }
            return []
        })
        for _ in 0..<3 {
            await store.loadLibrary()
            XCTAssertFalse(store.loadingLibrary)
            XCTAssertNil(store.libraryError)
        }
        XCTAssertEqual(calls, 3)
        await store.loadLibrary()
        XCTAssertEqual(calls, 3)
    }

    func testLessonsCoalesceAndSurviveWaiterCancellationIndependently() async {
        let library = ControlledLoader<[MusiaCore.LibraryItem]>()
        let lessons = ControlledLoader<[Lesson]>()
        let store = CatalogStore(libraryLoader: library.load, lessonsLoader: lessons.load)
        let first = Task { await store.loadLessons() }
        await lessons.waitForStart()
        first.cancel()
        let second = Task { await store.loadLessons(force: true) }
        let other = Task { await store.loadLibrary() }
        await library.waitForStart()
        XCTAssertEqual(lessons.calls, 1)
        lessons.finish(.success([]))
        await first.value; await second.value
        XCTAssertFalse(store.loadingLessons)
        XCTAssertTrue(store.loadingLibrary)
        XCTAssertNil(store.lessonsError)
        library.finish(.success([]))
        await other.value
        await store.loadLessons()
        XCTAssertEqual(lessons.calls, 1)
    }

    func testLessonsFailureRetryAndForcedReload() async {
        var calls = 0
        let store = CatalogStore(lessonsLoader: {
            calls += 1
            if calls == 1 { throw URLError(.timedOut) }
            return []
        })
        await store.loadLessons()
        XCTAssertNotNil(store.lessonsError)
        await store.loadLessons()
        XCTAssertNil(store.lessonsError)
        await store.loadLessons()
        XCTAssertEqual(calls, 2)
        await store.loadLessons(force: true)
        XCTAssertEqual(calls, 3)
    }
}
