import React, { useState, useEffect } from 'react';
import { X, Menu } from 'lucide-react';
import { Link } from 'react-router-dom';

const MobileMenu = ({ links, isAuthenticated, onDashboardClick, onLoginClick, onRegisterClick }) => {
  const [isOpen, setIsOpen] = useState(false);

  // Close menu on route change
  useEffect(() => {
    setIsOpen(false);
  }, []);

  // Prevent body scroll when menu is open
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };

  const closeMenu = () => {
    setIsOpen(false);
  };

  return (
    <>
      {/* Mobile Menu Button */}
      <button
        onClick={toggleMenu}
        className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
        aria-label="Toggle mobile menu"
        aria-expanded={isOpen}
      >
        <Menu className="h-6 w-6 text-gray-700" />
      </button>

      {/* Mobile Menu Overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
          onClick={closeMenu}
          aria-hidden="true"
        />
      )}

      {/* Mobile Menu Drawer */}
      <div
        className={`fixed top-0 right-0 h-full w-64 bg-white shadow-2xl z-50 transform transition-transform duration-300 ease-in-out md:hidden ${
          isOpen ? 'translate-x-0' : 'translate-x-full'
        }`}
        role="navigation"
        aria-label="Mobile navigation"
      >
        {/* Close Button */}
        <div className="flex justify-end p-4 border-b border-gray-200">
          <button
            onClick={closeMenu}
            className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
            aria-label="Close mobile menu"
          >
            <X className="h-6 w-6 text-gray-700" />
          </button>
        </div>

        {/* Menu Items */}
        <nav className="flex flex-col p-6 space-y-4">
          {links.map((link) => (
            <Link
              key={link.to}
              to={link.to}
              onClick={closeMenu}
              className="text-lg text-gray-700 hover:text-blue-600 transition-colors py-2"
            >
              {link.label}
            </Link>
          ))}

          {/* Auth Buttons */}
          <div className="pt-4 border-t border-gray-200 space-y-3">
            {isAuthenticated ? (
              <button
                onClick={() => {
                  closeMenu();
                  onDashboardClick && onDashboardClick();
                }}
                className="w-full px-4 py-3 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors font-medium"
              >
                Dashboard
              </button>
            ) : (
              <>
                <button
                  onClick={() => {
                    closeMenu();
                    onLoginClick && onLoginClick();
                  }}
                  className="w-full px-4 py-3 rounded-lg border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors font-medium"
                >
                  Login
                </button>
                <button
                  onClick={() => {
                    closeMenu();
                    onRegisterClick && onRegisterClick();
                  }}
                  className="w-full px-4 py-3 rounded-lg bg-blue-600 text-white hover:bg-blue-700 transition-colors font-medium"
                >
                  Get Started
                </button>
              </>
            )}
          </div>
        </nav>
      </div>
    </>
  );
};

export default MobileMenu;
