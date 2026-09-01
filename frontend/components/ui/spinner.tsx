import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface SpinnerProps extends React.HTMLAttributes<HTMLDivElement> {
  size?: "sm" | "default" | "lg";
}

const sizeMap = {
  sm: "h-4 w-4",
  default: "h-5 w-5",
  lg: "h-8 w-8",
};

function Spinner({ className, size = "default", ...props }: SpinnerProps) {
  return (
    <div className={cn("inline-flex items-center justify-center", className)} {...props}>
      <Loader2 className={cn("animate-spin text-muted-foreground", sizeMap[size])} />
    </div>
  );
}

export { Spinner };
