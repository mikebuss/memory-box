//
//  PersonSelectionView.swift
//  MemoryBox
//
//  Created by Mike Buss on 1/29/24.
//

import SwiftUI

struct PersonSelectionView: View {
    // Add people you can tag in a photo
    var people: [String] = [
        "Person A",
        "Person B"
    ]

    private let imageSize: CGFloat = 50
    @Binding var selectedPeople: Set<String>
    
    let columns: [GridItem] = Array(repeating: .init(.flexible()), count: 4)

    var body: some View {
        LazyVGrid(columns: columns, alignment: .center, spacing: 20) {
            ForEach(people, id: \.self) { person in
                VStack {
                    Image(person)
                        .resizable()
                        .frame(width: imageSize, height: imageSize)
                        .opacity(selectedPeople.contains(person) ? 1.0 : 0.4)
                        .onTapGesture {
                            if selectedPeople.contains(person) {
                                selectedPeople.remove(person)
                            } else {
                                selectedPeople.insert(person)
                            }
                        }
                    Text(person.components(separatedBy: " ").first ?? "")
                        .foregroundStyle(.black)
                        .opacity(selectedPeople.contains(person) ? 1.0 : 0.4)
                }
            }
        }
    }

    // Function to get selected people for the consumer
    func getSelectedPeople() -> [String] {
        return Array(selectedPeople)
    }
}

// Preview
struct PersonSelectionView_Previews: PreviewProvider {
    static var previews: some View {
        PersonSelectionView(selectedPeople: .constant(Set(["Person 1"])))
    }
}
