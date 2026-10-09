// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "MusiaCore",
    platforms: [.iOS(.v17), .macOS(.v13)],
    products: [.library(name: "MusiaCore", targets: ["MusiaCore"])],
    targets: [
        .target(name: "MusiaCore", path: "Musia/Core"),
        .target(name: "MusiaCatalog", dependencies: ["MusiaCore"], path: "Musia/Services", sources: ["CatalogStore.swift"]),
        .testTarget(name: "MusiaCatalogTests", dependencies: ["MusiaCatalog", "MusiaCore"], path: "Tests/MusiaCatalogTests"),
        .testTarget(name: "MusiaCoreTests", dependencies: ["MusiaCore"], path: "Tests/MusiaCoreTests"),
        .target(name: "MusiaWatchProtocol", path: "WatchShared"),
        .testTarget(name: "WatchProtocolTests", dependencies: ["MusiaWatchProtocol"], path: "Tests/WatchProtocolTests")
    ]
)
