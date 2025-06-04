import React from 'react';

const Button = React.forwardRef(({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return (
        <Comp
            className={cn(buttonVariants({ variant, size, className }))}
            ref={ref}
            {...props} />
    );
});
Button.displayName = "Button"

// Helper function (cn) and buttonVariants would typically be defined in a utils file
// For simplicity, we'll include a basic cn and placeholder for buttonVariants here.

// cn function (simplified from shadcn/ui)
function cn(...inputs) {
    return inputs.filter(Boolean).join(' ');
}

// Placeholder for buttonVariants - you'll need to define actual styles
const buttonVariants = ({ variant, size, className }) => {
    // Base styles
    let styles = "inline-flex items-center justify-center rounded-md text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50";

    // Variant styles
    if (variant === "destructive") {
        styles += " bg-destructive text-destructive-foreground hover:bg-destructive/90";
    } else if (variant === "outline") {
        styles += " border border-input bg-background hover:bg-accent hover:text-accent-foreground";
    } else if (variant === "secondary") {
        styles += " bg-secondary text-secondary-foreground hover:bg-secondary/80";
    } else if (variant === "ghost") {
        styles += " hover:bg-accent hover:text-accent-foreground";
    } else if (variant === "link") {
        styles += " text-primary underline-offset-4 hover:underline";
    } else { // Default variant
        styles += " bg-primary text-primary-foreground hover:bg-primary/90";
    }

    // Size styles
    if (size === "sm") {
        styles += " h-9 px-3";
    } else if (size === "lg") {
        styles += " h-11 px-8";
    } else if (size === "icon") {
        styles += " h-10 w-10";
    } else { // Default size
        styles += " h-10 px-4 py-2";
    }

    return cn(styles, className);
};

// You would typically import Slot from '@radix-ui/react-slot' if you use asChild
// For now, we'll define a placeholder Slot if asChild is true.
const Slot = React.forwardRef((props, ref) => {
    return React.cloneElement(props.children, { ...props, ref });
});
Slot.displayName = "Slot";


export { Button, buttonVariants };