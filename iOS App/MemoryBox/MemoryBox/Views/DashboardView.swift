//
//  DashboardView.swift
//  MemoryBox
//
//  Created by Mike Buss on 1/28/24.
//

import SwiftUI
import PhotosUI

struct DashboardView: View {
    @StateObject private var viewModel = DashboardViewModel()
    
    var body: some View {
        NavigationStack {
            VStack {
                ImageList(viewModel: viewModel)
                
                PhotosPicker(
                    selection: $viewModel.selection,
                    selectionBehavior: .continuousAndOrdered,
                    matching: .images,
                    preferredItemEncoding: .current,
                    photoLibrary: .shared()
                ) {
                    Text("Select Photos")
                }
                .photosPickerStyle(.inline)
                .photosPickerDisabledCapabilities(.selectionActions)
                .photosPickerAccessoryVisibility(.hidden, edges: .all)
                .ignoresSafeArea()
                .frame(height: 400)
            }
            .toolbar(content: {
                ToolbarItem(id: "Upload") {
                    Button(action: {
                        Task {
                            await viewModel.uploadImages()
                        }
                    }, label: {
                        Text("Upload")
                    })
                    .disabled(viewModel.isUploading)
                }
            })
            .navigationTitle("MemoryBox")
            .ignoresSafeArea(.keyboard)
        }
    }
}

struct ImageList: View {
    @ObservedObject var viewModel: DashboardViewModel
    
    var body: some View {
        if viewModel.attachments.isEmpty {
            Spacer()
            Image(systemName: "text.below.photo").font(.system(size: 150)).opacity(0.2)
            Spacer()
        } else {
            List(viewModel.attachments) { imageAttachment in
                ImageAttachmentView(imageAttachment: imageAttachment, viewModel: viewModel)
            }.listStyle(.plain)
        }
    }
}

extension Binding where Value == [String: Set<String>] {
    /// A subscript method that provides a binding to a set for a given key.
    /// If the key is not present in the dictionary, it uses an empty set.
    func bindingForKey(_ key: String) -> Binding<Set<String>> {
        .init(
            get: { self.wrappedValue[key] ?? Set() },
            set: { self.wrappedValue[key] = $0 }
        )
    }
}


struct ImageAttachmentView: View {
    @ObservedObject var imageAttachment: DashboardViewModel.ImageAttachment
    @ObservedObject var viewModel: DashboardViewModel
    
    var body: some View {
        VStack {
            HStack {
                if imageAttachment.uploaded == false {
                    TextField("Memory Description", text: $imageAttachment.imageDescription)
                } else {
                    Text("Uploaded!")
                        .padding()
                }
                
                Spacer()
                switch imageAttachment.imageStatus {
                case .finished(let image, _, _):
                    image.resizable().aspectRatio(contentMode: .fit).frame(height: 100)
                case .failed:
                    Image(systemName: "exclamationmark.triangle.fill")
                default:
                    ProgressView()
                }
            }
            
            if imageAttachment.uploaded == false {
                PersonSelectionView(selectedPeople: $viewModel.selectedPeopleForImage.bindingForKey(imageAttachment.id))
                    .padding(.top, 20)
            }
            
        }.task {
            await imageAttachment.loadImage()
        }
    }
}
