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
    private let api = APIClient()

    func loadLibrary(force: Bool = false) async {
        guard !loadingLibrary, force || !hasLibrary else { return }
        loadingLibrary = true; libraryError = nil
        defer { loadingLibrary = false }
        do {
            items = try await api.library()
            hasLibrary = true
        } catch is CancellationError { }
        catch let error as URLError where error.code == .cancelled { }
        catch { libraryError = error.localizedDescription }
    }

    func loadLessons(force: Bool = false) async {
        guard !loadingLessons, force || !hasLessons else { return }
        loadingLessons = true; lessonsError = nil
        defer { loadingLessons = false }
        do {
            lessons = try await api.lessons()
            hasLessons = true
        } catch is CancellationError { }
        catch let error as URLError where error.code == .cancelled { }
        catch { lessonsError = error.localizedDescription }
    }
}
