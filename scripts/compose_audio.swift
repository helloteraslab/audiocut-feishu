import AVFoundation
import Foundation

func parseRanges(_ raw: String) -> [(Double, Double)] {
    if raw.isEmpty { return [] }
    return raw.split(separator: ",").compactMap { part in
        let bits = part.split(separator: ":")
        guard bits.count == 2, let start = Double(bits[0]), let end = Double(bits[1]), end > start else {
            return nil
        }
        return (start, end)
    }
}

let args = CommandLine.arguments
guard args.count == 5 else {
    fputs("Usage: compose_audio.swift <input> <output> <intro_ranges> <delete_ranges>\n", stderr)
    exit(2)
}

let inputURL = URL(fileURLWithPath: args[1])
let outputURL = URL(fileURLWithPath: args[2])
let introRanges = parseRanges(args[3]).sorted { $0.0 < $1.0 }
let deleteRanges = parseRanges(args[4]).sorted { $0.0 < $1.0 }

let asset = AVURLAsset(url: inputURL)
guard let sourceTrack = asset.tracks(withMediaType: .audio).first else {
    fputs("No audio track found\n", stderr)
    exit(1)
}

let composition = AVMutableComposition()
guard let compositionTrack = composition.addMutableTrack(withMediaType: .audio, preferredTrackID: kCMPersistentTrackID_Invalid) else {
    fputs("Failed to create composition track\n", stderr)
    exit(1)
}

let scale: CMTimeScale = 600
var cursor = CMTime.zero

func insertRange(_ start: Double, _ end: Double) throws {
    let timeRange = CMTimeRange(
        start: CMTime(seconds: start, preferredTimescale: scale),
        end: CMTime(seconds: end, preferredTimescale: scale)
    )
    try compositionTrack.insertTimeRange(timeRange, of: sourceTrack, at: cursor)
    cursor = CMTimeAdd(cursor, timeRange.duration)
}

for (start, end) in introRanges {
    try insertRange(start, end)
}

let assetDuration = CMTimeGetSeconds(asset.duration)
var bodyStart = 0.0
for (delStart, delEnd) in deleteRanges {
    if delStart > bodyStart {
        try insertRange(bodyStart, delStart)
    }
    bodyStart = max(bodyStart, delEnd)
}
if bodyStart < assetDuration {
    try insertRange(bodyStart, assetDuration)
}

try? FileManager.default.removeItem(at: outputURL)
guard let exportSession = AVAssetExportSession(asset: composition, presetName: AVAssetExportPresetAppleM4A) else {
    fputs("Failed to create export session\n", stderr)
    exit(1)
}
exportSession.outputURL = outputURL
exportSession.outputFileType = .m4a

let semaphore = DispatchSemaphore(value: 0)
exportSession.exportAsynchronously {
    semaphore.signal()
}
semaphore.wait()

switch exportSession.status {
case .completed:
    print("OK")
case .failed, .cancelled:
    fputs("Export failed: \(exportSession.error?.localizedDescription ?? "unknown error")\n", stderr)
    exit(1)
default:
    fputs("Unexpected export status\n", stderr)
    exit(1)
}

