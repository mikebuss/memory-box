//
//  MemoryMetadata.swift
//  MemoryBox
//
//  Created by Mike Buss on 2/2/24.
//

import Foundation

struct MemoryMetadata: Codable {
    var updateDisplayImmediately: Bool
    var media: Media

    enum CodingKeys: String, CodingKey {
        case updateDisplayImmediately = "update_display_immediately"
        case media
    }
}

struct Media: Codable {
    var date: String
    var description: String
    var url: String = ""
    var people: Set<String>
}
