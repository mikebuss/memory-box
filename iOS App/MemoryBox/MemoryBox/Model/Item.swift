//
//  Item.swift
//  MemoryBox
//
//  Created by Mike Buss on 1/23/24.
//

import Foundation
import SwiftData

@Model
final class Item {
    var timestamp: Date
    
    init(timestamp: Date) {
        self.timestamp = timestamp
    }
}
