import React from 'react';

export default function Footer() {
  return (
    <footer className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-10">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="py-4 text-center text-sm text-gray-600">
          © {new Date().getFullYear()} All Rights Reserved by Chinmay Technosoft Pvt Ltd
        </div>
      </div>
    </footer>
  );
}
