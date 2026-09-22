import React from 'react';
import { motion } from 'framer-motion';

export interface ShinyTextProps {
  text?: string;
  children?: React.ReactNode;
  className?: string;
  duration?: number;
  angle?: number;
  fontSize?: string;
  fontWeight?: string | number;
}

/**
 * ShinyText Component
 * Renders text with an ultra-smooth continuous gradient sweep from left to right.
 * Uses all gradient shades of purple from least (lightest #f3e8ff) to dark (#581c87) with NO white.
 * Speed: 10s duration for a slow, fluid, seamless sweep.
 */
export const ShinyText: React.FC<ShinyTextProps> = ({
  text,
  children,
  className = '',
  duration = 10,
  angle = 100,
  fontSize,
  fontWeight,
}) => {
  const content = text || children;

  // All shades of purple from dark (purple-900) to least (purple-100) and back to dark (zero white)
  const purpleGradient = `linear-gradient(${angle}deg, 
    #581c87 0%, 
    #6b21a8 10%, 
    #7e22ce 20%, 
    #9333ea 30%, 
    #a855f7 38%, 
    #c084fc 44%, 
    #d8b4fe 48%, 
    #f3e8ff 50%, 
    #d8b4fe 52%, 
    #c084fc 56%, 
    #a855f7 62%, 
    #9333ea 70%, 
    #7e22ce 80%, 
    #6b21a8 90%, 
    #581c87 100%
  )`;

  return (
    <motion.span
      className={`inline-block relative select-none ${className}`}
      style={{
        fontSize,
        fontWeight,
        backgroundImage: purpleGradient,
        backgroundSize: '250% 100%',
        WebkitBackgroundClip: 'text',
        backgroundClip: 'text',
        WebkitTextFillColor: 'transparent',
        color: 'transparent',
        display: 'inline-block',
      }}
      animate={{
        backgroundPosition: ['-150% 0%', '150% 0%'],
      }}
      transition={{
        duration,
        repeat: Infinity,
        ease: 'linear',
      }}
    >
      {content}
    </motion.span>
  );
};

export default ShinyText;
