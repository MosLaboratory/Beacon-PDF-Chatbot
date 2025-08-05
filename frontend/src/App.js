import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import PDFUpload from './components/PDFUpload';
import ChatInterface from './components/ChatInterface';
import ErrorToast from './components/ErrorToast';
import { apiService } from './services/api';

function App() {
  const [pdfLoaded, setPdfLoaded] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [error, setError] = useState('');
  const [showError, setShowError] = useState(false);

  useEffect(() => {
    // Check if there's already a PDF loaded
    checkPDFStatus();
  }, []);

  const checkPDFStatus = async () => {
    try {
      console.log('Checking PDF status...');
      const pdfInfo = await apiService.getPDFInfo();
      console.log('PDF info received:', pdfInfo);
      setPdfLoaded(pdfInfo.has_content || false);
    } catch (error) {
      console.error('Error checking PDF status:', error);
    }
  };

  const handleUpload = async (file) => {
    setIsUploading(true);
    setError('');
    
    try {
      console.log('Uploading PDF:', file.name);
      const response = await apiService.uploadPDF(file);
      console.log('PDF uploaded successfully:', response);
      setPdfLoaded(true);
      
      // Double-check the PDF status after upload
      setTimeout(() => {
        checkPDFStatus();
      }, 1000);
      
    } catch (error) {
      console.error('Upload error:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to upload PDF';
      setError(errorMessage);
      setShowError(true);
    } finally {
      setIsUploading(false);
    }
  };

  const handleUploadError = (message) => {
    setError(message);
    setShowError(true);
  };

  const handleChatError = (message) => {
    setError(message);
    setShowError(true);
  };

  const closeError = () => {
    setShowError(false);
    setError('');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left Column - PDF Upload */}
          <div className="space-y-6">
            <div className="card">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Upload PDF Document
              </h2>
              <PDFUpload
                onUpload={handleUpload}
                onError={handleUploadError}
                isLoading={isUploading}
              />
            </div>
            
            {pdfLoaded && (
              <div className="card">
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  PDF Information
                </h3>
                <div className="space-y-2 text-sm text-gray-600">
                  <p>✅ PDF successfully loaded and processed</p>
                  <p>🤖 Ready to chat with AI assistant</p>
                </div>
              </div>
            )}
          </div>
          
          {/* Right Column - Chat Interface */}
          <div className="card h-96 lg:h-[600px]">
            <ChatInterface
              pdfLoaded={pdfLoaded}
              onError={handleChatError}
            />
          </div>
        </div>
      </main>
      
      <ErrorToast
        message={error}
        onClose={closeError}
        isVisible={showError}
      />
    </div>
  );
}

export default App; 