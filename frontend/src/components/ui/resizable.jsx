import * as React from "react"
import { DragHandleDots2Icon } from "@radix-ui/react-icons"
import * as ResizablePrimitive from "react-resizable-panels"

import { cn } from "../../lib/utils"

const ResizablePanelGroup = React.forwardRef(
  ({ className, direction = "horizontal", onLayout, ...props }, ref) => (
    <ResizablePrimitive.PanelGroup
      ref={ref}
      direction={direction}
      className={cn(
        "flex h-full w-full data-[direction=horizontal]:flex-row data-[direction=vertical]:flex-col",
        className
      )}
      onLayout={onLayout}
      {...props}
    />
  )
)
ResizablePanelGroup.displayName = "ResizablePanelGroup"

const ResizablePanel = React.forwardRef(
  ({ className, defaultSize, minSize = 0.2, ...props }, ref) => (
    <ResizablePrimitive.Panel
      ref={ref}
      defaultSize={defaultSize}
      minSize={minSize}
      className={cn("relative h-full", className)}
      {...props}
    />
  )
)
ResizablePanel.displayName = "ResizablePanel"

const ResizableHandle = React.forwardRef(
  ({ withHandle, className, ...props }, ref) => (
    <ResizablePrimitive.PanelResizeHandle
      ref={ref}
      className={cn(
        "relative flex w-px items-center justify-center bg-border after:absolute after:inset-y-0 after:left-1/2 after:w-1 after:-translate-x-1/2 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring focus-visible:ring-offset-1 data-[direction=horizontal]:cursor-col-resize data-[direction=vertical]:h-px data-[direction=vertical]:w-full data-[direction=vertical]:cursor-row-resize",
        className
      )}
      {...props}
    >
      {withHandle && (
        <div className="z-10 flex h-4 w-4 items-center justify-center rounded-sm border bg-border">
          <DragHandleDots2Icon className="h-2.5 w-2.5" />
        </div>
      )}
    </ResizablePrimitive.PanelResizeHandle>
  )
)
ResizableHandle.displayName = "ResizableHandle"

export { ResizablePanelGroup, ResizablePanel, ResizableHandle } 