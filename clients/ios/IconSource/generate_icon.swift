import AppKit
import CoreGraphics
import Foundation

// Nightwell Studio dark monogram, drawn in true resolution for iOS app icons.
// This is an opaque full-bleed icon, not an image that depends on external media.
guard CommandLine.arguments.count >= 2 else {
    fatalError("Expected PNG output path")
}
let width = 1024
let height = 1024
guard let bitmap = NSBitmapImageRep(
    bitmapDataPlanes: nil, pixelsWide: width, pixelsHigh: height,
    bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
    isPlanar: false, colorSpaceName: .deviceRGB,
    bytesPerRow: 0, bitsPerPixel: 0
), let drawing = NSGraphicsContext(bitmapImageRep: bitmap) else {
    fatalError("Cannot create icon bitmap")
}
let context = drawing.cgContext
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = drawing
defer { NSGraphicsContext.restoreGraphicsState() }

func color(_ r: CGFloat, _ g: CGFloat, _ b: CGFloat, _ a: CGFloat = 1) -> CGColor {
    CGColor(colorSpace: CGColorSpaceCreateDeviceRGB(), components: [r, g, b, a])!
}
func polygon(_ points: [CGPoint]) -> CGPath {
    let path = CGMutablePath()
    guard let first = points.first else { return path }
    path.move(to: first)
    for point in points.dropFirst() { path.addLine(to: point) }
    path.closeSubpath()
    return path
}
func drawFacet(_ points: [CGPoint], top: CGColor, bottom: CGColor) {
    let path = polygon(points)
    context.saveGState()
    context.setShadow(offset: CGSize(width: 1, height: -9), blur: 22,
                      color: color(0.83, 0.90, 1.0, 0.22))
    context.addPath(path)
    context.setFillColor(bottom)
    context.fillPath()
    context.restoreGState()
    context.saveGState()
    context.addPath(path)
    context.clip()
    if let gradient = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(),
                                 colors: [bottom, top] as CFArray, locations: [0, 1]) {
        context.drawLinearGradient(gradient,
            start: CGPoint(x: 260, y: 198), end: CGPoint(x: 730, y: 855),
            options: [])
    }
    context.restoreGState()
}
context.setFillColor(color(0.018, 0.022, 0.030))
context.fill(CGRect(x: 0, y: 0, width: 1024, height: 1024))
// Dark, smoky background.
if let ambient = CGGradient(colorsSpace: CGColorSpaceCreateDeviceRGB(),
                             colors: [color(0.18, 0.22, 0.29, 0.18),
                                      color(0.01, 0.012, 0.016, 0)] as CFArray,
                             locations: [0, 1]) {
    context.drawRadialGradient(ambient,
        startCenter: CGPoint(x: 510, y: 540), startRadius: 90,
        endCenter: CGPoint(x: 510, y: 540), endRadius: 620, options: [])
}
// Fine arcs near the corners, never competing with the monogram.
for (offset, alpha) in [(0.0, 0.23), (28.0, 0.10), (63.0, 0.055)] {
    context.beginPath()
    context.move(to: CGPoint(x: 0, y: 780 - offset))
    context.addCurve(to: CGPoint(x: 380, y: 1024),
                     control1: CGPoint(x: 210, y: 860 - offset),
                     control2: CGPoint(x: 235, y: 995))
    context.setStrokeColor(color(0.73, 0.81, 0.95, alpha))
    context.setLineWidth(2)
    context.strokePath()

    context.beginPath()
    context.move(to: CGPoint(x: 650, y: 0))
    context.addCurve(to: CGPoint(x: 1024, y: 290 + offset),
                     control1: CGPoint(x: 880, y: 63),
                     control2: CGPoint(x: 930, y: 200 + offset))
    context.setStrokeColor(color(0.72, 0.82, 0.98, alpha))
    context.setLineWidth(2)
    context.strokePath()
}
// Dim bevels behind the main N.
drawFacet([
    CGPoint(x: 262, y: 220), CGPoint(x: 262, y: 794),
    CGPoint(x: 393, y: 679), CGPoint(x: 393, y: 342)
], top: color(0.93, 0.95, 0.98), bottom: color(0.34, 0.39, 0.48))
drawFacet([
    CGPoint(x: 636, y: 667), CGPoint(x: 761, y: 797),
    CGPoint(x: 761, y: 222), CGPoint(x: 636, y: 349)
], top: color(0.91, 0.95, 0.99), bottom: color(0.31, 0.37, 0.46))
// Broad silver diagonal face, light reflecting from upper-left to lower-right.
drawFacet([
    CGPoint(x: 262, y: 794), CGPoint(x: 390, y: 794),
    CGPoint(x: 761, y: 266), CGPoint(x: 761, y: 122)
], top: color(0.97, 0.98, 1.00), bottom: color(0.45, 0.51, 0.61))
// Narrow edge highlight along the diagonal.
context.beginPath()
context.move(to: CGPoint(x: 267, y: 787))
context.addLine(to: CGPoint(x: 759, y: 136))
context.setStrokeColor(color(1, 1, 1, 0.40))
context.setLineWidth(2)
context.strokePath()

context.flush()
guard let png = bitmap.representation(using: .png, properties: [:]) else {
    fatalError("Cannot encode icon PNG")
}
try png.write(to: URL(fileURLWithPath: CommandLine.arguments[1]))
print("Nightwell Studio AppIcon: \(width)x\(height), \(png.count) bytes")
