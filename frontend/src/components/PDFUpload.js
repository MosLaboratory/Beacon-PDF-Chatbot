import React, { useState, useRef } from 'react';
import { Upload, FileText, X, CheckCircle } from 'lucide-react';
import { cn } from '../utils/cn';

const PDFUpload = ({ onUpload, onError, isLoading = false }) => {
  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelect(files[0]);
    }
  };

  const handleFileSelect = (file) => {
    if (file.type !== 'application/pdf') {
      onError('Please select a valid PDF file');
      return;
    }

    if (file.size > 10 * 1024 * 1024) { // 10MB limit
      onError('File size must be less than 10MB');
      return;
    }

    setSelectedFile(file);
  };

  const handleFileInputChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;
    
    try {
      await onUpload(selectedFile);
      setSelectedFile(null);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Upload error:', error);
    }
  };

  const removeFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        className={cn(
          "border-2 border-dashed rounded-lg p-8 text-center transition-colors duration-200",
          isDragOver
            ? "border-primary-400 bg-primary-50"
            : "border-gray-300 hover:border-gray-400",
          selectedFile && "border-green-400 bg-green-50"
        )}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        {selectedFile ? (
          <div className="space-y-4">
            <div className="flex items-center justify-center space-x-2">
              <CheckCircle className="w-8 h-8 text-green-500" />
              <span className="text-lg font-medium text-green-700">
                PDF Selected
              </span>
            </div>
            <div className="flex items-center justify-center space-x-2">
              <FileText className="w-5 h-5 text-gray-500" />
              <span className="text-sm text-gray-600">{selectedFile.name}</span>
              <button
                onClick={removeFile}
                className="p-1 hover:bg-gray-200 rounded-full transition-colors"
              >
                <X className="w-4 h-4 text-gray-500" />
              </button>
            </div>
            <div className="text-xs text-gray-500">
              {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
            </div>
            <button
              onClick={handleUpload}
              disabled={isLoading}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="flex items-center space-x-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Uploading...</span>
                </div>
              ) : (
                'Upload PDF'
              )}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <Upload className="w-12 h-12 mx-auto text-gray-400" />
            <div>
              <p className="text-lg font-medium text-gray-900">
                Upload your PDF document
              </p>
              <p className="text-sm text-gray-500 mt-1">
                Drag and drop your PDF here, or click to browse
              </p>
            </div>
            <button
              onClick={() => fileInputRef.current?.click()}
              className="btn-secondary"
            >
              Choose File
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf"
              onChange={handleFileInputChange}
              className="hidden"
            />
            <p className="text-xs text-gray-400">
              Maximum file size: 10MB
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default PDFUpload; 