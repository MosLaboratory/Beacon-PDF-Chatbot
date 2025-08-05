import React from 'react';
import { Bot, Github } from 'lucide-react';

const Header = () => {
  return (
    <header className="bg-white border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-3">
            <div className="flex-shrink-0">
              <Bot className="w-8 h-8 text-primary-600" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">PDF Chatbot</h1>
              <p className="text-sm text-gray-500">AI-powered PDF document assistant</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-4">
            <a
              href="https://github.com/yourusername/pdf-chatbot"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center space-x-2 text-gray-500 hover:text-gray-700 transition-colors"
            >
              <Github className="w-5 h-5" />
              <span className="text-sm">GitHub</span>
            </a>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header; 