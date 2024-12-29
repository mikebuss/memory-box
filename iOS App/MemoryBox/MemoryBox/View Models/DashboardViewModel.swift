import Foundation
import SwiftUI
import PhotosUI

@MainActor final class DashboardViewModel: ObservableObject {
    
    @Published var error: Error?
    @Published var isUploading: Bool = false
    
    // A class that manages an image that a person selects in the Photos picker.
    @MainActor final class ImageAttachment: ObservableObject, Identifiable {
        
        // Statuses that indicate the app's progress in loading a selected photo.
        enum Status {
        
            // A status indicating that the app has requested a photo.
            case loading
            
            // A status indicating that the app has loaded a photo.
            case finished(Image, Data, UIImage)
            
            // A status indicating that the photo has failed to load.
            case failed(Error)
            
            // Determines whether the photo has failed to load.
            var isFailed: Bool {
                return switch self {
                case .failed: true
                default: false
                }
            }
        }
        
        // An error that indicates why a photo has failed to load.
        enum LoadingError: Error {
            case contentTypeNotSupported
        }
        
        // A reference to a selected photo in the picker.
        let pickerItem: PhotosPickerItem
        
        // A load progress for the photo.
        @Published var imageStatus: Status?
        
        // A textual description for the photo.
        @Published var imageDescription: String = ""
        
        @Published var uploaded: Bool = false
        
        // An identifier for the photo.
        nonisolated var id: String {
            pickerItem.identifier
        }
        
        // Creates an image attachment for the given picker item.
        init(_ pickerItem: PhotosPickerItem) {
            self.pickerItem = pickerItem
        }
        
        // Loads the photo that the picker item features.
        func loadImage() async {
            guard imageStatus == nil || imageStatus?.isFailed == true else {
                return
            }
            imageStatus = .loading
            do {
                
#if os(iOS)
                if let data = try await pickerItem.loadTransferable(type: Data.self),
                   let uiImage = UIImage(data: data) {
                    imageStatus = .finished(Image(uiImage: uiImage), data, uiImage)
                } else {
                    throw LoadingError.contentTypeNotSupported
                }
#endif
            } catch {
                imageStatus = .failed(error)
            }
        }
    }
    
    // A dictionary mapping image identifiers to selected people
    @Published var selectedPeopleForImage: [String: Set<String>] = [:]

    
    // An array of items for the picker's selected photos.
    //
    // On set, this method updates the image attachments for the current selection.
    @Published var selection = [PhotosPickerItem]() {
        didSet {
            // Update the attachments according to the current picker selection.
            let newAttachments = selection.map { item in
                // Access an existing attachment, if it exists; otherwise, create a new attachment.
                attachmentByIdentifier[item.identifier] ?? ImageAttachment(item)
            }
            // Update the saved attachments array for any new attachments loaded in scope.
            let newAttachmentByIdentifier = newAttachments.reduce(into: [:]) { partialResult, attachment in
                partialResult[attachment.id] = attachment
            }
            // To support asynchronous access, assign new arrays to the instance properties rather than updating the existing arrays.
            attachments = newAttachments
            attachmentByIdentifier = newAttachmentByIdentifier
        }
    }
    
    // An array of image attachments for the picker's selected photos.
    @Published var attachments = [ImageAttachment]()
    
    // A dictionary that stores previously loaded attachments for performance.
    private var attachmentByIdentifier = [String: ImageAttachment]()
}

// A extension that handles the situation in which a picker item lacks a photo library.
private extension PhotosPickerItem {
    var identifier: String {
        guard let identifier = itemIdentifier else {
            fatalError("The photos picker lacks a photo library.")
        }
        return identifier
    }
}

