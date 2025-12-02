import { useState, useRef, useEffect } from 'react';
import './CheckboxDropdown.css';

interface CheckboxDropdownProps {
  label: string;
  options: Array<{ value: string; label: string }>;
  selectedValues: string[];
  onChange: (selected: string[]) => void;
  placeholder?: string;
}

export default function CheckboxDropdown({
  label,
  options,
  selectedValues,
  onChange,
  placeholder = 'Sélectionner...'
}: CheckboxDropdownProps) {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Fermer le dropdown si on clique en dehors
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleToggle = (value: string) => {
    const newSelected = selectedValues.includes(value)
      ? selectedValues.filter(v => v !== value)
      : [...selectedValues, value];
    onChange(newSelected);
  };

  const handleSelectAll = () => {
    if (selectedValues.length === options.length) {
      onChange([]);
    } else {
      onChange(options.map(opt => opt.value));
    }
  };

  const displayText = selectedValues.length === 0
    ? placeholder
    : selectedValues.length === 1
    ? options.find(opt => opt.value === selectedValues[0])?.label || selectedValues[0]
    : `${selectedValues.length} sélectionné(s)`;

  return (
    <div className="checkbox-dropdown" ref={dropdownRef}>
      <label className="checkbox-dropdown-label">{label}</label>
      <div className="checkbox-dropdown-toggle" onClick={() => setIsOpen(!isOpen)}>
        <span className={selectedValues.length === 0 ? 'placeholder' : ''}>
          {displayText}
        </span>
        <span className={`arrow ${isOpen ? 'open' : ''}`}>▼</span>
      </div>
      {isOpen && (
        <div className="checkbox-dropdown-menu">
          <div className="checkbox-dropdown-item checkbox-dropdown-header">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={selectedValues.length === options.length}
                onChange={handleSelectAll}
              />
              <span>Tout sélectionner</span>
            </label>
          </div>
          <div className="checkbox-dropdown-divider"></div>
          {options.map(option => (
            <div
              key={option.value}
              className="checkbox-dropdown-item"
              onClick={() => handleToggle(option.value)}
            >
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={selectedValues.includes(option.value)}
                  onChange={() => handleToggle(option.value)}
                  onClick={(e) => e.stopPropagation()}
                />
                <span>{option.label}</span>
              </label>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

