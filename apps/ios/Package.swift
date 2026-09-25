// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MusiaCore",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "MusiaCore", targets: ["MusiaCore"])],
    targets: [
        .target(name: "MusiaCore", path: "Musia/Core"),
        .testTarget(name: "MusiaCoreTests", dependencies: ["MusiaCore"], path: "Tests/MusiaCoreTests")
    ]
)
