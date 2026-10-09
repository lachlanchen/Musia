import Combine
import Foundation
import MusiaCore

@MainActor
final class CatalogStore: ObservableObject {
    @Published private(set) var items: [LibraryItem] = []
    @Published private(set) var lessons: [Lesson] = []
    @Published private(set) var libraryError: String?
    @Published private(set) var lessonsError: String?
    @Published private(set) var loadingLibrary = false
    @Published private(set) var loadingLessons = false
    private var hasLibrary = false
    private var hasLessons = false
    private let libraryLoader: () async throws -> [LibraryItem]
    private let lessonsLoader: () async throws -> [Lesson]
    private var libraryTask: Task<Void, Never>?
    private var lessonsTask: Task<Void, Never>?

    init(libraryLoader: @escaping () async throws -> [LibraryItem] = { try await APIClient().library() },
         lessonsLoader: @escaping () async throws -> [Lesson] = { try await APIClient().lessons() }) {
        self.libraryLoader = libraryLoader
        self.lessonsLoader = lessonsLoader
    }

    func loadLibrary(force: Bool = false) async {
        if let libraryTask { await libraryTask.value; return }
        guard force || !hasLibrary else { return }
        loadingLibrary = true; libraryError = nil
        // The store owns the request; transient SwiftUI task cancellation only
        // cancels a waiter, not the shared catalog load.
        let task = Task {
            defer { loadingLibrary = false; libraryTask = nil }
            do {
                items = try await libraryLoader()
                hasLibrary = true
            } catch is CancellationError { }
            catch let error as URLError where error.code == .cancelled { }
            catch { libraryError = error.localizedDescription }
        }
        libraryTask = task
        await task.value
    }

    func loadLessons(force: Bool = false) async {
        if let lessonsTask { await lessonsTask.value; return }
        guard force || !hasLessons else { return }
        loadingLessons = true; lessonsError = nil
        let task = Task {
            defer { loadingLessons = false; lessonsTask = nil }
            do {
                lessons = try await lessonsLoader()
                hasLessons = true
            } catch is CancellationError { }
            catch let error as URLError where error.code == .cancelled { }
            catch { lessonsError = error.localizedDescription }
        }
        lessonsTask = task
        await task.value
    }
}
