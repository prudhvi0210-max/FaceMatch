import AppKit
let folder = URL(fileURLWithPath: CommandLine.arguments[1])
try FileManager.default.createDirectory(at: folder, withIntermediateDirectories: true)
for size in [16,32,64,128,256,512,1024] {
    let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size, bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: bitmap)
    let scale = CGFloat(size) / 1024
    let transform = NSAffineTransform(); transform.scale(by: scale); transform.concat()
    let background = NSBezierPath(roundedRect: NSRect(x: 55,y:55,width:914,height:914), xRadius:210,yRadius:210)
    NSColor(calibratedRed:0.13,green:0.37,blue:0.28,alpha:1).setFill(); background.fill()
    NSColor(calibratedRed:0.93,green:0.97,blue:0.87,alpha:1).setStroke()
    let corners = NSBezierPath(); corners.lineWidth=29; corners.lineCapStyle = .round; corners.lineJoinStyle = .round
    for (x,y,sx,sy) in [(CGFloat(250),CGFloat(250),CGFloat(1),CGFloat(1)),(774,250,-1,1),(250,774,1,-1),(774,774,-1,-1)] {
        corners.move(to:NSPoint(x:x,y:y+sy*100)); corners.line(to:NSPoint(x:x,y:y)); corners.line(to:NSPoint(x:x+sx*100,y:y))
    }
    corners.stroke()
    let head = NSBezierPath(ovalIn:NSRect(x:419,y:452,width:186,height:227)); head.lineWidth=23; head.stroke()
    let shoulders=NSBezierPath(); shoulders.move(to:NSPoint(x:341,y:332)); shoulders.curve(to:NSPoint(x:683,y:332),controlPoint1:NSPoint(x:365,y:478),controlPoint2:NSPoint(x:659,y:478)); shoulders.lineWidth=23; shoulders.lineCapStyle = .round; shoulders.stroke()
    NSGraphicsContext.restoreGraphicsState()
    let png=bitmap.representation(using:.png,properties:[:])!
    let name = size==1024 ? "icon_512x512@2x.png" : "icon_\(size)x\(size).png"
    if size != 64 { try png.write(to:folder.appendingPathComponent(name)) }
    if [32,64,256,512].contains(size) { try png.write(to:folder.appendingPathComponent("icon_\(size/2)x\(size/2)@2x.png")) }
}
