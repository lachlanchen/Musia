import XCTest
@testable import MusiaCore

final class ContractTests: XCTestCase {
    func testFirstPulseContractAndExactPCMGrid() throws {
        let song = try FirstPulse.song(audioURL: URL(fileURLWithPath: "/tmp/first-pulse.wav"))
        let asset = try XCTUnwrap(song.defaultAsset)
        XCTAssertEqual(asset.bpm, 60)
        XCTAssertEqual(asset.confidence.beats, .verified)
        XCTAssertEqual(asset.confidence.chords, .verified)
        XCTAssertEqual(asset.beats.map(\.time), (0..<20).map(Double.init))
        XCTAssertTrue(asset.lyrics.isEmpty)
        XCTAssertEqual(asset.loopPhrases.last?.end, 20)
        XCTAssertEqual(asset.chords.map(\.name), ["Em", "Am", "Em", "Am"])
        XCTAssertEqual(asset.chords.map(\.start), [4, 8, 12, 16])
        let wav = FirstPulse.wavData()
        XCTAssertEqual(wav.count, 44 + 22 * FirstPulse.sampleRate * 2)
        XCTAssertEqual(String(decoding: wav.prefix(4), as: UTF8.self), "RIFF")
        XCTAssertEqual(wav, FirstPulse.wavData())
        for beat in 0..<20 {
            let offset = 44 + beat * FirstPulse.sampleRate * 2
            XCTAssertTrue(wav[(offset + 2)..<(offset + 1_000)].contains { $0 != 0 })
            if beat < 4 {
                XCTAssertTrue(wav[(offset + 12_000)..<(offset + 14_000)].allSatisfy { $0 == 0 })
            }
        }
        XCTAssertEqual(Array(wav.suffix(2)), [0, 0])
    }

    func testContractDecodesTokensConfidenceAndBothNoteFormats() throws {
        let json = """
        {"version":1,"id":"a","title":"Song","artist":"Artist","coverUrl":null,
        "defaultAssetId":"v","assets":[{"id":"v","label":"Vocal","language":"en",
        "audioUrl":"https://example.com/a.m4a","duration":8,"bpm":60,"timeSignature":"4/4",
        "confidence":{"beats":"analysis","chords":"estimated","melody":"new-value"},
        "beats":[{"time":0},{"time":1}],"chords":[{"start":0,"end":2,"name":"C","confidence":0.8}],
        "lyrics":[{"id":"l","start":0,"end":2,"text":"Hello","tokens":[
        {"text":"Hello","start":0,"end":2,"reading":"heh-loh"}]}],"phrases":[],
        "melody":[{"start":0,"end":1,"note":60,"numberNote":"1","text":"Hello"}]}]}
        """
        let song = try JSONDecoder().decode(Song.self, from: Data(json.utf8)).validated()
        let asset = try XCTUnwrap(song.defaultAsset)
        XCTAssertEqual(asset.confidence.melody, .unavailable)
        XCTAssertEqual(asset.melody.first?.note.text, "60")
        XCTAssertEqual(asset.lyrics.first?.tokens.first?.reading, "heh-loh")
        XCTAssertEqual(asset.loopPhrases.first?.text, "Hello")
        XCTAssertEqual(asset.displayLyricTracks.map(\.language), ["en"])
        XCTAssertEqual(asset.displayLyricTracks.first?.lines.first?.text, "Hello")
        var dto = try XCTUnwrap(JSONSerialization.jsonObject(with: Data(json.utf8)) as? [String: Any])
        var assets = try XCTUnwrap(dto["assets"] as? [[String: Any]])
        assets[0]["lyricTracks"] = [["language": "ja", "lines": [["id": "l", "start": 0, "end": 2,
            "text": "光", "tokens": [["text": "光", "start": 0, "end": 2, "reading": "ひかり"]]]]]]
        dto["assets"] = assets
        let updated = try JSONDecoder().decode(Song.self, from: JSONSerialization.data(withJSONObject: dto)).validated()
        XCTAssertEqual(updated.defaultAsset?.displayLyricTracks.first?.lines.first?.tokens.first?.reading, "ひかり")
        let invalid = json.replacingOccurrences(of: "\"end\":2", with: "\"end\":20")
        XCTAssertThrowsError(try JSONDecoder().decode(Song.self, from: Data(invalid.utf8)).validated())
        let wrongVersion = json.replacingOccurrences(of: "\"version\":1", with: "\"version\":2")
        XCTAssertThrowsError(try JSONDecoder().decode(Song.self, from: Data(wrongVersion.utf8)).validated())
    }

    func testDuplicateLibraryIDsAreRejected() throws {
        let item = "{\"id\":\"a\",\"title\":\"A\",\"artist\":\"B\",\"duration\":1,\"kind\":\"song\"}"
        let data = Data("{\"version\":1,\"items\":[\(item),\(item)]}".utf8)
        XCTAssertThrowsError(try JSONDecoder().decode(LibraryResponse.self, from: data).validated())
    }

    func testHistoryPersistenceResetAndExport() throws {
        let suite = "musia.tests.\(UUID().uuidString)"
        let defaults = try XCTUnwrap(UserDefaults(suiteName: suite))
        defer { defaults.removePersistentDomain(forName: suite) }
        let repository = HistoryRepository(defaults: defaults)
        var record = PracticeRecord(songID: "a", title: "A", assetID: "v", mode: .tap, rate: 0.5)
        record.seconds = 10; record.tapCount = 2; record.absoluteOffsetTotal = 120
        try repository.upsert(record)
        record.seconds = 11
        try repository.upsert(record)
        XCTAssertEqual(repository.records.count, 1)
        XCTAssertEqual(repository.records.first?.meanAbsoluteOffset, 60)
        XCTAssertEqual(HistoryRepository(defaults: defaults).records.first?.seconds, 11)
        let json = try XCTUnwrap(JSONSerialization.jsonObject(with: repository.export()) as? [String: Any])
        XCTAssertEqual(json["version"] as? Int, 1)
        XCTAssertEqual((json["records"] as? [[String: Any]])?.count, 1)
        defaults.set("unrelated", forKey: "another.key")
        repository.reset()
        XCTAssertTrue(HistoryRepository(defaults: defaults).records.isEmpty)
        XCTAssertEqual(defaults.string(forKey: "another.key"), "unrelated")
    }
}
