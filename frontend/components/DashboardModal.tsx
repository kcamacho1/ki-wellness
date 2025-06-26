'use client'; // Enable client-side rendering for this Next.js page

import React from 'react';
import FoodJournalForm from './FoodJournalForm'; // Assuming FoodJournalForm is in the same 'components' directory
import { User } from '@supabase/supabase-js'; // Import User type for prop type checking

/**
 * Interface for the props of the DashboardModal component.
 * @property {boolean} isOpen - Controls the visibility of the modal.
 * @property {() => void} onClose - Function to call when the modal needs to be closed.
 * @property {User | null} user - The currently logged-in user object from Supabase.
 * @property {() => void} onEntrySaved - Function to call after a new food entry is successfully saved.
 */
interface DashboardModalProps {
  isOpen: boolean;
  onClose: () => void;
  user: User | null;
  onEntrySaved: () => void;
}

/**
 * DashboardModal Component
 * This modal provides options for food entry, future data management, and table filtering.
 * It appears as an overlay when 'isOpen' is true.
 */
const DashboardModal: React.FC<DashboardModalProps> = ({ isOpen, onClose, user, onEntrySaved }) => {
  // If the modal is not open, return null to render nothing.
  if (!isOpen) return null;

  return (
    // Modal Overlay: Fixed position, semi-transparent background, centers content.
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50 p-4">
      {/* Modal Content Area: Background, padding, rounded corners, shadow, scrollable. */}
      <div className="bg-[aliceblue] p-8 rounded-xl shadow-lg relative w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        {/* Close Button: Absolute positioned, styled with Tailwind classes for appearance and hover effect. */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-700 hover:text-gray-900 text-2xl font-bold"
          aria-label="Close modal" // Accessibility improvement
        >
          &times; {/* HTML entity for a multiplication sign, commonly used as a close icon */}
        </button>

        {/* Modal Title */}
        <h2 className="text-2xl font-bold text-green-800 papyrus mb-6">Food Journal Options</h2>
        <p className="text-center text-green-900"><i>Automatically processed through OpenFood and Nutritionix API for Protein, Carbs, Fat and Calories</i></p>
        <br></br>

        {/* Section: Add New Food Entry */}
        <section className="mb-8 p-4 bg-green-700 rounded-lg shadow-inner">
          <h3 className="text-xl font-semibold text-green-50 mb-4">+ Manual Food Entry</h3>
          {/* FoodJournalForm component is integrated here.
              It receives the 'user' prop and a callback for when an entry is saved. */}
          <FoodJournalForm user={user} onEntrySaved={onEntrySaved} />
        </section>

        {/* Section: Data Management (Future Feature Placeholder) */}
        <section className="mb-8 p-4 bg-blue-50 rounded-lg shadow-inner">
          <h3 className="text-xl font-semibold text-green-800 mb-4">📥 Data Management (Future)</h3>
          <div className="space-y-4">
            {/* Placeholder buttons for download/upload functionality */}
            <button
              className="w-full bg-blue-500 text-white py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors opacity-75 cursor-not-allowed"
              disabled // Disable button as it's a future feature
            >
              Download All Data (CSV)
            </button>
            <button
              className="w-full bg-blue-500 text-amber-50 py-2 px-4 rounded-lg hover:bg-blue-600 transition-colors opacity-75 cursor-not-allowed"
              disabled // Disable button as it's a future feature
            >
              Upload Data (CSV)
            </button>
            <p className="text-sm text-gray-600 mt-2 text-center">
              * This functionality will be available in a future update.
            </p>
          </div>
        </section>

      </div>
    </div>
  );
};

export default DashboardModal;