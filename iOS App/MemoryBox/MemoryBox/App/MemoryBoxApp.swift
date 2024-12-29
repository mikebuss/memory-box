//
//  MemoryBoxApp.swift
//  MemoryBox
//
//  Created by Mike Buss on 1/23/24.
//

import SwiftUI
import SwiftData
import Photos

@main
struct MemoryBoxApp: App {
    var sharedModelContainer: ModelContainer = {
        let schema = Schema([
            Item.self,
        ])
        let modelConfiguration = ModelConfiguration(schema: schema, isStoredInMemoryOnly: false)

        do {
            return try ModelContainer(for: schema, configurations: [modelConfiguration])
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()
    
    var body: some Scene {
        WindowGroup {
            DashboardView()
                .onAppear {
                    PHPhotoLibrary.requestAuthorization { status in
                        switch status {
                        case .authorized:
                            // Access has been granted.
                            break
                        case .denied, .restricted:
                            // Access has been denied or restricted.
                            break
                        case .notDetermined:
                            // Access hasn't been requested yet.
                            break
                        case .limited:
                            // The user granted limited access. (iOS 14 and later)
                            break
                        @unknown default:
                            // Handle any new future cases.
                            break
                        }
                    }
                }
        }
        .modelContainer(sharedModelContainer)
    }
}
