import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority"
import { cn } from "../../lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-semibold ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-sm",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-sm",
        outline:
          "border border-input bg-background hover:bg-accent hover:text-accent-foreground",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/80 shadow-sm",
        ghost: "hover:bg-accent hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        // Custom variants
        soft: "bg-primary/10 text-primary hover:bg-primary/20 shadow-none",
        gradient: "relative bg-gradient-to-r from-primary to-secondary text-white hover:opacity-90 shadow-sm",
        glass: "bg-background/60 backdrop-blur-md border border-border/40 hover:bg-background/80",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3 text-xs",
        lg: "h-11 rounded-md px-8 text-base",
        icon: "h-10 w-10",
        // Custom sizes
        xs: "h-8 px-2.5 text-xs rounded-md",
        xl: "h-12 px-10 text-base rounded-md",
      },
      animation: {
        none: "",
        pulse: "animate-pulse",
        bounce: "hover:-translate-y-0.5 active:translate-y-0.5 transition-transform",
        scale: "hover:scale-105 active:scale-95 transition-transform",
        glow: "relative after:absolute after:inset-0 after:-z-10 after:rounded-md after:bg-primary/30 after:blur-md after:transition-all hover:after:bg-primary/40 hover:after:blur-lg after:opacity-0 hover:after:opacity-100",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
      animation: "none",
    },
  }
)

const Button = React.forwardRef(({ 
  className, 
  variant, 
  size, 
  animation,
  asChild = false,
  loading = false, 
  leftIcon,
  rightIcon,
  ...props 
}, ref) => {
  const Comp = asChild ? Slot : "button"
  
  // Handle the case where we have a Slot component (asChild=true)
  if (asChild) {
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, animation, className }))}
        ref={ref}
        disabled={loading || props.disabled}
        {...props}
      />
    )
  }
  
  // Regular button with optional loading spinner
  return (
    <button
      className={cn(buttonVariants({ variant, size, animation, className }))}
      ref={ref}
      disabled={loading || props.disabled}
      {...props}
    >
      {loading && (
        <svg className="mr-2 h-4 w-4 animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
      )}
      {leftIcon && <span className="mr-2">{leftIcon}</span>}
      {props.children}
      {rightIcon && <span className="ml-2">{rightIcon}</span>}
    </button>
  )
})
Button.displayName = "Button"

export { Button, buttonVariants } 