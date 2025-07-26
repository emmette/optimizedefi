import { useEffect, useState } from 'react';
import { useAccount } from 'wagmi';
import { useAuthStore } from '@/store/authStore';

interface AdminStatus {
  isAdmin: boolean;
  isLoading: boolean;
  error: string | null;
}

/**
 * Hook to check if the current user has admin privileges
 */
export function useAdminAuth(): AdminStatus {
  const { address } = useAccount();
  const { isAuthenticated, user } = useAuthStore();
  const [adminStatus, setAdminStatus] = useState<AdminStatus>({
    isAdmin: false,
    isLoading: true,
    error: null,
  });

  useEffect(() => {
    const checkAdminStatus = async () => {
      // Reset state
      setAdminStatus({
        isAdmin: false,
        isLoading: true,
        error: null,
      });

      // Check if user is authenticated
      if (!isAuthenticated || !address || !user) {
        setAdminStatus({
          isAdmin: false,
          isLoading: false,
          error: null,
        });
        return;
      }

      try {
        // Call admin status endpoint
        const token = localStorage.getItem('auth_token');
        if (!token) {
          setAdminStatus({
            isAdmin: false,
            isLoading: false,
            error: 'No auth token found',
          });
          return;
        }

        const response = await fetch('/api/auth/admin/status', {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });

        if (!response.ok) {
          if (response.status === 403) {
            // Not an admin, but that's ok
            setAdminStatus({
              isAdmin: false,
              isLoading: false,
              error: null,
            });
            return;
          }
          throw new Error('Failed to check admin status');
        }

        const data = await response.json();
        setAdminStatus({
          isAdmin: data.is_admin === true,
          isLoading: false,
          error: null,
        });
      } catch (error) {
        console.error('Admin auth check failed:', error);
        setAdminStatus({
          isAdmin: false,
          isLoading: false,
          error: error instanceof Error ? error.message : 'Unknown error',
        });
      }
    };

    checkAdminStatus();
  }, [address, isAuthenticated, user]);

  return adminStatus;
}

/**
 * Higher-order component to protect admin routes
 */
export function withAdminAuth<P extends object>(
  Component: React.ComponentType<P>
): React.ComponentType<P> {
  return function AdminProtectedComponent(props: P) {
    const { isAdmin, isLoading } = useAdminAuth();
    const router = require('next/router').useRouter();

    useEffect(() => {
      if (!isLoading && !isAdmin) {
        // Redirect non-admins to home
        router.push('/');
      }
    }, [isAdmin, isLoading, router]);

    if (isLoading) {
      return (
        <div className="flex items-center justify-center min-h-screen">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 dark:border-white"></div>
        </div>
      );
    }

    if (!isAdmin) {
      return null; // Will redirect
    }

    return <Component {...props} />;
  };
}

/**
 * Component to conditionally render content based on admin status
 */
export function AdminOnly({ 
  children,
  fallback = null 
}: { 
  children: React.ReactNode;
  fallback?: React.ReactNode;
}) {
  const { isAdmin, isLoading } = useAdminAuth();

  if (isLoading) {
    return null;
  }

  if (!isAdmin) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}