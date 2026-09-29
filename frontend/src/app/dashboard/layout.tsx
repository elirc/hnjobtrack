import { Suspense } from "react";

function LoadingFallback() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-orange-500" />
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <Suspense fallback={<LoadingFallback />}>{children}</Suspense>;
}
