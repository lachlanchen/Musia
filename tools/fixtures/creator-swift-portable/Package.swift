// swift-tools-version: 5.9
import PackageDescription

// Mount the real Core and CoreTests read-only; no substitute implementations.
let package = Package(name: "MusiaCreatorPortableCheck", targets: [
    .target(name: "MusiaCore", path: "Sources/MusiaCore", exclude: ["APIClient.swift", "CreatorAPI.swift"]),
    .testTarget(name: "MusiaCoreTests", dependencies: ["MusiaCore"], path: "Tests/MusiaCoreTests",
                sources: ["CreatorConversationTests.swift"])
])
