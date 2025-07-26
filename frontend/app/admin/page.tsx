'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { withAdminAuth } from '@/hooks/useAdminAuth';
import { MetricsDashboard } from '@/components/admin/MetricsDashboard';
import { useAuthStore } from '@/store/authStore';

function AdminPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuthStore();

  useEffect(() => {
    // Redirect if not authenticated
    if (!isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  return (
    <div className="container mx-auto py-8 px-4">
      <MetricsDashboard />
    </div>
  );
}

// Wrap with admin auth HOC
export default withAdminAuth(AdminPage);