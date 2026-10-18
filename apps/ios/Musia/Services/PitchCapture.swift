import AVFoundation
import MusiaCore

@MainActor
final class PitchCapture: ObservableObject {
    @Published var busy = false
    @Published var message: String?
    @Published var result: PitchResult?
    private var recorder: AVAudioRecorder?
    private var temporary: URL?
    private var work: Task<Void, Never>?

    func cancel() {
        work?.cancel(); work = nil
        cleanup(); busy = false; message = nil
    }
    private func cleanup() {
        recorder?.stop(); recorder = nil
        if let temporary { try? FileManager.default.removeItem(at: temporary) }
        temporary = nil
#if os(iOS)
        try? AVAudioSession.sharedInstance().setCategory(.playback, mode: .default)
#endif
    }
    func start(targetHz: Double) {
        cancel(); result = nil; message = "Preparing microphone..."; busy = true
        work = Task {
#if os(iOS)
            let allowed = await AVAudioApplication.requestRecordPermission()
#else
            let allowed = await AVCaptureDevice.requestAccess(for: .audio)
#endif
            guard !Task.isCancelled else { return }
            guard allowed else {
                message = "Microphone access is off. Listening practice still works; enable the microphone in system settings to match your voice."
                busy = false; work = nil; return
            }
            do {
                try await Task.sleep(nanoseconds: 400_000_000)
#if os(iOS)
                try AVAudioSession.sharedInstance().setCategory(.playAndRecord, mode: .measurement, options: [.defaultToSpeaker])
                try AVAudioSession.sharedInstance().setActive(true)
#endif
                let url = FileManager.default.temporaryDirectory.appendingPathComponent("musia-pitch-\(UUID().uuidString).wav")
                temporary = url
                recorder = try AVAudioRecorder(url: url, settings: [
                    AVFormatIDKey: kAudioFormatLinearPCM, AVSampleRateKey: PitchPractice.sampleRate,
                    AVNumberOfChannelsKey: 1, AVLinearPCMBitDepthKey: 16,
                    AVLinearPCMIsFloatKey: false, AVLinearPCMIsBigEndianKey: false
                ])
                guard recorder?.record(forDuration: 3) == true else { throw CocoaError(.fileWriteUnknown) }
                message = "Sing or hum one comfortable note..."
                try await Task.sleep(nanoseconds: 3_000_000_000)
                recorder?.stop(); recorder = nil
                let file = try AVAudioFile(forReading: url)
                guard file.length > 0, file.length <= PitchPractice.sampleRate * 4,
                      Int(file.processingFormat.sampleRate) == PitchPractice.sampleRate,
                      let buffer = AVAudioPCMBuffer(pcmFormat: file.processingFormat, frameCapacity: AVAudioFrameCount(file.length)) else { throw CocoaError(.fileReadCorruptFile) }
                try file.read(into: buffer)
                guard let channel = buffer.floatChannelData?[0] else { throw CocoaError(.fileReadCorruptFile) }
                let samples = Array(UnsafeBufferPointer(start: channel, count: Int(buffer.frameLength)))
                cleanup(); message = "Measuring pitch..."
                let measurement = await Task.detached(priority: .userInitiated) { PitchPractice.analyze(samples, targetHz: targetHz) }.value
                guard !Task.isCancelled else { return }
                result = measurement
                message = measurement == nil ? "Not enough clear, steady voice to score. Try a quiet room, a comfortable pitch, and a gentle hum." : nil
            } catch {
                guard !Task.isCancelled else { return }
                cleanup(); message = "Could not measure this take. Check the microphone and try again."
            }
            busy = false; work = nil
        }
    }
}
