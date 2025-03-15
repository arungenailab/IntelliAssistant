import * as React from "react"
import { cn } from "../../lib/utils"

// Enhanced Card Component with modern styles
const Card = React.forwardRef(({ 
  className, 
  variant = "default", // default, glass, gradient, outline, elevated
  hoverEffect = false,
  interactive = false,
  ...props 
}, ref) => {
  const baseStyles = "rounded-lg border bg-card text-card-foreground"
  
  const variantStyles = {
    default: "shadow-sm",
    glass: "bg-background/70 backdrop-blur-lg border-muted/20",
    gradient: "border-0 bg-gradient-to-br from-muted/50 via-card to-muted/50",
    outline: "bg-transparent shadow-none",
    elevated: "shadow-md",
  }
  
  const hoverStyles = interactive 
    ? "transition-all duration-200 hover:shadow-md" 
    : hoverEffect 
      ? "transition-all duration-200 hover:-translate-y-1 hover:shadow-md" 
      : ""
  
  return (
    <div
      ref={ref}
      className={cn(
        baseStyles,
        variantStyles[variant],
        hoverStyles,
        className
      )}
      {...props}
    />
  )
})
Card.displayName = "Card"

// Card Header with modern styling
const CardHeader = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex flex-col space-y-1.5 p-6", className)}
    {...props}
  />
))
CardHeader.displayName = "CardHeader"

// Card Title with improved typography and fixed accessibility
const CardTitle = React.forwardRef(({ className, as: Component = "h3", children, ...props }, ref) => {
  // Ensure the component has content for accessibility
  if (!children) {
    console.warn("CardTitle should have content for accessibility");
  }
  
  return (
    <Component
      ref={ref}
      className={cn(
        "font-semibold leading-none tracking-tight text-lg",
        className
      )}
      {...props}
    >
      {children}
    </Component>
  )
})
CardTitle.displayName = "CardTitle"

// Card Description with subtle color
const CardDescription = React.forwardRef(({ className, ...props }, ref) => (
  <p
    ref={ref}
    className={cn("text-sm text-muted-foreground", className)}
    {...props}
  />
))
CardDescription.displayName = "CardDescription"

// Card Content area
const CardContent = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

// Card Footer with border
const CardFooter = React.forwardRef(({ className, ...props }, ref) => (
  <div
    ref={ref}
    className={cn("flex items-center p-6 pt-0", className)}
    {...props}
  />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent } 