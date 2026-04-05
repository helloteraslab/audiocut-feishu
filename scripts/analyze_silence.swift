import AVFoundation
import Foundation

let args = CommandLine.arguments
guard args.count >= 2 else {
    fputs("Usage: analyze_silence.swift <audio_path> [threshold] [min_silence]\n", stderr)
    exit(2)
}

let audioURL = URL(fileURLWithPath: args[1])
let threshold = Float(args.count >= 3 ? (Double(args[2]) ?? 0.008) : 0.008)
let minSilence = args.count >= 4 ? (Double(args[3]) ?? 1.0) : 1.0

let asset = AVURLAsset(url: audioURL)
guard let track = asset.tracks(withMediaType: .audio).first else {
    fputs("No audio track found\n", stderr)
    exit(1)
}

do {
    let reader = try AVAssetReader(asset: asset)
    let outputSettings: [String: Any] = [
        AVFormatIDKey: kAudioFormatLinearPCM,
        AVLinearPCMIsFloatKey: true,
        AVLinearPCMBitDepthKey: 32,
        AVLinearPCMIsBigEndianKey: false,
        AVLinearPCMIsNonInterleaved: false
    ]
    let output = AVAssetReaderTrackOutput(track: track, outputSettings: outputSettings)
    output.alwaysCopiesSampleData = false
    guard reader.canAdd(output) else {
        fputs("Cannot add reader output\n", stderr)
        exit(1)
    }
    reader.add(output)
    guard reader.startReading() else {
        fputs("Failed to start reading\n", stderr)
        exit(1)
    }

    let desc = track.formatDescriptions.first as! CMAudioFormatDescription
    let asbd = CMAudioFormatDescriptionGetStreamBasicDescription(desc)!.pointee
    let sampleRate = Double(asbd.mSampleRate)
    let channels = Int(asbd.mChannelsPerFrame)

    var currentTime = 0.0
    var silenceStart: Double? = nil
    var intervals: [(Double, Double)] = []

    while reader.status == .reading {
        guard let sampleBuffer = output.copyNextSampleBuffer() else { break }
        guard let blockBuffer = CMSampleBufferGetDataBuffer(sampleBuffer) else {
            CMSampleBufferInvalidate(sampleBuffer)
            continue
        }
        let numSamples = CMSampleBufferGetNumSamples(sampleBuffer)
        let byteLength = CMBlockBufferGetDataLength(blockBuffer)
        var data = Data(count: byteLength)
        data.withUnsafeMutableBytes { rawBuf in
            if let base = rawBuf.baseAddress {
                CMBlockBufferCopyDataBytes(blockBuffer, atOffset: 0, dataLength: byteLength, destination: base)
            }
        }

        var maxAmp: Float = 0
        data.withUnsafeBytes { rawBuf in
            let ptr = rawBuf.bindMemory(to: Float.self)
            let sampleCount = min(ptr.count, numSamples * channels)
            for i in 0..<sampleCount {
                let amp = abs(ptr[i])
                if amp > maxAmp { maxAmp = amp }
            }
        }

        let duration = Double(numSamples) / sampleRate
        let isSilent = maxAmp < threshold
        if isSilent {
            if silenceStart == nil { silenceStart = currentTime }
        } else if let start = silenceStart {
            let end = currentTime
            if end - start >= minSilence { intervals.append((start, end)) }
            silenceStart = nil
        }

        currentTime += duration
        CMSampleBufferInvalidate(sampleBuffer)
    }

    if let start = silenceStart, currentTime - start >= minSilence {
        intervals.append((start, currentTime))
    }

    if reader.status == .failed {
        fputs("Reader failed: \(reader.error?.localizedDescription ?? "unknown")\n", stderr)
        exit(1)
    }

    for (start, end) in intervals {
        print(String(format: "%.3f\t%.3f\t%.3f", start, end, end - start))
    }
} catch {
    fputs("Error: \(error.localizedDescription)\n", stderr)
    exit(1)
}
