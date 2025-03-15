import * as React from "react"
import { cn } from "../../lib/utils"

const Input = React.forwardRef(({ 
  className, 
  type = "text",
  variant = "default", // default, bordered, underlined, ghost
  size = "default", // sm, default, lg
  error,
  icon,
  iconPosition = "left",
  fullWidth = false,
  ...props 
}, ref) => {
  // Base styles for all inputs
  const baseStyles = "flex w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none disabled:cursor-not-allowed disabled:opacity-50"
  
  // Add variant styles
  const variantStyles = {
    default: "focus-visible:ring-2 focus-visible:ring-ring border-input",
    bordered: "border-2 focus-visible:border-primary focus-visible:ring-0",
    underlined: "border-0 border-b-2 rounded-none px-0 focus-visible:border-primary focus-visible:ring-0",
    ghost: "border-0 bg-transparent px-0 focus-visible:bg-muted/50 focus-visible:ring-0",
  }
  
  // Add size styles
  const sizeStyles = {
    sm: "h-8 px-2 py-1 text-xs",
    default: "h-10",
    lg: "h-12 px-4 py-3 text-base",
  }
  
  // Add width styles
  const widthStyles = fullWidth ? "w-full" : "w-auto"
  
  // Add error styles if there's an error
  const errorStyles = error ? "border-destructive focus-visible:ring-destructive" : ""
  
  // Create class names for the input
  const inputClasses = cn(
    baseStyles,
    variantStyles[variant],
    sizeStyles[size],
    widthStyles,
    errorStyles,
    // If there's an icon, add padding
    icon && iconPosition === "left" && "pl-10",
    icon && iconPosition === "right" && "pr-10",
    className
  )
  
  return (
    <div className={cn("relative", fullWidth && "w-full")}>
      {icon && iconPosition === "left" && (
        <div className="absolute left-3 top-0 flex h-full items-center pointer-events-none text-muted-foreground">
          {icon}
        </div>
      )}
      
      <input
        type={type}
        className={inputClasses}
        ref={ref}
        {...props}
      />
      
      {icon && iconPosition === "right" && (
        <div className="absolute right-3 top-0 flex h-full items-center pointer-events-none text-muted-foreground">
          {icon}
        </div>
      )}
      
      {error && typeof error === 'string' && (
        <p className="mt-1 text-xs text-destructive">{error}</p>
      )}
    </div>
  )
})
Input.displayName = "Input"

export { Input } 