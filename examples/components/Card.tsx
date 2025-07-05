import React from 'react';

interface CardProps {
  /** Card title */
  title?: string;
  /** Card description */
  description?: string;
  /** Visual style variant */
  variant?: 'default' | 'outlined' | 'elevated';
  /** Padding size */
  padding?: 'none' | 'small' | 'medium' | 'large';
  /** Whether the card is interactive/clickable */
  interactive?: boolean;
  /** Click handler for interactive cards */
  onClick?: () => void;
  /** Card content */
  children?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  title,
  description,
  variant = 'default',
  padding = 'medium',
  interactive = false,
  onClick,
  children
}) => {
  const baseClasses = 'card rounded-lg transition-all duration-200';
  
  const variantClasses = {
    default: 'bg-white',
    outlined: 'bg-transparent border border-gray-200',
    elevated: 'bg-white shadow-lg hover:shadow-xl'
  };
  
  const paddingClasses = {
    none: '',
    small: 'p-3',
    medium: 'p-6',
    large: 'p-8'
  };
  
  const interactiveClasses = interactive 
    ? 'cursor-pointer hover:scale-[1.02] active:scale-[0.98]' 
    : '';
  
  return (
    <div
      className={`
        ${baseClasses}
        ${variantClasses[variant]}
        ${paddingClasses[padding]}
        ${interactiveClasses}
      `.trim().replace(/\s+/g, ' ')}
      onClick={interactive ? onClick : undefined}
    >
      {title && (
        <h3 className="text-xl font-semibold text-gray-900 mb-2">
          {title}
        </h3>
      )}
      {description && (
        <p className="text-gray-600 mb-4">
          {description}
        </p>
      )}
      {children}
    </div>
  );
};