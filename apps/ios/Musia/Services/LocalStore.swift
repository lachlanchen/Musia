import Combine
import Foundation
import MusiaCore

@MainActor
final class LocalStore: ObservableObject {
    @Published private(set) var records: [PracticeRecord]
    @Published private(set) var error: String?
    private let repository: HistoryRepository

    init() {
        repository = HistoryRepository()
        records = repository.records
        error = repository.loadError
    }

    func save(_ record: PracticeRecord) {
        do {
            try repository.upsert(record)
            records = repository.records
        } catch { self.error = "History could not be saved: \(error.localizedDescription)" }
    }

    func export() throws -> Data { try repository.export() }

    func reset() {
        repository.reset()
        records = []; error = nil
    }
}
