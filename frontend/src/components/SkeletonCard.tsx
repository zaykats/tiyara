import { Skeleton } from "@/components/ui/skeleton";

export function SkeletonCard() {
  return (
    <div className="surface-panel p-4 space-y-3 animate-pulse">
      <div className="flex items-center gap-3">
        <Skeleton className="h-4 w-24 bg-muted" />
        <Skeleton className="h-5 w-16 bg-muted" />
      </div>
      <Skeleton className="h-3 w-full bg-muted" />
      <Skeleton className="h-3 w-2/3 bg-muted" />
    </div>
  );
}