extension DashboardViewModel {
    func uploadImages() async {
        isUploading = true
        
        do {
            for attachment in attachments.filter( {$0.uploaded == false} ) {
                let people = selectedPeopleForImage[attachment.id] ?? []
                let dateTaken = try await attachment.loadImageMetadata() ?? "2020-10-08"
                let media = Media(date: dateTaken, description: attachment.imageDescription, people: people)
                let memoryMetadata = MemoryMetadata(updateDisplayImmediately: true, media: media)
                try await upload(attachment: attachment, metadata: memoryMetadata)
                attachment.uploaded = true
            }
        } catch {
            self.error = error
        }
        
        isUploading = false
    }

    
    func upload(attachment: ImageAttachment, metadata: MemoryMetadata) async throws {
        switch attachment.imageStatus {
        case .finished(_, _, let uiImage):
            print("Uploading image")
            
            guard let resizedImage = uiImage.resized(toWidth: 800),
                  let resizedImageData = resizedImage.jpegData(compressionQuality: 1.0) else {
                throw UploadError.unableToResizeImage
            }
            
            guard let url = URL(string: "http://192.168.1.8:2358/media-direct-upload") else { return }
            var request = URLRequest(url: url)
            request.httpMethod = "POST"
            
            let boundary = "Boundary-\(UUID().uuidString)"
            request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
            
            var body = Data()
            
            // Add the metadata part as JSON
            let metadataJSONData = try JSONEncoder().encode(metadata)
            let metadataJSONString = String(data: metadataJSONData, encoding: .utf8)!
            
            body.append("--\(boundary)\r\n")
            body.append("Content-Disposition: form-data; name=\"metadata\"\r\n")
            body.append("Content-Type: application/json\r\n\r\n")
            body.append(metadataJSONString)
            body.append("\r\n")
            
            // Add the file part
            let filename = "image.jpg"
            let mimeType = "image/jpeg"
            body.append("--\(boundary)\r\n")
            body.append("Content-Disposition: form-data; name=\"file\"; filename=\"\(filename)\"\r\n")
            body.append("Content-Type: \(mimeType)\r\n\r\n")
            body.append(resizedImageData)
            body.append("\r\n")
            
            // End of the body
            body.append("--\(boundary)--\r\n")
                        
            // Execute the request
            let (responseData, _) = try await URLSession.shared.upload(for: request, from: body)
            
            // Handle response data if needed
            if let responseString = String(data: responseData, encoding: .utf8) {
                print("Response: \(responseString)")
            }
            
        default:
            throw UploadError.imageNotProcessed
        }
    }
}

enum UploadError: Error {
    case imageNotProcessed
    case unableToResizeImage
    
    var errorDescription: String? {
        switch self {
        case .imageNotProcessed:
            return NSLocalizedString("The image could not be processed from the Photos app.", comment: "")
        case .unableToResizeImage:
            return NSLocalizedString("The image could not be resized.", comment: "")
        }
    }
}

extension Data {
    mutating func append(_ string: String) {
        if let data = string.data(using: .utf8) {
            append(data)
        }
    }
}

extension DashboardViewModel.ImageAttachment {
    func loadImageMetadata() async throws -> String? {
        guard case .finished(_, _, _) = self.imageStatus else {
            return nil
        }
        guard let identifier = pickerItem.itemIdentifier else {
            return nil
        }
        
        let identifiers = [identifier]
        let assets = PHAsset.fetchAssets(withLocalIdentifiers: identifiers, options: nil)
        guard let asset = assets.firstObject else {
            return nil
        }
        
        let dateFormatter = DateFormatter()
        dateFormatter.dateFormat = "yyyy-MM-dd"
        
        return asset.creationDate.map { dateFormatter.string(from: $0) }
    }
}


extension UIImage {
    func resized(toWidth width: CGFloat) -> UIImage? {
        // Calculate the aspect ratio of the current image
        let aspectRatio = 800.0 / 480.0
        
        // Determine target height to maintain aspect ratio
        var targetHeight = width / aspectRatio
        
        // Check if calculated height makes the image portrait, switch dimensions to maintain landscape
        if targetHeight > width {
            // If the target height is greater than the target width, it means the image is portrait.
            // Swap the values to ensure the result is landscape.
            let temp = width
            targetHeight = temp
        }
        
        let canvasSize = CGSize(width: width, height: targetHeight)
        
        UIGraphicsBeginImageContextWithOptions(canvasSize, false, scale)
        defer { UIGraphicsEndImageContext() }
        
        // Draw the image in the center of the canvas to maintain aspect ratio
        let rect = CGRect(x: 0, y: 0, width: width, height: targetHeight)
        draw(in: rect)
        return UIGraphicsGetImageFromCurrentImageContext()
    }
}
