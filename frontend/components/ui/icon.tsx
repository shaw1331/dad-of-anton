import { type LucideIcon, type LucideProps } from "lucide-react";
import { cn } from "@/lib/utils";

const sizeMap = {
  sm: "h-4 w-4",
  default: "h-5 w-5",
  lg: "h-6 w-6",
};

interface IconProps extends Omit<LucideProps, "size"> {
  icon: LucideIcon;
  size?: "sm" | "default" | "lg";
}

function Icon({ icon: IconComponent, size = "default", className, ...props }: IconProps) {
  return (
    <IconComponent
      className={cn(sizeMap[size], className)}
      strokeWidth={1.5}
      {...props}
    />
  );
}

export { Icon };
export type { IconProps };
