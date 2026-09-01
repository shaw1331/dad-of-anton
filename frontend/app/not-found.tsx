import Link from "next/link";
import { FileX2 } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center py-24">
      <Card className="w-full max-w-sm">
        <CardContent className="flex flex-col items-center gap-4 p-6">
          <FileX2 className="h-10 w-10 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">Page not found</p>
          <Link
            href="/"
            className="inline-flex items-center justify-center gap-2 rounded-md bg-secondary px-4 py-2 text-sm font-medium text-secondary-foreground shadow-sm transition-colors hover:bg-secondary/80"
          >
            Go home
          </Link>
        </CardContent>
      </Card>
    </div>
  );
}
