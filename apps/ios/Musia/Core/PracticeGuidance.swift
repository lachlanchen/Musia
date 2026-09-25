import Foundation

public enum PracticeGuidance {
    public static func text(songID: String, mode: PracticeMode) -> String {
        if songID == FirstPulse.id {
            switch mode {
            case .listen: return "Four count-in clicks at 60 BPM. Em enters at 4 seconds, Am at 8, Em at 12, and Am at 16."
            case .tap: return "Listen to the count-in. Tap from 4 through 19 seconds, then let the final chord fade."
            case .play: return "Prepare Em during the count-in. Strum Em at 4 seconds, Am at 8, Em at 12, and Am at 16."
            }
        }
        switch mode {
        case .listen: return "Listen for the pulse and a change in harmony. Analyzed timing may be imperfect."
        case .tap: return "Follow the audible pulse. Tap offsets use reference beats, which may be imperfect."
        case .play: return "Practice one comfortable phrase. Treat analyzed chords as suggestions and check them by ear."
        }
    }

    public static func phase(songID: String, time: Double, playing: Bool, hasBeats: Bool) -> String {
        guard playing else { return "Ready" }
        guard songID == FirstPulse.id else {
            return hasBeats ? "Reference pulses - downbeat unverified" : "Beat reference unavailable"
        }
        if time < 4 { return "Count-in" }
        if time < 20 { return "Bar \(min(4, Int((time - 4) / 4) + 1)) of 4" }
        return "Final chord fade"
    }
}
