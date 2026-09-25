import Foundation

public enum PracticeMode: String, Codable, CaseIterable, Sendable {
    case listen = "Listen", tap = "Tap", play = "Play"
}

public struct PracticeRecord: Codable, Identifiable, Sendable {
    public let id: UUID
    public let songID: String
    public let title: String
    public let assetID: String
    public let date: Date
    public var mode: PracticeMode
    public var seconds: Double
    public var rate: Double
    public var tapCount: Int
    public var absoluteOffsetTotal: Double

    public var meanAbsoluteOffset: Double? {
        tapCount > 0 ? absoluteOffsetTotal / Double(tapCount) : nil
    }

    public init(songID: String, title: String, assetID: String, mode: PracticeMode, rate: Double) {
        id = UUID(); date = Date()
        self.songID = songID; self.title = title; self.assetID = assetID
        self.mode = mode; self.rate = rate
        seconds = 0; tapCount = 0; absoluteOffsetTotal = 0
    }
}

public final class HistoryRepository {
    private let defaults: UserDefaults
    private let key = "musia.history.v1"
    public private(set) var records: [PracticeRecord] = []
    public private(set) var loadError: String?

    public init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        if let data = defaults.data(forKey: key) {
            do { records = try JSONDecoder().decode([PracticeRecord].self, from: data) }
            catch { loadError = "Saved history could not be read. Reset local data to start again." }
        }
    }

    public func upsert(_ record: PracticeRecord) throws {
        guard loadError == nil else { return }
        var updated = records.filter { $0.id != record.id }
        updated.insert(record, at: 0)
        updated = Array(updated.prefix(200))
        let data = try JSONEncoder().encode(updated)
        defaults.set(data, forKey: key)
        records = updated
    }

    public func reset() {
        defaults.removeObject(forKey: key)
        records = []; loadError = nil
    }

    public func export() throws -> Data {
        struct Export: Encodable {
            let version = 1
            let exportedAt: Date
            let records: [PracticeRecord]
        }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        encoder.dateEncodingStrategy = .iso8601
        return try encoder.encode(Export(exportedAt: Date(), records: records))
    }
}
