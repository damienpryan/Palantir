document.addEventListener('DOMContentLoaded', () => {
    const chatDisplay = document.getElementById('chat-display');
    const userQueryInput = document.getElementById('user-query');
    const sendQueryButton = document.getElementById('send-query');
    const contextFileUpload = document.getElementById('context-file-upload');
    const uploadButton = document.getElementById('upload-button');
    const uploadStatus = document.getElementById('upload-status');
    const downloadLinksArea = document.getElementById('download-links');

    // Function to add a message to the chat display
    const addMessageToChat = (sender, message) => { 
        const messageElement = document.createElement('div');
        messageElement.classList.add('chat-message');
        messageElement.classList.add(sender === 'user' ? 'user-message' : 'ai-message');
        messageElement.innerHTML = `<strong>${sender === 'user' ? 'You' : 'AI'}:</strong> ${message}`;
        chatDisplay.appendChild(messageElement);
        chatDisplay.scrollTop = chatDisplay.scrollHeight; // Scroll to bottom
    }; 

    // Handle sending query
    sendQueryButton.addEventListener('click', async () => {
        const query = userQueryInput.value.trim();
        if (query === '') {
            return;
        }

        addMessageToChat('user', query);
        userQueryInput.value = ''; // Clear input

        try {
            // Replace with your actual Flask RAG endpoint
            const response = await fetch(`/app/chat/${encodeURIComponent(query)}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            addMessageToChat('ai', data.response || 'No specific response received.'); // Assuming Flask returns { "response": "..." }
        } catch (error) {
            console.error('Error fetching RAG response:', error);
            addMessageToChat('ai', 'Error: Could not get a response. Please try again.');
        }
    });

    // Allow sending query with Enter key (Shift + Enter for new line)
    userQueryInput.addEventListener('keypress', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault(); // Prevent new line
            sendQueryButton.click();
        }
    });

    // Handle file upload
    uploadButton.addEventListener('click', async () => {
        const file = contextFileUpload.files[0];
        if (!file) {
            uploadStatus.textContent = 'Please select a file to upload.';
            uploadStatus.style.color = 'orange';
            return;
        }

        uploadStatus.textContent = 'Uploading file...';
        uploadStatus.style.color = 'blue';

        const formData = new FormData();
        formData.append('file', file); // 'file' should match the name Flask expects

        try {
            // Replace with your actual Flask file upload endpoint
            const response = await fetch('/app/upload_context', {
                method: 'POST',
                body: formData,
            });

            if (response.ok) {
                const result = await response.json();
                uploadStatus.textContent = `Upload successful: ${result.message || file.name}`;
                uploadStatus.style.color = 'green';
                // Optionally, clear the file input after successful upload
                contextFileUpload.value = '';
                // Add a message to chat indicating file was used for context
                addMessageToChat('system', `File "${file.name}" uploaded for context.`);
            } else {
                const errorData = await response.json();
                throw new Error(`Upload failed: ${errorData.message || response.statusText}`);
            }
        } catch (error) {
            console.error('Error uploading file:', error);
            uploadStatus.textContent = `Upload failed: ${error.message}`;
            uploadStatus.style.color = 'red';
        }
    });

    // Placeholder for populating download links
    // In a real application, Flask would provide an API endpoint (e.g., /app/get_download_list)
    // that this frontend would call to get a list of available files to display.
    // For now, this is just a comment to indicate where that logic would go.
    function populateDownloadLinks(files) {
        downloadLinksArea.innerHTML = ''; // Clear previous links
        if (files && files.length > 0) {
            files.forEach(file => {
                const linkElement = document.createElement('p');
                // Assuming Flask provides a download URL like /app/download/filename.ext
                linkElement.innerHTML = `<a href="/app/download/${encodeURIComponent(file.filename)}" target="_blank">${file.display_name || file.filename}</a>`;
                downloadLinksArea.appendChild(linkElement);
            });
        } else {
            downloadLinksArea.innerHTML = '<p>No downloadable content available yet.</p>';
        }
    }

    // Example of how you might call populateDownloadLinks later (e.g., after a RAG response generates a file)
    // populateDownloadLinks([{ filename: 'generated_report.txt', display_name: 'Generated Report' }]);
});
